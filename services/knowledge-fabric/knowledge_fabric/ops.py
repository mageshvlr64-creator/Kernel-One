"""Ops layer — the fifteen feature ops of docs/features/13_knowledge_fabric/.

Each op is validated against the canonical contracts, authorized by the permission
matrix (Document:read for overview/quality/failures; Document:execute for the rest),
executed against the chunk index inside one logical operation, and audited with
exactly one `knowledge_fabric.<op>` invocation event (success or failure) — plus,
for the op that completes indexing, the canonical state-machine transition event
`document.indexed` (INDEXING -> READY, owner knowledge_fabric).

Errors come only from the canonical registry (reference/01): INVALID_REQUEST,
FILE_NOT_FOUND, FILE_CLASSIFICATION_DENIED, TOOL_NOT_ALLOWED, POLICY_DENIED,
RAG_INDEX_UNAVAILABLE, RESOURCE_CONFLICT, DEPENDENCY_UNAVAILABLE, INTERNAL_ERROR.
"""
from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import statemachine as sm
from .audit import AuditSink, build_audit_event
from .config import Settings
from .domain import (ContextBundle, DocumentChunk, DocumentRef, SearchHit,
                     now_iso, validate_chunk_fields)
from .errors import RegistryError
from .policy import Actor, enforce
from .retry import classify, run_with_retry
from .storage import ChunkIndex, DocumentSource, cosine, embed_text


@dataclass
class OpResult:
    op: str
    data: Dict[str, Any]
    resource_id: Optional[str]
    audit_event_id: str
    correlation_id: str
    state: Optional[str] = None


@dataclass
class Context:
    actor: Actor
    source_ip: Optional[str] = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


WS = re.compile(r"\s+")
TOKEN = re.compile(r"[A-Za-z0-9']+")


def _tokens(text: str) -> List[str]:
    return [t.lower() for t in TOKEN.findall(text)]


# --------------------------------------------------------------------------- handlers

def _load_document(service: "KnowledgeFabricService", payload: Dict[str, Any]) -> DocumentRef:
    document_id = payload.get("document_id")
    if not isinstance(document_id, str) or not document_id.strip():
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_id",
                                      "issue": "required uuid string"}],
                            operator_detail="document_id required")
    ref = service.source.get(document_id)
    if ref is None:
        raise RegistryError("FILE_NOT_FOUND",
                            operator_detail=f"document {document_id} not found")
    return ref


def _require_indexing(ref: DocumentRef) -> None:
    if ref.state != "INDEXING":
        raise RegistryError(
            "INVALID_REQUEST",
            details=[{"field": "document_id",
                      "issue": f"document state is {ref.state}, not INDEXING"}],
            operator_detail=f"document {ref.document_id} is {ref.state}, not INDEXING")


def _empty_text_failure(service: "KnowledgeFabricService", ref: DocumentRef) -> None:
    """Content-level failure: move the document INDEXING -> FAILED (canonical,
    owner knowledge_fabric) with the document.failed transition event."""
    event = build_audit_event(
        event_type="document.failed", actor_id="system", action="execute",
        resource_type="Document", result="error", resource_id=ref.document_id,
        classification=ref.classification, error_code="INVALID_REQUEST",
        reason="document source text is empty after normalization",
        correlation_id=None, source_interface="internal")
    sm.transition("INDEXING", "FAILED", owner="knowledge_fabric")
    ref.state = "FAILED"
    service.audit_sink.emit(event)


def handle_document_store(service: "KnowledgeFabricService", ctx: Context,
                          payload: Dict[str, Any]) -> Dict[str, Any]:
    ref = _load_document(service, payload)
    _require_indexing(ref)
    rec = service.store.get_record(ref.document_id) or {}
    rec.setdefault("name", f"document-{ref.document_id[:8]}")
    service.store.index_records[ref.document_id] = rec
    service.store.record_ready(ref.document_id, rec.get("ready", False))
    return {"document_id": ref.document_id, "state": ref.state,
            "index_record": {"chunks": rec.get("chunks", 0),
                             "embedded": rec.get("embedded", 0),
                             "ready": rec.get("ready", False)}}


