"""Leakage-safe grouped splits.

Splits are done at **group** level (translation groups + MinHash components)
so that no paraphrase/translation of the same seed appears in more than
one split.

Default ratios: 80 / 10 / 10  (train / val / test).
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .schema import CanonicalRecord, stable_hash

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SplitResult:
    train: list[CanonicalRecord]
    val: list[CanonicalRecord]
    test: list[CanonicalRecord]
    group_stats: dict[str, dict]  # split -> {groups, records, labels, languages}


def grouped_split(
    records: Iterable[CanonicalRecord],
    *,
    ratios: tuple[float, float, float] = (0.8, 0.1, 0.1),
    seed: int = 42,
) -> SplitResult:
    """Split by group_id; deterministic via seeded rng on group key."""
    assert abs(sum(ratios) - 1.0) < 1e-9
    train_r, val_r, _ = ratios

    # collect groups
    groups: dict[str, list[CanonicalRecord]] = defaultdict(list)
    for rec in records:
        groups[rec.group_id].append(rec)

    # deterministic shuffle of group keys
    group_keys = list(groups.keys())
    rng = random.Random(seed)
    rng.shuffle(group_keys)

    n = len(group_keys)
    n_train = int(n * train_r)
    n_val = int(n * val_r)

    train_keys = set(group_keys[:n_train])
    val_keys = set(group_keys[n_train : n_train + n_val])
    test_keys = set(group_keys[n_train + n_val :])

    train, val, test = [], [], []
    stats = {"train": _empty_stats(), "val": _empty_stats(), "test": _empty_stats()}

    for gid, recs in groups.items():
        if gid in train_keys:
            split = "train"
            out = train
        elif gid in val_keys:
            split = "val"
            out = val
        else:
            split = "test"
            out = test

        for rec in recs:
            out.append(rec)
            _add_stats(stats[split], rec)

    for k in stats:
        stats[k]["groups"] = len(train_keys if k == "train" else val_keys if k == "val" else test_keys)

    logger.info("Split sizes: train=%d val=%d test=%d (groups %d/%d/%d)", len(train), len(val), len(test), len(train_keys), len(val_keys), len(test_keys))
    return SplitResult(train=train, val=val, test=test, group_stats=stats)


def _empty_stats() -> dict:
    return {"groups": 0, "records": 0, "labels": defaultdict(int), "languages": defaultdict(int), "scripts": defaultdict(int), "categories": defaultdict(int)}


def _add_stats(stats: dict, rec: CanonicalRecord) -> None:
    stats["records"] += 1
    stats["labels"][rec.label] += 1
    if rec.language:
        stats["languages"][rec.language] += 1
    stats["scripts"][rec.script] += 1
    for c in rec.categories:
        stats["categories"][c] += 1


def write_splits(result: SplitResult, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for split_name, records in (("train", result.train), ("val", result.val), ("test", result.test)):
        path = out_dir / f"{split_name}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(rec.to_json() + "\n")
        logger.info("Wrote %s (%d records)", path, len(records))

    # stats
    stats_path = out_dir / "split_stats.json"
    with stats_path.open("w", encoding="utf-8") as f:
        serializable = {k: {kk: (dict(vv) if isinstance(vv, defaultdict) else vv) for kk, vv in v.items()} for k, v in result.group_stats.items()}
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    # manifest
    manifest = {
        "train_count": len(result.train),
        "val_count": len(result.val),
        "test_count": len(result.test),
        "total_groups": sum(v["groups"] for v in result.group_stats.values()),
        "schema_version": "0.1.0",
    }
    with (out_dir / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)