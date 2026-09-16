"""Ops layer — the ten feature ops of docs/features/14_evidence_and_provenance/.

Each op is validated against the canonical contracts, authorized by the
permission matrix (Document:execute for all ten — feature docs §16), executed
against the evidence_links store inside one logical operation, and audited with
exactly one `evidence_and_provenance.<op>` invocation event (success, error, or
denial — feature docs §22/§28: the store write and the audit event are one
operation, never two independently-failable writes).

Ops (slug → feature file):
- evidence_system (01)             create an Evidence row (+ optional enrichment from
                                   industrial-service /internal/resolve-tag and
                                   /internal/validate-finding when the payload carries
                                   the optional `equipment_tag` / `finding` extensions —
                                   the Character-3 ingest wiring named in the industrial
                                   changelog; fail closed, see industrial_gateway.py)
- claim_extraction (02)            segment an agent answer into checkable claims
- claim_to_source_mapping (03)     link a claim to its supporting Evidence
- page_level_citations (04)        Source→Version→Page citation for a claim
- coordinate_level_citations (05)  page + bbox citation for a claim
- source_chain (06)                Source→Version→Page/Section→Chunk chain walk
- evidence_graph (07)              claims/evidence/sources graph for a task
- confidence (08)                  four-axis qualitative representation (never
                                   a single 0–100% number — §3a)
- unsupported_claim_detection (09) claims without Evidence rows (domain/13:
                                   an agent MUST NOT emit a claim without one); also runs
                                   the cross-source contradiction pass via industrial
                                   /internal/detect-conflicts when op 01 ingested
                                   evidence for an equipment (industrial/14 case 2) —
                                   conflicting rows become 'contradicted' (upgrade only;
                                   never downgraded by anything)
- evidence_failures (10)           structured diagnosis of evidence problems

Evidence carries no state machine of its own: the canonical Document machine
(runtime/_state_machines_canonical.md) governs documents; Evidence rows are
created immutable except `verification_status`, written only by op 09.

Errors come only from the canonical registry (reference/01): INVALID_REQUEST,
FILE_NOT_FOUND, FILE_CLASSIFICATION_DENIED, TOOL_NOT_ALLOWED, POLICY_DENIED,
RESOURCE_CONFLICT, RAG_INDEX_UNAVAILABLE, DEPENDENCY_UNAVAILABLE, INTERNAL_ERROR.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .audit import AuditSink, build_audit_event
from .config import Settings
from .domain import (Citation, Evidence, is_uuid, now_iso,
                     validate_citation_fields, validate_evidence_fields)
from .errors import RegistryError
from .industrial_gateway import IndustrialGatewayClient
from .policy import Actor, enforce
from .retry import run_with_retry
from .storage import EvidenceLinks, RetrievalView, SourceChainStore


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


CLAIM_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


# ------------------------------------------------------------------ shared helpers

def _require_uuid(payload: Dict[str, Any], field_name: str) -> str:
    from .domain import is_uuid
    value = payload.get(field_name)
    if not is_uuid(value):
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": field_name, "issue": "required uuid"}],
                            operator_detail=f"{field_name} required")
    return value


def _require_str(payload: Dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": field_name,
                                      "issue": "required non-empty string"}],
                            operator_detail=f"{field_name} required")
    return value


def _load_evidence(service: "EvidenceService", evidence_id: str) -> Evidence:
    ev = service.links.get(evidence_id)
    if ev is None:
        raise RegistryError("FILE_NOT_FOUND",
                            operator_detail=f"evidence {evidence_id} not found")
    return ev


def _new_evidence_from_payload(service: "EvidenceService",
                               payload: Dict[str, Any]) -> Evidence:
    """Validate Evidence fields against schemas/09 and build the row.

    Caller-supplied verification_status is ignored (created rows start
    `unverified`); only the verification pipeline (op 09) sets it (domain/13).
    """
    errors: List[Dict[str, str]] = []
    validate_evidence_fields(payload, errors)
    if errors:
        raise RegistryError("INVALID_REQUEST", details=errors,
                            operator_detail="evidence payload failed schema validation")
    return Evidence(
        task_id=payload["task_id"],
        source_document_id=payload["source_document_id"],
        document_version=payload["document_version"],
        chunk_id=payload["chunk_id"],
        page_number=payload.get("page_number"),
        section_reference=payload.get("section_reference"),
        source_hash=payload["source_hash"],
        retrieval_method=payload["retrieval_method"],
        source_authority=payload["source_authority"],
        confidence=payload.get("confidence"),
    )


def _chunk_view(service: "EvidenceService", chunk_id: str) -> Dict[str, Any]:
    view = service.retrieval.get(chunk_id)
    if view is None:
        raise RegistryError("RAG_INDEX_UNAVAILABLE",
                            operator_detail=f"chunk {chunk_id} not present in the "
                            f"retrieval view (knowledge-fabric seam down or unindexed)")
    return view


def _contradicted_document_ids(service: "EvidenceService", equipment_id: str,
                               rows: List[Evidence]) -> set:
    """Evidence documents contradicting each other for one equipment.

    Builds industrial/14's claim dicts from the evidence rows and runs the
    deterministic detector. Claim shape: the parameter is the section reference
    (two documents asserting what the same section says), the value is the
    chunk text (the content being asserted), and authority/validity windows
    come from the source-chain store — the same facts ops 06/08 read. Rows
    without a section reference, chunk text, or chain facts cannot assert
    anything and are skipped. Returns the set of source document ids that
    participate in at least one ConflictRecord (status 'unresolved' — the
    detector never auto-resolves; evidence-service owns the consequence).
    """
    claims: List[Dict[str, Any]] = []
    for ev in rows:
        if not ev.section_reference:
            continue
        chunk = service.retrieval.get(ev.chunk_id)
        if not chunk or not chunk.get("text"):
            continue
        row = service.chains.version_row(ev.source_document_id, ev.document_version)
        if row is None:
            continue
        claims.append({
            "document_id": ev.source_document_id,
            "document_name": f"document {ev.source_document_id} "
                             f"v{ev.document_version}",
            "authority": row.get("authority") or "unknown",
            "effective_from": row.get("effective_from"),
            "effective_until": row.get("effective_until"),
            "parameter": ev.section_reference,
            "value": chunk.get("text"),
        })
    if len(claims) < 2:
        return set()
    conflicts = service.industrial.detect_conflicts(equipment_id, claims)
    out: set = set()
    for conflict in conflicts:
        out.add(str(conflict.get("source_a_document_id")))
        out.add(str(conflict.get("source_b_document_id")))
    return out


def _enrich_from_industrial(service: "EvidenceService",
                            payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Cross-service enrichment for ingest (op 01) — industrial-service.

    When the payload carries `equipment_tag` (+ `within_unit_id`, `plant_id`)
    and/or a `finding` object, both /internal endpoints are called BEFORE the
    Evidence row is persisted: enrichment failure raises (DEPENDENCY_UNAVAILABLE
    or POLICY_DENIED), so ingest never silently stores an unenriched row
    (fail closed). Payloads without these optional keys never touch the
    dependency. Resolution case-2 (ambiguous) results are surfaced verbatim for
    human confirmation — this service never persists governed_by edges.
    """
    tag = payload.get("equipment_tag")
    unit = payload.get("within_unit_id")
    plant = payload.get("plant_id")
    finding = payload.get("finding")
    check = payload.get("conflict_check")
    if tag is None and finding is None and check is None:
        return None
    out: Dict[str, Any] = {}
    if tag is not None:
        if not isinstance(tag, str) or not tag.strip() or not is_uuid(unit) \
                or not is_uuid(plant):
            raise RegistryError(
                "INVALID_REQUEST",
                details=[{"field": "equipment_tag",
                          "issue": "required non-empty string"},
                         {"field": "within_unit_id/plant_id",
                          "issue": "required uuids when equipment_tag is present"}],
                operator_detail="industrial enrichment requires equipment_tag "
                                "with within_unit_id and plant_id")
        out["equipment_resolution"] = service.industrial.resolve_tag(
            tag_number=tag.strip(), within_unit_id=unit, plant_id=plant)
    if finding is not None:
        if not isinstance(finding, dict):
            raise RegistryError(
                "INVALID_REQUEST",
                details=[{"field": "finding", "issue": "must be an object"}],
                operator_detail="finding enrichment requires a JSON object")
        out["finding_validation"] = service.industrial.validate_finding(finding)
    check = payload.get("conflict_check")
    if check is not None:
        if not isinstance(check, dict) or not is_uuid(check.get("equipment_id")) \
                or not isinstance(check.get("claims"), list):
            raise RegistryError(
                "INVALID_REQUEST",
                details=[{"field": "conflict_check",
                          "issue": "must be an object with equipment_id (uuid) "
                                   "and claims (list)"}],
                operator_detail="conflict_check enrichment requires equipment_id "
                                "and claims")
        out["conflicts"] = service.industrial.detect_conflicts(
            check["equipment_id"], check["claims"])
    return out