def handle_document_normalization(service: "KnowledgeFabricService", ctx: Context,
                                  payload: Dict[str, Any]) -> Dict[str, Any]:
    ref = _load_document(service, payload)
    _require_indexing(ref)
    raw = ref.source_text or ""
    # Normalization: NFKC, drop control chars (except \n), collapse whitespace.
    normalized = unicodedata.normalize("NFKC", raw)
    normalized = "".join(c for c in normalized if c == "\n" or not unicodedata.category(c).startswith("C"))
    normalized = WS.sub(" ", normalized).strip()
    reduction = len(raw) - len(normalized)
    if not normalized:
        _empty_text_failure(service, ref)
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_id",
                                      "issue": "no indexable content"}],
                            operator_detail="source text empty after normalization")
    ref.source_text = normalized
    rec = service.store.get_record(ref.document_id) or {}
    rec["normalized_chars"] = len(normalized)
    service.store.index_records[ref.document_id] = rec
    return {"document_id": ref.document_id, "normalized_chars": len(normalized),
            "reduction_chars": reduction}


def handle_chunking(service: "KnowledgeFabricService", ctx: Context,
                    payload: Dict[str, Any]) -> Dict[str, Any]:
    ref = _load_document(service, payload)
    _require_indexing(ref)
    text = ref.source_text or ""
    if not text.strip():
        _empty_text_failure(service, ref)
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_id",
                                      "issue": "no content to chunk"}],
                            operator_detail="source text empty")
    max_chars = service.settings.chunk_max_chars
    min_chars = service.settings.chunk_min_chars
    # Paragraph-first splitting, then window packing with ~10% overlap.
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    units: List[str] = []
    for para in paragraphs:
        if len(para) <= max_chars:
            units.append(para)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", para)
        cur = ""
        for s in sentences:
            if cur and len(cur) + 1 + len(s) > max_chars:
                units.append(cur)
                cur = s
            else:
                cur = f"{cur} {s}".strip()
        if cur:
            units.append(cur)
    chunks: List[str] = []
    cur = ""
    for unit in units:
        if cur and len(cur) + 1 + len(unit) > max_chars:
            chunks.append(cur)
            cur = ""
        cur = f"{cur} {unit}".strip() if cur else unit
    if cur:
        chunks.append(cur)
    # Merge a too-short tail into its predecessor so every chunk >= min (last resort).
    if len(chunks) > 1 and len(chunks[-1]) < min_chars:
        last = chunks.pop()
        chunks[-1] = f"{chunks[-1]} {last}".strip()
    # Oversized single unit (no sentence boundaries): hard-split with overlap.
    final: List[str] = []
    for piece in chunks:
        if len(piece) <= max_chars:
            final.append(piece)
            continue
        step = int(max_chars * 0.9)
        i = 0
        while i < len(piece):
            final.append(piece[i:i + max_chars])
            i += step
    doc_chunks = [DocumentChunk(document_id=ref.document_id, chunk_index=i, text=t,
                                page_number=None)
                  for i, t in enumerate(final)]
    # One store mutation for the whole batch (single-transaction semantics §5).
    service.index.replace_document_chunks(ref.document_id, doc_chunks)
    service.store.record_chunks(ref.document_id, len(doc_chunks))
    return {"document_id": ref.document_id, "chunk_count": len(doc_chunks)}


def handle_embeddings(service: "KnowledgeFabricService", ctx: Context,
                      payload: Dict[str, Any]) -> Dict[str, Any]:
    ref = _load_document(service, payload)
    _require_indexing(ref)
    chunks = service.index.chunks_for_document(ref.document_id)
    if not chunks:
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_id",
                                      "issue": "no chunks indexed yet"}],
                            operator_detail="run chunking before embeddings")
    dim = service.settings.embedding_dim
    for c in chunks:
        vec = service.embedder(c.text)
        if not isinstance(vec, list) or len(vec) != dim:
            raise RegistryError("INTERNAL_ERROR",
                                operator_detail=f"embedding dim mismatch: got "
                                f"{len(vec) if isinstance(vec, list) else type(vec).__name__}, want {dim}")
        c.embedding = [float(x) for x in vec]
    service.store.record_embedded(ref.document_id, len(chunks))
    return {"document_id": ref.document_id, "embedded_count": len(chunks)}


