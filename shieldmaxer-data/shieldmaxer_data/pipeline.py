"""End-to-end build pipeline: pull → normalise → dedupe → split → report."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .dedupe import build_translation_groups, deduplicate
from .report import build_report, print_summary
from .schema import CanonicalRecord
from .sources import ADAPTERS, get_adapter, list_adapters
from .split import grouped_split, write_splits

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("shieldmaxer_data")


def build(
    out_dir: Path,
    *,
    max_per_source: int | None = None,
    include_gated: bool = False,
    include_nc: bool = False,
    ratios: tuple[float, float, float] = (0.8, 0.1, 0.1),
    seed: int = 42,
) -> None:
    # 1. Pull & normalise
    log.info("Pulling datasets...")
    all_records: list[CanonicalRecord] = []

    for name in ADAPTERS:
        if name in {"wildguardmix", "xstest", "harmbench", "strongreject", "lmsys_chat_1m", "wildchat_1m"} and not include_gated:
            log.info("Skipping gated %s (use --include-gated)", name)
            continue
        if name in {"beavertails", "indic_safety_eval"} and not include_nc:
            log.info("Skipping NC %s (use --include-nc)", name)
            continue
        try:
            adapter = get_adapter(name)
            log.info("Processing %s...", name)
            count = 0
            for rec in adapter(max_rows=max_per_source):
                all_records.append(rec)
                count += 1
            log.info("  → %d records", count)
        except Exception as e:
            log.warning("Adapter %s failed: %s", name, e)

    log.info("Total pulled: %d", len(all_records))

    # 2. Deduplicate
    log.info("Deduplicating...")
    dedup = deduplicate(all_records)
    uniq = dedup.unique
    log.info("After exact+near-dedup: %d (dropped %d)", len(uniq), dedup.dropped)

    # 3. Translation groups (leakage-safe key)
    build_translation_groups(uniq)

    # 4. Split
    log.info("Splitting (group-level)...")
    split_res = grouped_split(uniq, ratios=ratios, seed=seed)

    # 5. Write outputs
    write_splits(split_res, out_dir)

    # 6. Report
    report_path = out_dir / "report.json"
    stats = build_report(uniq, report_path)
    print_summary(stats)

    log.info("Done. Output in %s", out_dir)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Shield Maxer data preparation pipeline")
    p.add_argument("--out", default="data/processed", help="Output directory")
    p.add_argument("--max-per-source", type=int, default=None, help="Limit rows per source (for quick test)")
    p.add_argument("--include-gated", action="store_true", help="Include gated datasets (needs HF_TOKEN)")
    p.add_argument("--include-nc", action="store_true", help="Include CC-BY-NC datasets (non-commercial only)")
    p.add_argument("--train-ratio", type=float, default=0.8)
    p.add_argument("--val-ratio", type=float, default=0.1)
    p.add_argument("--test-ratio", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--list-sources", action="store_true", help="List available sources and exit")

    args = p.parse_args(argv)

    if args.list_sources:
        for name, desc in list_adapters():
            print(f"  {name:<25} {desc}")
        return 0

    ratios = (args.train_ratio, args.val_ratio, args.test_ratio)
    if abs(sum(ratios) - 1.0) > 1e-9:
        p.error("ratios must sum to 1.0")

    build(
        Path(args.out),
        max_per_source=args.max_per_source,
        include_gated=args.include_gated,
        include_nc=args.include_nc,
        ratios=ratios,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())