def _attach_citation_if_requested(service: "EvidenceService", ev: Evidence,
                                  payload: Dict[str, Any]) -> Optional[Citation]:
    """Render a Citation (schemas/10) when the payload carries a text span."""
    if "text_span_start" not in payload and "text_span_end" not in payload:
        return None
    errors: List[Dict[str, str]] = []
    validate_citation_fields({"evidence_id": ev.id,
                              "text_span_start": payload.get("text_span_start"),
                              "text_span_end": payload.get("text_span_end")}, errors)
    if errors:
        raise RegistryError("INVALID_REQUEST", details=errors,
                            operator_detail="citation span failed schema validation")
    citation = service.links.add_citation(Citation(
        evidence_id=ev.id, text_span_start=payload["text_span_start"],
        text_span_end=payload["text_span_end"]))
    return citation


# -------------------------------------------------------------- 01 evidence_system

def handle_evidence_system(service: "EvidenceService", ctx: Context,
                           payload: Dict[str, Any]) -> Dict[str, Any]:
    # Enrichment precedes persistence (fail closed); additive to the base op —
    # payloads without the optional extensions behave exactly as before.
    enrichment = _enrich_from_industrial(service, payload)
    ev = _new_evidence_from_payload(service, payload)
    service.links.add(ev)
    result = {"evidence": ev.to_dict(), "evidence_id": ev.id}
    if enrichment is not None:
        result["industrial_enrichment"] = enrichment
        # Record which equipment this task's evidence was resolved against so
        # op 09 can run the contradiction pass later (industrial/14 case 2).
        # STUB: in-process registry; the real lookup joins the knowledge graph's
        # governed_by edges once PostgreSQL/KG land (DEC-023 seam).
        resolution = enrichment.get("equipment_resolution")
        if isinstance(resolution, dict) and resolution.get("matched_equipment_id"):
            service.conflict_targets.setdefault(ev.task_id, set()).add(
                str(resolution["matched_equipment_id"]))
    return result