def handle_keyword_index(service: "KnowledgeFabricService", ctx: Context,
                         payload: Dict[str, Any]) -> Dict[str, Any]:
    ref = _load_document(service, payload)
    _require_indexing(ref)
    chunks = service.index.chunks_for_document(ref.document_id)
    if not chunks:
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_id",
                                      "issue": "no chunks indexed yet"}],
                            operator_detail="run chunking first")
    terms = set()
    for c in chunks:
        terms.update(_tokens(c.text))
    rec = service.store.get_record(ref.document_id) or {}
    rec["keyword_terms"] = len(terms)
    service.store.index_records[ref.document_id] = rec
    return {"document_id": ref.document_id, "terms_indexed": len(terms)}


def _try_transition_ready(service: "KnowledgeFabricService", ref: DocumentRef) -> None:
    """After indexing steps complete, move INDEXING -> READY when the document is
    fully indexed (canonical transition, owner knowledge_fabric, document.indexed)."""
    rec = service.store.get_record(ref.document_id) or {}
    complete = (rec.get("chunks", 0) >= service.settings.min_chunks_for_ready
                and rec.get("embedded", 0) >= rec.get("chunks", 0) > 0)
    if not complete:
        return
    event = build_audit_event(
        event_type="document.indexed", actor_id="system", action="execute",
        resource_type="Document", result="success", resource_id=ref.document_id,
        classification=ref.classification, source_interface="internal")
    sm.transition("INDEXING", "READY", owner="knowledge_fabric")
    ref.state = "READY"
    service.store.record_ready(ref.document_id, True)
    service.audit_sink.emit(event)


def handle_vector_index(service: "KnowledgeFabricService", ctx: Context,
                        payload: Dict[str, Any]) -> Dict[str, Any]:
    ref = _load_document(service, payload)
    _require_indexing(ref)
    chunks = service.index.chunks_for_document(ref.document_id)
    if not chunks:
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_id",
                                      "issue": "no chunks indexed yet"}],
                            operator_detail="run chunking first")
    missing = [c.chunk_index for c in chunks if not c.embedding]
    if missing:
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_id",
                                      "issue": f"{len(missing)} chunk(s) have no embedding"}],
                            operator_detail="run embeddings before vector index")
    # Reaching here means the index store accepted every vector (stub: in-memory;
    # real: pgvector HNSW per integrations/06). Failure to write raises
    # RAG_INDEX_UNAVAILABLE from the store seam.
    rec = service.store.get_record(ref.document_id) or {}
    rec["vectors_indexed"] = len(chunks)
    service.store.index_records[ref.document_id] = rec
    _try_transition_ready(service, ref)
    return {"document_id": ref.document_id, "vectors_indexed": len(chunks),
            "document_state": ref.state}


def handle_metadata_index(service: "KnowledgeFabricService", ctx: Context,
                          payload: Dict[str, Any]) -> Dict[str, Any]:
    ref = _load_document(service, payload)
    # Idempotent bookkeeping: legal both mid-indexing and after READY (so calling
    # metadata_index after vector_index triggered READY does not 400).
    if ref.state not in ("INDEXING", "READY"):
        raise RegistryError(
            "INVALID_REQUEST",
            details=[{"field": "document_id",
                      "issue": f"document state is {ref.state}"}],
            operator_detail=f"document {ref.document_id} is {ref.state}")
    chunks = service.index.chunks_for_document(ref.document_id)
    if not chunks:
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_id",
                                      "issue": "no chunks indexed yet"}],
                            operator_detail="run chunking first")
    entries = sum(1 for c in chunks if c.page_number is not None or c.bbox)
    rec = service.store.get_record(ref.document_id) or {}
    rec["metadata_entries"] = entries
    service.store.index_records[ref.document_id] = rec
    return {"document_id": ref.document_id, "metadata_entries": entries}


def _doc_meta(service: "KnowledgeFabricService", document_id: str) -> dict:
    """Authoritative metadata for a document: classification/workspace/name come from
    the DocumentRef (source of truth), with index-record overlays on top."""
    meta = dict(service.store.index_records.get(document_id) or {})
    ref = service.source.get(document_id)
    if ref is not None:
        meta.setdefault("classification", ref.classification)
        meta.setdefault("workspace_id", ref.workspace_id)
        meta.setdefault("name", f"document-{document_id[:8]}")
    return meta


