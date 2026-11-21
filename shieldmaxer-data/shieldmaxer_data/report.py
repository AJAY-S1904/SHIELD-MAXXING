"""Dataset quality report + provenance index."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from .schema import CanonicalRecord


def build_report(records: Iterable[CanonicalRecord], out_path: Path) -> dict:
    stats = {
        "total_records": 0,
        "by_label": Counter(),
        "by_language": Counter(),
        "by_script": Counter(),
        "by_category": Counter(),
        "by_source": Counter(),
        "romanized_count": 0,
        "code_mixed_count": 0,
        "jailbreak_count": 0,
        "benign_sensitive_count": 0,
        "license_counts": Counter(),
        "provenance": {},
    }

    for rec in records:
        stats["total_records"] += 1
        stats["by_label"][rec.label] += 1
        if rec.language:
            stats["by_language"][rec.language] += 1
        stats["by_script"][rec.script] += 1
        for c in rec.categories:
            stats["by_category"][c] += 1
        stats["by_source"][rec.source_dataset] += 1
        if rec.romanized:
            stats["romanized_count"] += 1
        if rec.code_mixed:
            stats["code_mixed_count"] += 1
        if rec.is_jailbreak:
            stats["jailbreak_count"] += 1
        if rec.is_benign_sensitive:
            stats["benign_sensitive_count"] += 1
        if rec.license:
            stats["license_counts"][rec.license] += 1

    # convert Counters to plain dicts for JSON
    serializable = {k: (dict(v) if isinstance(v, Counter) else v) for k, v in stats.items()}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

    return serializable


def print_summary(stats: dict) -> None:
    print("\n=== Shield Maxer Data Report ===")
    print(f"Total records: {stats['total_records']:,}")
    print(f"  safe: {stats['by_label'].get('safe', 0):,}  unsafe: {stats['by_label'].get('unsafe', 0):,}  ambiguous: {stats['by_label'].get('ambiguous', 0):,}")
    print(f"  romanized: {stats['romanized_count']:,}  code-mixed: {stats['code_mixed_count']:,}")
    print(f"  jailbreak: {stats['jailbreak_count']:,}  benign-sensitive: {stats['benign_sensitive_count']:,}")
    print(f"\nTop languages: {dict(list(stats['by_language'].items())[:10])}")
    print(f"Scripts: {stats['by_script']}")
    print(f"\nCategories: {stats['by_category']}")
    print(f"\nSources: {stats['by_source']}")
    print(f"\nLicenses: {stats['license_counts']}")