# -------------------------------------------------------------- 02 claim_extraction

def handle_claim_extraction(service: "EvidenceService", ctx: Context,
                            payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = _require_uuid(payload, "task_id")
    answer_text = _require_str(payload, "answer_text")
    if len(answer_text) > service.settings.claim_max_chars:
        raise RegistryError(
            "INVALID_REQUEST",
            details=[{"field": "answer_text",
                      "issue": f"exceeds {service.settings.claim_max_chars} chars"}],
            operator_detail="answer_text too long for claim extraction")
    claims: List[Dict[str, Any]] = []
    cursor = 0
    for text in CLAIM_SPLIT.split(answer_text):
        text = text.strip()
        if not text:
            continue
        start = answer_text.find(text, cursor)
        end = start + len(text)
        cursor = end
        claims.append({"claim_id": str(uuid.uuid4()), "text": text,
                       "span_start": start, "span_end": end})
    service.claims.put(task_id, claims)
    return {"task_id": task_id, "claims": claims, "claim_count": len(claims)}


# -------------------------------------------------------- 03 claim_to_source_mapping

def handle_claim_to_source_mapping(service: "EvidenceService", ctx: Context,
                                   payload: Dict[str, Any]) -> Dict[str, Any]:
    claim_id = _require_uuid(payload, "claim_id")
    claim = service.claims.get_claim(claim_id)
    if claim is None:
        raise RegistryError("FILE_NOT_FOUND",
                            operator_detail=f"claim {claim_id} not found — run "
                            f"claim_extraction first")
    if payload.get("task_id") and payload["task_id"] != claim["task_id"]:
        # domain/13: task_id is 'which task's answer this evidence supports' — an
        # evidence row cannot support a claim from a different task.
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "task_id",
                                      "issue": "must match the claim's task"}],
                            operator_detail="evidence task_id does not match claim's task")
    ev = _new_evidence_from_payload(service, payload)
    service.links.add(ev)
    service.claims.link_claim(claim_id, ev.id)
    return {"claim_id": claim_id, "evidence": ev.to_dict(), "evidence_id": ev.id,
            "task_id": ev.task_id}