def _visible_chunks(service: "KnowledgeFabricService", actor: Actor,
                    workspace_id: str) -> List[Tuple[DocumentChunk, dict]]:
    """Chunks visible to the actor: classification <= clearance, workspace match
    (REQ-FUNC-004 — never queried without the filter, domain/07 Notes)."""
    out: List[Tuple[DocumentChunk, dict]] = []
    for chunk in service.index.all_chunks():
        meta = _doc_meta(service, chunk.document_id)
        classification = meta.get("classification", "INTERNAL")
        doc_workspace = meta.get("workspace_id", "")
        from .policy import CLEARANCE_ORDER
        if CLEARANCE_ORDER[actor.clearance] < CLEARANCE_ORDER[classification]:
            continue
        if workspace_id and doc_workspace and doc_workspace != workspace_id:
            if actor.role not in ("Administrator", "Auditor"):
                continue
        out.append((chunk, meta))
    return out


def _keyword_score(query_tokens: List[str], text: str) -> float:
    if not query_tokens:
        return 0.0
    chunk_tokens = set(_tokens(text))
    hits = sum(1 for t in query_tokens if t in chunk_tokens)
    return hits / len(query_tokens)


def handle_hybrid_search(service: "KnowledgeFabricService", ctx: Context,
                         payload: Dict[str, Any]) -> Dict[str, Any]:
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "query", "issue": "required non-empty string"}],
                            operator_detail="query required")
    top_k = payload.get("top_k") or service.settings.retrieval_top_k
    if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 50:
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "top_k", "issue": "integer 1..50"}],
                            operator_detail="top_k out of range")
    workspace_id = payload.get("workspace_id") or ctx.actor.workspace_id
    q_tokens = _tokens(query)
    q_vec = service.embedder(query)
    scored: List[SearchHit] = []
    for chunk, meta in _visible_chunks(service, ctx.actor, workspace_id):
        kw = _keyword_score(q_tokens, chunk.text)
        vec = cosine(q_vec, chunk.embedding) if chunk.embedding else 0.0
        score = 0.5 * kw + 0.5 * vec
        if score <= 0.0:
            continue
        scored.append(SearchHit(
            chunk_id=chunk.id, document_id=chunk.document_id,
            document_name=meta.get("name", f"document-{chunk.document_id[:8]}"),
            chunk_index=chunk.chunk_index, page_number=chunk.page_number,
            text=chunk.text, score=round(score, 6),
            score_breakdown={"keyword": round(kw, 6), "vector": round(vec, 6)}))
    scored.sort(key=lambda h: (-h.score, h.document_id, h.chunk_index))
    candidates = scored[:service.settings.retrieval_candidates]
    return {"query": query, "hits": [h.__dict__ for h in candidates[:top_k]],
            "total_candidates": len(scored)}


def handle_reranking(service: "KnowledgeFabricService", ctx: Context,
                     payload: Dict[str, Any]) -> Dict[str, Any]:
    query = payload.get("query")
    candidates = payload.get("candidates")
    if not isinstance(query, str) or not query.strip() or not isinstance(candidates, list):
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "query/candidates",
                                      "issue": "query string and candidates array required"}],
                            operator_detail="reranking needs query and candidates")
    q_tokens = _tokens(query)
    reranked: List[dict] = []
    for item in candidates:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            raise RegistryError("INVALID_REQUEST",
                                details=[{"field": "candidates",
                                          "issue": "each candidate needs text"}],
                                operator_detail="malformed candidate")
        text = item["text"]
        token_set = set(_tokens(text))
        coverage = (sum(1 for t in q_tokens if t in token_set) / len(q_tokens)
                    if q_tokens else 0.0)
        base = float(item.get("score", 0.0) or 0.0)
        new_score = round(0.5 * base + 0.5 * coverage, 6)
        out = dict(item)
        out["score"] = new_score
        out.setdefault("score_breakdown", {})
        out["score_breakdown"]["rerank_coverage"] = round(coverage, 6)
        reranked.append(out)
    reranked.sort(key=lambda h: -h["score"])
    return {"query": query, "hits": reranked, "count": len(reranked)}


