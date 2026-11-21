"""Deduplication & leakage-safe grouping.

*Exact*: identical normalised text → one canonical record.
*Near-duplicate*: MinHash LSH (Jaccard ≥ 0.8) → connected components.
*Explicit translation groups*: `parent_id` (original English prompt) +
  `source_id` per language forms a group. We always keep the *parent* for
  English, others as translations. Split happens at **group** level so that
  no translation of the same seed appears in two different splits.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Iterator

from datasketch import MinHash, MinHashLSH

from .schema import CanonicalRecord, normalize_text, stable_hash

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DedupResult:
    unique: list[CanonicalRecord]
    dropped: int
    groups: dict[str, list[str]]  # group_id -> list of record_ids


def _minhash(text: str, num_perm: int = 128) -> MinHash:
    m = MinHash(num_perm=num_perm)
    # 3-gram shingles
    tokens = [text[i : i + 3] for i in range(len(text) - 2)]
    for tok in tokens:
        m.update(tok.encode("utf-8"))
    return m


def deduplicate(
    records: Iterable[CanonicalRecord],
    *,
    threshold: float = 0.8,
    num_perm: int = 128,
) -> DedupResult:
    """Exact + near-duplicate dedupe with MinHash LSH.

    Returns DedupResult with unique records and a `groups` mapping that can be
    used downstream for group-level splitting.
    """
    # 1) exact text hash dedupe
    exact_seen: dict[str, CanonicalRecord] = {}
    for rec in records:
        h = rec.text_hash
        if h in exact_seen:
            # merge provenance
            prev = exact_seen[h]
            prev.provenance.setdefault("duplicates", []).append(rec.record_id)
        else:
            exact_seen[h] = rec

    uniq = list(exact_seen.values())
    logger.info("Exact dedupe: %d → %d", len(records) if hasattr(records, "__len__") else "stream", len(uniq))

    # 2) MinHash LSH near-dup
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    minhashes: dict[str, MinHash] = {}
    for rec in uniq:
        mh = _minhash(rec.text, num_perm)
        minhashes[rec.record_id] = mh
        lsh.insert(rec.record_id, mh)

    # 3) connected components over near-dup edges
    parent: dict[str, str] = {rid: rid for rid in minhashes}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for rec in uniq:
        cand = lsh.query(minhashes[rec.record_id])
        for other in cand:
            if other != rec.record_id:
                union(rec.record_id, other)

    groups = defaultdict(list)
    for rid in minhashes:
        groups[find(rid)].append(rid)

    # keep the *first* record in each component as canonical
    canonical_ids = {comp[0] for comp in groups.values()}
    final = [r for r in uniq if r.record_id in canonical_ids]

    # 4) attach group_id = component root for downstream splitting
    for rec in final:
        rec.group_id = f"grp:{find(rec.record_id)}"

    logger.info("Near-dup components: %d", len(groups))
    return DedupResult(unique=final, dropped=len(uniq) - len(final), groups={k: v for k, v in groups.items()})


def build_translation_groups(records: Iterable[CanonicalRecord]) -> dict[str, list[str]]:
    """Create group_id based on explicit parent_id / translation links.

    Priority:
      1. parent_id (usually the English source prompt id) → group
      2. source_id where a dataset gives parallel translations (e.g. MultiJail)
    Falls back to MinHash group_id if neither present.
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for rec in records:
        if rec.parent_id:
            gid = f"trans:{rec.parent_id}"
        elif rec.source_dataset == "DAMO-NLP-SG/MultiJail" and "_" in (rec.source_id or ""):
            # MultiJail uses parent_id=<en_text>, source_id=<id>_<lang>
            gid = f"mj:{rec.source_id.split('_')[0]}"
        else:
            gid = rec.group_id or f"txt:{rec.text_hash}"
        rec.group_id = gid
        groups[gid].append(rec.record_id)
    return dict(groups)