# -------------------------------------------------------- 04 page_level_citations

def handle_page_level_citations(service: "EvidenceService", ctx: Context,
                                payload: Dict[str, Any]) -> Dict[str, Any]:
    evidence_id = _require_uuid(payload, "evidence_id")
    ev = _load_evidence(service, evidence_id)
    chunk = _chunk_view(service, ev.chunk_id)
    page_number = ev.page_number if ev.page_number is not None else chunk.get("page_number")
    if page_number is None:
        raise RegistryError(
            "INVALID_REQUEST",
            details=[{"field": "page_number",
                      "issue": "no page number on the evidence row or its chunk"}],
            operator_detail="page number unavailable for this evidence")
    citation = _attach_citation_if_requested(service, ev, payload)
    return {"evidence_id": evidence_id, "source_document_id": ev.source_document_id,
            "document_version": ev.document_version, "page_number": page_number,
            "citation": citation.to_dict() if citation else None}


# --------------------------------------------------- 05 coordinate_level_citations

def handle_coordinate_level_citations(service: "EvidenceService", ctx: Context,
                                      payload: Dict[str, Any]) -> Dict[str, Any]:
    evidence_id = _require_uuid(payload, "evidence_id")
    ev = _load_evidence(service, evidence_id)
    chunk = _chunk_view(service, ev.chunk_id)
    bbox = chunk.get("bbox")
    if not bbox:
        raise RegistryError(
            "INVALID_REQUEST",
            details=[{"field": "bbox",
                      "issue": "source chunk has no coordinate data"}],
            operator_detail="coordinate citation unavailable: chunk carries no bbox")
    page_number = ev.page_number if ev.page_number is not None else chunk.get("page_number")
    citation = _attach_citation_if_requested(service, ev, payload)
    return {"evidence_id": evidence_id, "source_document_id": ev.source_document_id,
            "document_version": ev.document_version,
            "page_number": page_number, "bbox": list(bbox),
            "section_reference": ev.section_reference,
            "citation": citation.to_dict() if citation else None}


# ------------------------------------------------------------------- 06 source_chain

def handle_source_chain(service: "EvidenceService", ctx: Context,
                        payload: Dict[str, Any]) -> Dict[str, Any]:
    evidence_id = _require_uuid(payload, "evidence_id")
    ev = _load_evidence(service, evidence_id)
    chain_store = service.chains
    steps: List[Dict[str, Any]] = []
    current_doc: Optional[str] = ev.source_document_id
    current_version: Optional[int] = ev.document_version
    seen: set = set()
    while current_doc is not None and current_version is not None:
        key = (current_doc, current_version)
        if key in seen:
            raise RegistryError("RESOURCE_CONFLICT",
                                operator_detail="cyclic supersession chain detected")
        seen.add(key)
        if len(steps) > service.settings.source_chain_max_depth:
            raise RegistryError("RESOURCE_CONFLICT",
                                operator_detail="supersession chain exceeds max depth")
        row = chain_store.version_row(current_doc, current_version)
        if row is None:
            raise RegistryError(
                "RAG_INDEX_UNAVAILABLE",
                operator_detail=f"source chain broken: document {current_doc} "
                f"version {current_version} unknown to the source chain store")
        superseded_by = row.get("superseded_by")
        is_superseded = bool(superseded_by) or chain_store.is_superseded(current_doc, current_version)
        steps.append({
            "document_id": current_doc,
            "version": row["version"],
            "sha256": row["sha256"],
            "authority": row["authority"],
            "effective_from": row.get("effective_from"),
            "effective_until": row.get("effective_until"),
            "superseded_by": superseded_by,
            "is_current": not is_superseded,
        })
        if superseded_by:
            nxt = chain_store.current_version(superseded_by)
            current_doc, current_version = superseded_by, (nxt or {}).get("version")
        else:
            current_doc, current_version = None, None
    return {"evidence_id": evidence_id, "chain": steps,
            "complete": bool(steps) and steps[-1]["is_current"]}