def handle_document_hierarchy(service: "KnowledgeFabricService", ctx: Context,
                              payload: Dict[str, Any]) -> Dict[str, Any]:
    ref = _load_document(service, payload)
    chunks = service.index.chunks_for_document(ref.document_id)
    if not chunks:
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_id",
                                      "issue": "no chunks indexed yet"}],
                            operator_detail="run chunking first")
    sections: Dict[Optional[int], dict] = {}
    for c in chunks:
        key = c.page_number
        sec = sections.setdefault(key, {"page_number": key, "chunk_indices": [],
                                        "first_text": c.text[:120]})
        sec["chunk_indices"].append(c.chunk_index)
    ordered = [sections[k] for k in sorted(sections.keys(),
                                           key=lambda k: (k is None, k))]
    return {"document_id": ref.document_id, "chunk_count": len(chunks),
            "sections": ordered}


def handle_permission_filtering(service: "KnowledgeFabricService", ctx: Context,
                                payload: Dict[str, Any]) -> Dict[str, Any]:
    document_ids = payload.get("document_ids")
    if not isinstance(document_ids, list) or not all(isinstance(d, str) for d in document_ids):
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "document_ids",
                                      "issue": "array of document ids required"}],
                            operator_detail="document_ids required")
    from .policy import CLEARANCE_ORDER
    visible, hidden = [], []
    for did in document_ids:
        meta = _doc_meta(service, did)
        classification = meta.get("classification", "INTERNAL")
        doc_workspace = meta.get("workspace_id", "")
        if CLEARANCE_ORDER[ctx.actor.clearance] < CLEARANCE_ORDER[classification]:
            hidden.append({"document_id": did,
                           "reason": f"classification {classification} above clearance"})
            continue
        if doc_workspace and doc_workspace != ctx.actor.workspace_id and \
                ctx.actor.role not in ("Administrator", "Auditor"):
            hidden.append({"document_id": did, "reason": "outside caller workspace"})
            continue
        visible.append({"document_id": did})
    return {"visible": visible, "hidden": hidden}


def handle_context_assembly(service: "KnowledgeFabricService", ctx: Context,
                            payload: Dict[str, Any]) -> Dict[str, Any]:
    search_payload = {"query": payload.get("query"),
                      "top_k": payload.get("top_k"),
                      "workspace_id": payload.get("workspace_id")}
    result = handle_hybrid_search(service, ctx, search_payload)
    max_tokens = payload.get("max_tokens") or 2000
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens < 64:
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "max_tokens", "issue": "integer >= 64"}],
                            operator_detail="max_tokens too small")
    hits = [SearchHit(**h) for h in result["hits"]]
    chars_per_token = 4
    budget = max_tokens * chars_per_token
    items: List[SearchHit] = []
    used = 0
    truncated = False
    for h in hits:
        cost = len(h.text)
        if used + cost > budget:
            truncated = True
            break
        items.append(h)
        used += cost
    bundle = ContextBundle(query=result["query"], items=items,
                           total_tokens_approx=used // chars_per_token,
                           truncated=truncated,
                           document_ids=sorted({h.document_id for h in items}))
    return {"query": bundle.query, "items": [h.__dict__ for h in bundle.items],
            "total_tokens_approx": bundle.total_tokens_approx,
            "truncated": bundle.truncated, "document_ids": bundle.document_ids}


def handle_knowledge_overview(service: "KnowledgeFabricService", ctx: Context,
                              payload: Dict[str, Any]) -> Dict[str, Any]:
    document_id = payload.get("document_id")
    if document_id:
        rec = service.store.get_record(document_id)
        if rec is None:
            raise RegistryError("FILE_NOT_FOUND",
                                operator_detail=f"no index record for {document_id}")
        return {"document_id": document_id, "index_record": rec}
    docs = list(service.store.index_records.items())
    total_chunks = sum(r.get("chunks", 0) for _, r in docs)
    total_embedded = sum(r.get("embedded", 0) for _, r in docs)
    ready = sum(1 for _, r in docs if r.get("ready"))
    return {"documents_indexed": len(docs), "total_chunks": total_chunks,
            "total_embedded": total_embedded, "documents_ready": ready,
            "index_size_chunks": service.index.count_total()}


