"""Claim store — claim_extraction (op 02) and claim_to_source_mapping (op 03).

Claims are segments of an agent answer (features/14 file 02) with their source
spans; each claim may link to one or more Evidence rows (file 03). Production:
the `claims` columns of the evidence_links schema; stub: in-process maps.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class ClaimStore:
    def __init__(self) -> None:
        self._by_task: Dict[str, List[Dict[str, Any]]] = {}
        self._by_id: Dict[str, Dict[str, Any]] = {}
        self._claim_links: Dict[str, List[str]] = {}   # claim_id -> evidence_ids

    def put(self, task_id: str, claims: List[Dict[str, Any]]) -> None:
        """Replace the claim set for a task (re-extraction is idempotent bookkeeping)."""
        for old in self._by_task.get(task_id, []):
            self._by_id.pop(old["claim_id"], None)
            self._claim_links.pop(old["claim_id"], None)
        self._by_task[task_id] = claims
        for claim in claims:
            self._by_id[claim["claim_id"]] = {**claim, "task_id": task_id}

    def get_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        return self._by_id.get(claim_id)

    def claims_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        return list(self._by_task.get(task_id, []))

    def link_claim(self, claim_id: str, evidence_id: str) -> None:
        links = self._claim_links.setdefault(claim_id, [])
        if evidence_id not in links:
            links.append(evidence_id)

    def evidence_for_claim(self, claim_id: str) -> List[str]:
        return list(self._claim_links.get(claim_id, []))