# ------------------------------------------------------------------- 07 evidence_graph

def handle_evidence_graph(service: "EvidenceService", ctx: Context,
                          payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = _require_uuid(payload, "task_id")
    evidence_rows = service.links.for_task(task_id)
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    for ev in evidence_rows:
        nodes.append({"kind": "evidence", "id": ev.id,
                      "source_document_id": ev.source_document_id,
                      "chunk_id": ev.chunk_id,
                      "verification_status": ev.verification_status,
                      "source_authority": ev.source_authority})
        edges.append({"kind": "derived_from", "from": ev.id,
                      "to": f"document:{ev.source_document_id}"})
        edges.append({"kind": "extracted_from", "from": ev.id,
                      "to": f"chunk:{ev.chunk_id}"})
    for claim in service.claims.claims_for_task(task_id):
        nodes.append({"kind": "claim", "id": claim["claim_id"],
                      "text": claim["text"],
                      "span_start": claim["span_start"],
                      "span_end": claim["span_end"]})
        for eid in service.claims.evidence_for_claim(claim["claim_id"]):
            edges.append({"kind": "supported_by", "from": claim["claim_id"],
                          "to": eid})
    # Co-source edges: evidence rows sharing a source document (cross-source
    # agreement signals feed industrial/14 conflict detection).
    by_doc: Dict[str, List[str]] = {}
    for ev in evidence_rows:
        by_doc.setdefault(ev.source_document_id, []).append(ev.id)
    for doc_id, eids in by_doc.items():
        for i in range(len(eids)):
            for j in range(i + 1, len(eids)):
                edges.append({"kind": "shares_source", "from": eids[i],
                              "to": eids[j], "document_id": doc_id})
    return {"task_id": task_id,
            "node_count": len(nodes), "edge_count": len(edges),
            "nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------- 08 confidence

def _freshness_axis(service: "EvidenceService", ev: Evidence) -> str:
    row = service.chains.version_row(ev.source_document_id, ev.document_version)
    if row is None:
        return "Unknown"
    if row.get("effective_until") or service.chains.is_superseded(
            ev.source_document_id, ev.document_version):
        return "Superseded"
    if row.get("effective_from"):
        return "Current"
    return "Undated"


_AUTHORITY_AXIS = {"primary": "Primary", "secondary": "Secondary",
                   "reference": "Reference"}
_AGREEMENT_AXIS = {"supported": "Agreement", "contradicted": "Contradicted",
                   "unsupported": "Unverified", "unverified": "Unverified"}


def handle_confidence(service: "EvidenceService", ctx: Context,
                      payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = _require_uuid(payload, "task_id")
    evidence_rows = service.links.for_task(task_id)
    claims = service.claims.claims_for_task(task_id)

    # Coverage axis: claims with >=1 matching Evidence row, over total claims
    # (feature 08 §3a). If no claims were extracted, coverage is Unknown —
    # never invented.
    if claims:
        covered = sum(1 for c in claims
                      if service.claims.evidence_for_claim(c["claim_id"]))
        ratio = covered / len(claims)
        if ratio >= service.settings.coverage_high_ratio:
            coverage = "High"
        elif ratio >= service.settings.coverage_partial_ratio:
            coverage = "Partial"
        else:
            coverage = "Low"
        coverage_detail = {"covered_claims": covered, "total_claims": len(claims)}
    else:
        coverage = "Unknown"
        coverage_detail = {"reason": "no claims extracted for this task "
                                     "(run claim_extraction)"}

    per_evidence = []
    for ev in evidence_rows:
        per_evidence.append({
            "evidence_id": ev.id,
            "source_authority": _AUTHORITY_AXIS[ev.source_authority],
            "freshness": _freshness_axis(service, ev),
            "cross_source_agreement": _AGREEMENT_AXIS[ev.verification_status],
        })

    # The raw retrieval score is exposed ONLY as a clearly-labeled ranking
    # signal for the operator debug view (domain/13 methodology; master prompt
    # §12 anti-pattern). No combined 0-100% number is computed — the four axes
    # above are the user-facing representation (ui/09_evidence_panel.md).
    raw_debug = {"label": "retrieval ranking signal — NOT a correctness probability",
                 "values": [{"evidence_id": ev.id, "confidence": ev.confidence}
                            for ev in evidence_rows if ev.confidence is not None]}
    return {"task_id": task_id,
            "axes": {"evidence_coverage": coverage,
                     "evidence_coverage_detail": coverage_detail,
                     "source_authority": sorted({_AUTHORITY_AXIS[ev.source_authority]
                                                 for ev in evidence_rows}) if evidence_rows else [],
                     "freshness": sorted({_freshness_axis(service, ev)
                                          for ev in evidence_rows}) if evidence_rows else [],
                     "cross_source_agreement": sorted({_AGREEMENT_AXIS[ev.verification_status]
                                                       for ev in evidence_rows}) if evidence_rows else []},
            "per_evidence": per_evidence,
            "raw_confidence_debug": raw_debug}


# ---------------------------------------------------- 09 unsupported_claim_detection

def handle_unsupported_claim_detection(service: "EvidenceService", ctx: Context,
                                       payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = _require_uuid(payload, "task_id")
    claims = service.claims.claims_for_task(task_id)
    if not claims:
        raise RegistryError(
            "FILE_NOT_FOUND",
            operator_detail=f"no extracted claims for task {task_id} — run "
                            f"claim_extraction first")
    need = service.settings.min_supporting_evidence
    unsupported: List[Dict[str, Any]] = []
    supported_claims = 0
    for claim in claims:
        eids = service.claims.evidence_for_claim(claim["claim_id"])
        if len(eids) >= need:
            supported_claims += 1
        else:
            unsupported.append({"claim_id": claim["claim_id"],
                                "text": claim["text"],
                                "supporting_evidence": len(eids)})

    # Verification-status writes: rows mapped to supported claims become
    # `supported`; `contradicted` is NEVER downgraded (it is conflict
    # detection's output — industrial/14). Unmapped rows stay `unverified`.
    verification_updates = 0
    for claim in claims:
        for eid in service.claims.evidence_for_claim(claim["claim_id"]):
            if len(service.claims.evidence_for_claim(claim["claim_id"])) < need:
                continue
            ev = service.links.get(eid)
            if ev is not None and ev.verification_status == "unverified":
                service.links.set_verification_status(eid, "supported")
                verification_updates += 1

    # Cross-source contradiction pass (industrial/14 case 2, via
    # /internal/detect-conflicts): when op 01 ingested evidence for an
    # equipment, the deterministic detector arbitrates cross-document
    # disagreement over the same section. Every Evidence row whose source
    # document participates in a ConflictRecord becomes 'contradicted' — an
    # UPGRADE only: the supported-loop above touches 'unverified' rows, and
    # nothing in this service ever downgrades 'contradicted' (industrial/14's
    # output). Detector unavailable: skip the pass — detection failure must
    # never fabricate a status; the next op-09 run catches up.
    verification_contradictions = 0
    evidence_rows = service.links.for_task(task_id)
    for equipment_id in sorted(service.conflict_targets.get(task_id, set())):
        try:
            contradicted_docs = _contradicted_document_ids(service, equipment_id,
                                                           evidence_rows)
        except RegistryError as err:
            if err.code not in ("DEPENDENCY_UNAVAILABLE", "RAG_INDEX_UNAVAILABLE"):
                raise
            continue
        for ev in evidence_rows:
            if (ev.source_document_id in contradicted_docs
                    and ev.verification_status != "contradicted"):
                service.links.set_verification_status(ev.id, "contradicted")
                verification_contradictions += 1

    total = len(claims)
    ratio = len(unsupported) / total
    flagged = ratio >= service.settings.unsupported_flag_ratio
    return {"task_id": task_id, "total_claims": total,
            "supported_claim_count": supported_claims,
            "unsupported_claim_count": len(unsupported),
            "unsupported_claims": unsupported,
            "unsupported_ratio": round(ratio, 6),
            "flagged": flagged,
            "verification_status_updates": verification_updates,
            "verification_contradictions": verification_contradictions}


# ------------------------------------------------------------------ 10 evidence_failures

def handle_evidence_failures(service: "EvidenceService", ctx: Context,
                             payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = payload.get("task_id")
    if task_id is not None:
        evidence_rows = service.links.for_task(str(task_id))
    elif payload.get("evidence_id"):
        evidence_rows = [_load_evidence(service, str(payload["evidence_id"]))]
    else:
        raise RegistryError("INVALID_REQUEST",
                            details=[{"field": "task_id/evidence_id",
                                      "issue": "one of task_id or evidence_id required"}],
                            operator_detail="nothing to diagnose")
    diagnosis: List[Dict[str, Any]] = []
    for ev in evidence_rows:
        row = service.chains.version_row(ev.source_document_id, ev.document_version)
        if row is None:
            diagnosis.append({"evidence_id": ev.id, "issue": "source_chain_broken",
                              "detail": f"document {ev.source_document_id} "
                                        f"v{ev.document_version} unknown"})
        elif service.chains.is_superseded(ev.source_document_id, ev.document_version):
            diagnosis.append({"evidence_id": ev.id, "issue": "source_superseded",
                              "detail": "a newer version of the source document exists"})
        try:
            chunk = _chunk_view(service, ev.chunk_id)
        except RegistryError as err:
            diagnosis.append({"evidence_id": ev.id, "issue": "chunk_unavailable",
                              "detail": err.operator_detail})
            continue
        if chunk.get("page_number") is None and ev.page_number is None:
            diagnosis.append({"evidence_id": ev.id, "issue": "no_page_number",
                              "detail": "citation can resolve only to document level"})
        if not chunk.get("bbox"):
            diagnosis.append({"evidence_id": ev.id, "issue": "no_coordinates",
                              "detail": "coordinate-level citations unavailable"})
        if ev.verification_status == "unverified":
            diagnosis.append({"evidence_id": ev.id, "issue": "verification_pending",
                              "detail": "unsupported-claim detection has not run"})
    return {"diagnosis": diagnosis or [{"issue": "none"}],
            "evidence_count": len(evidence_rows)}


# ------------------------------------------------------------------------------ registry

OPS: Dict[str, Dict[str, Any]] = {
    "evidence_system": {"handler": handle_evidence_system, "action": "execute"},
    "claim_extraction": {"handler": handle_claim_extraction, "action": "execute"},
    "claim_to_source_mapping": {"handler": handle_claim_to_source_mapping, "action": "execute"},
    "page_level_citations": {"handler": handle_page_level_citations, "action": "execute"},
    "coordinate_level_citations": {"handler": handle_coordinate_level_citations, "action": "execute"},
    "source_chain": {"handler": handle_source_chain, "action": "execute"},
    "evidence_graph": {"handler": handle_evidence_graph, "action": "execute"},
    "confidence": {"handler": handle_confidence, "action": "execute"},
    "unsupported_claim_detection": {"handler": handle_unsupported_claim_detection, "action": "execute"},
    "evidence_failures": {"handler": handle_evidence_failures, "action": "execute"},
}


# ------------------------------------------------------------------------------ service

class EvidenceService:
    """Single implementation behind both the in-process entry points and the HTTP
    wrapper (feature docs §12 — exactly one implementation, not two)."""

    def __init__(self, *, links: EvidenceLinks, claims_store,
                 chains: SourceChainStore, retrieval: RetrievalView,
                 audit_sink: AuditSink, settings: Settings,
                 industrial: Optional[IndustrialGatewayClient] = None) -> None:
        self.links = links
        self.claims = claims_store
        self.chains = chains
        self.retrieval = retrieval
        self.audit_sink = audit_sink
        self.settings = settings
        # Cross-service enrichment client (industrial-service). Defaults from
        # settings; tests inject a stub, server.py uses the settings-built one.
        if industrial is None:
            industrial = IndustrialGatewayClient(
                base_url=settings.industrial_base_url,
                timeout_seconds=settings.industrial_timeout_seconds)
        self.industrial = industrial
        self.invocations: Dict[str, dict] = {}   # audit_event_id -> invocation summary
        self._idempotency: Dict[str, OpResult] = {}
        # task_id -> equipment ids whose evidence op 01 resolved for it. Read by
        # op 09's contradiction pass (industrial/14 case 2). STUB: in-process
        # registry; replaced by the knowledge-graph governed_by lookup later.
        self.conflict_targets: Dict[str, set] = {}

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

        idem_key = payload.get("idempotency_key")
        if isinstance(idem_key, str) and idem_key in self._idempotency:
            # Edge case §30: duplicate idempotency_key returns the original result
            # without re-executing. Still exactly one audit event for THIS invocation.
            prior = self._idempotency[idem_key]
            event = build_audit_event(
                event_type=f"evidence_and_provenance.{op}", actor_id=actor.actor_id,
                action=spec["action"], resource_type="Document", result="success",
                resource_id=prior.resource_id, reason="idempotent replay — original result returned",
                correlation_id=ctx.correlation_id, source_ip=source_ip)
            self.audit_sink.emit(event)
            return OpResult(op=op, data=prior.data, resource_id=prior.resource_id,
                            audit_event_id=event["event_id"],
                            correlation_id=ctx.correlation_id, state=prior.state)

        try:
            # Policy gate before any business logic (Document:execute per §16).
            enforce("Document", spec["action"], actor)

            handler: Callable = spec["handler"]

            def _run() -> Dict[str, Any]:
                return handler(self, ctx, payload)

            data = run_with_retry(_run, op)
        except RegistryError as err:
            event = build_audit_event(
                event_type=f"evidence_and_provenance.{op}", actor_id=actor.actor_id,
                action=spec["action"], resource_type="Document", result="error",
                resource_id=err.resource_id or _primary_id(payload),
                error_code=err.code, reason=err.operator_detail,
                correlation_id=ctx.correlation_id, source_ip=source_ip)
            self.audit_sink.emit(event)
            self.invocations[event["event_id"]] = {
                "op": op, "state": None, "resource_id": _primary_id(payload),
                "timestamp": event["timestamp"], "outcome": "error"}
            raise
        except Exception as exc:  # noqa: BLE001 — normalized to INTERNAL_ERROR
            event = build_audit_event(
                event_type=f"evidence_and_provenance.{op}", actor_id=actor.actor_id,
                action=spec["action"], resource_type="Document", result="error",
                resource_id=_primary_id(payload), error_code="INTERNAL_ERROR",
                reason=str(exc)[:200], correlation_id=ctx.correlation_id,
                source_ip=source_ip)
            self.audit_sink.emit(event)
            raise RegistryError("INTERNAL_ERROR",
                                operator_detail=f"unexpected: {exc}") from exc

        event = build_audit_event(
            event_type=f"evidence_and_provenance.{op}", actor_id=actor.actor_id,
            action=spec["action"], resource_type="Document", result="success",
            resource_id=data.get("evidence_id") or _primary_id(payload),
            correlation_id=ctx.correlation_id, source_ip=source_ip)
        self.audit_sink.emit(event)
        resource_id = data.get("evidence_id") or _primary_id(payload)
        self.invocations[event["event_id"]] = {
            "op": op, "state": None, "resource_id": resource_id,
            "timestamp": event["timestamp"], "outcome": "success"}
        result = OpResult(op=op, data=data, resource_id=resource_id,
                          audit_event_id=event["event_id"],
                          correlation_id=ctx.correlation_id, state=None)
        if isinstance(idem_key, str) and idem_key:
            self._idempotency[idem_key] = result
        return result


def _primary_id(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("evidence_id", "claim_id", "task_id", "id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None