def handle_retrieval_quality(service: "KnowledgeFabricService", ctx: Context,
                             payload: Dict[str, Any]) -> Dict[str, Any]:
    result = handle_hybrid_search(service, ctx, {"query": payload.get("query"),
                                                 "top_k": payload.get("top_k")})
    scores = [h["score"] for h in result["hits"]]
    return {"query": result["query"], "hit_count": len(scores),
            "total_candidates": result["total_candidates"],
            "score_max": max(scores) if scores else 0.0,
            "score_min": min(scores) if scores else 0.0,
            "score_mean": (sum(scores) / len(scores)) if scores else 0.0,
            "empty_result": not scores}


def handle_retrieval_failures(service: "KnowledgeFabricService", ctx: Context,
                              payload: Dict[str, Any]) -> Dict[str, Any]:
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "query", "issue": "required"}],
                            operator_detail="query required")
    diagnosis: List[str] = []
    total = service.index.count_total()
    if total == 0:
        diagnosis.append("no_chunks_indexed")
    else:
        visible = _visible_chunks(service, ctx.actor, "")
        if not visible:
            diagnosis.append("classification_filtered_all")
        else:
            q_tokens = _tokens(query)
            if not any(_keyword_score(q_tokens, c.text) > 0 for c, _ in visible):
                diagnosis.append("no_keyword_overlap")
            if not any(c.embedding for c, _ in visible):
                diagnosis.append("no_embeddings")
    if not diagnosis:
        result = handle_hybrid_search(service, ctx, {"query": query})
        if not result["hits"]:
            diagnosis.append("no_score_above_threshold")
    return {"query": query, "diagnosis": diagnosis or ["none"],
            "index_size_chunks": total}


# --------------------------------------------------------------------------- registry

OPS: Dict[str, Dict[str, Any]] = {
    # slug: handler, canonical audit action, retry class implicit via classify()
    "document_store": {"handler": handle_document_store, "action": "execute"},
    "document_normalization": {"handler": handle_document_normalization, "action": "execute"},
    "chunking": {"handler": handle_chunking, "action": "execute"},
    "embeddings": {"handler": handle_embeddings, "action": "execute"},
    "keyword_index": {"handler": handle_keyword_index, "action": "execute"},
    "vector_index": {"handler": handle_vector_index, "action": "execute"},
    "metadata_index": {"handler": handle_metadata_index, "action": "execute"},
    "hybrid_search": {"handler": handle_hybrid_search, "action": "read"},
    "reranking": {"handler": handle_reranking, "action": "execute"},
    "document_hierarchy": {"handler": handle_document_hierarchy, "action": "execute"},
    "permission_filtering": {"handler": handle_permission_filtering, "action": "execute"},
    "context_assembly": {"handler": handle_context_assembly, "action": "execute"},
    "knowledge_overview": {"handler": handle_knowledge_overview, "action": "read"},
    "retrieval_quality": {"handler": handle_retrieval_quality, "action": "read"},
    "retrieval_failures": {"handler": handle_retrieval_failures, "action": "read"},
}


# --------------------------------------------------------------------------- service

