"""
02_download_tier1_tier2.py – Download Jailbreak + Benign datasets
=================================================================
Tier 1  = jailbreak / prompt-injection sources
Tier 2  = benign / hard-negative (over-refusal fix)

Usage:
    python scripts/02_download_tier1_tier2.py [--dry-run] [--tier 1|2]
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from config import TIER1_DATASETS, TIER2_DATASETS, RAW, LOGS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS / "02_download_tier1_tier2.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)


def download_tier(tier_id: int, datasets: dict, dry_run: bool):
    from datasets import load_dataset, DownloadConfig

    out_base = RAW / f"tier{tier_id}"
    manifest_path = RAW / f"tier{tier_id}_manifest.json"

    manifest = {}
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    for key, cfg in datasets.items():
        if key in manifest and manifest[key].get("status") == "ok" and not dry_run:
            log.info(f"Skipping {key} (already done)")
            continue

        hf_id = cfg["hf_id"]
        out_dir = out_base / key
        out_dir.mkdir(parents=True, exist_ok=True)

        result = {
            "key": key,
            "hf_id": hf_id,
            "license": cfg.get("license", "unknown"),
            "gated": cfg.get("gated", False),
            "downloaded_at": datetime.utcnow().isoformat(),
            "status": "pending",
            "row_counts": {},
        }

        if dry_run:
            log.info(f"[DRY-RUN] Would download {hf_id}")
            result["status"] = "dry_run"
            manifest[key] = result
            continue

        try:
            log.info(f"Downloading {hf_id} ...")
            t0 = time.time()
            dl_cfg = DownloadConfig(resume_download=True, num_proc=4)
            try:
                ds = load_dataset(hf_id, split="train", download_config=dl_cfg)
                splits = {"train": ds}
            except Exception:
                ds = load_dataset(hf_id, download_config=dl_cfg)
                splits = dict(ds)

            elapsed = time.time() - t0
            log.info(f"  Downloaded in {elapsed:.1f}s")

            for sp, dset in splits.items():
                p = out_dir / f"{sp}.parquet"
                dset.to_parquet(str(p))
                result["row_counts"][sp] = len(dset)
                log.info(f"  {sp}: {len(dset):,} rows → {p.name}")

            result["out_dir"] = str(out_dir)
            result["status"] = "ok"

        except Exception as e:
            log.error(f"  FAILED {hf_id}: {e}")
            result["status"] = f"error: {e}"

        manifest[key] = result

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    log.info(f"Tier {tier_id} manifest saved → {manifest_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tier", type=int, choices=[1, 2], default=None)
    args = parser.parse_args()

    if args.tier in (None, 1):
        log.info("=== TIER 1 — Jailbreak / Prompt Injection ===")
        download_tier(1, TIER1_DATASETS, args.dry_run)

    if args.tier in (None, 2):
        log.info("=== TIER 2 — Benign / Hard Negatives ===")
        download_tier(2, TIER2_DATASETS, args.dry_run)


if __name__ == "__main__":
    main()