class KnowledgeFabricService:
    """Single implementation behind both the in-process entry points and the HTTP
    wrapper (feature docs §12 — exactly one implementation, not two)."""

    def __init__(self, *, source: DocumentSource, index: ChunkIndex,
                 audit_sink: AuditSink, settings: Settings,
                 embedder: Optional[Callable[[str], List[float]]] = None) -> None:
        self.source = source
        self.index = index
        self.audit_sink = audit_sink
        self.settings = settings
        self.embedder = embedder or (lambda text: embed_text(text, settings.embedding_dim))
        from .store import KnowledgeStore
        self.store = KnowledgeStore(index)
        self.invocations: Dict[str, dict] = {}   # audit_event_id -> invocation summary

    # ---- central dispatcher -------------------------------------------------------
    def invoke(self, op: str, actor: Actor, payload: Optional[Dict[str, Any]],
               *, source_ip: Optional[str] = None) -> OpResult:
        ctx = Context(actor=actor, source_ip=source_ip)
        spec = OPS.get(op)
        if spec is None:
            raise RegistryError("INVALID_REQUEST",
                                details=[{"field": "op", "issue": f"unknown op {op!r}"}],
                                operator_detail=f"unknown op {op!r}")
        payload = payload or {}
        if not isinstance(payload, dict):
            raise RegistryError("INVALID_REQUEST",
                                details=[{"field": "payload", "issue": "must be an object"}],
                                operator_detail="payload must be a JSON object")

        # Schema gate before any business logic (schemas/08 validation behavior).
        # Policy gate, handler, and audit all run inside the guarded block so that
        # EVERY invocation — success, denial, or error — emits exactly one
        # knowledge_fabric.<op> event (feature docs §22).
        try:
            if "chunks" in payload or ("text" in payload and "query" not in payload):
                errors: List[Dict[str, str]] = []
                validate_chunk_fields(payload, dim=self.settings.embedding_dim,
                                      errors=errors)
                if errors:
                    raise RegistryError("INVALID_REQUEST", details=errors,
                                        operator_detail="chunk payload failed schema")

            # Document-scoped ops check against the resource; corpus ops check the
            # role/action row against a PUBLIC baseline — classification filtering for
            # retrieval happens per chunk (domain/07 Notes: "never queried without that
            # filter"), not as a corpus-level denial.
            resource_kwargs: Dict[str, Any] = {}
            if "document_id" in payload:
                ref = self.source.get(payload.get("document_id"))
                if ref is not None:
                    resource_kwargs = {"resource_classification": ref.classification,
                                       "resource_workspace_id": ref.workspace_id,
                                       "resource_owner_id": ref.owner_id}
            else:
                resource_kwargs = {"resource_classification": "PUBLIC"}
            enforce("Document", spec["action"], actor, **resource_kwargs)

            handler: Callable = spec["handler"]

            def _run() -> Dict[str, Any]:
                return handler(self, ctx, payload)

            data = run_with_retry(_run, op)
        except RegistryError as err:
            ref = self.source.get(payload.get("document_id")) if payload else None
            event = build_audit_event(
                event_type=f"knowledge_fabric.{op}", actor_id=actor.actor_id,
                action=spec["action"], resource_type="Document", result="error",
                resource_id=payload.get("document_id"),
                classification=ref.classification if ref else None,
                error_code=err.code, reason=err.operator_detail,
                correlation_id=ctx.correlation_id, source_ip=source_ip)
            self.audit_sink.emit(event)
            self.invocations[event["event_id"]] = {
                "op": op, "state": None, "resource_id": payload.get("document_id"),
                "timestamp": event["timestamp"], "outcome": "error"}
            raise
        except Exception as exc:  # noqa: BLE001 — normalized to INTERNAL_ERROR
            event = build_audit_event(
                event_type=f"knowledge_fabric.{op}", actor_id=actor.actor_id,
                action=spec["action"], resource_type="Document", result="error",
                resource_id=payload.get("document_id"),
                error_code="INTERNAL_ERROR", reason=str(exc)[:200],
                correlation_id=ctx.correlation_id, source_ip=source_ip)
            self.audit_sink.emit(event)
            raise RegistryError("INTERNAL_ERROR",
                                operator_detail=f"unexpected: {exc}") from exc

        event = build_audit_event(
            event_type=f"knowledge_fabric.{op}", actor_id=actor.actor_id,
            action=spec["action"], resource_type="Document", result="success",
            resource_id=payload.get("document_id"),
            classification=(self.source.get(payload["document_id"]).classification
                            if payload.get("document_id") and
                            self.source.get(payload.get("document_id")) else None),
            correlation_id=ctx.correlation_id, source_ip=source_ip)
        self.audit_sink.emit(event)
        self.invocations[event["event_id"]] = {
            "op": op, "state": data.get("document_state"),
            "resource_id": payload.get("document_id"),
            "timestamp": event["timestamp"], "outcome": "success"}
        return OpResult(op=op, data=data,
                        resource_id=payload.get("document_id"),
                        audit_event_id=event["event_id"],
                        correlation_id=ctx.correlation_id,
                        state=data.get("document_state"))
