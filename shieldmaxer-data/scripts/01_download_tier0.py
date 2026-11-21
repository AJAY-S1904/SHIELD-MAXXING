"""
01_download_tier0.py – Download & cache Tier 0 (core training) datasets
========================================================================
Run from d:\HACKATHON\shieldmaxer-data\

Usage:
    python scripts/01_download_tier0.py [--dry-run] [--dataset <key>]

For gated datasets (wildguardmix) you must have already run:
    huggingface-cli login
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from config import TIER0_DATASETS, RAW, LOGS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS / "01_download_tier0.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)

MANIFEST_PATH = RAW / "tier0_manifest.json"


def load_manifest():
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    return {}


def save_manifest(m):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(m, f, indent=2)


def download_dataset(key: str, cfg: dict, dry_run: bool) -> dict:
    from datasets import load_dataset, DownloadConfig

    hf_id = cfg["hf_id"]
    out_dir = RAW / "tier0" / key
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "key": key,
        "hf_id": hf_id,
        "license": cfg["license"],
        "gated": cfg.get("gated", False),
        "downloaded_at": datetime.utcnow().isoformat(),
        "status": "pending",
        "row_counts": {},
    }

    if dry_run:
        log.info(f"[DRY-RUN] Would download {hf_id} → {out_dir}")
        result["status"] = "dry_run"
        return result

    try:
        log.info(f"Downloading {hf_id} ...")
        t0 = time.time()

        dl_cfg = DownloadConfig(resume_download=True, num_proc=4)

        # Try loading specific split first; fall back to all splits
        split = cfg.get("split", "train")
        try:
            ds = load_dataset(hf_id, split=split, download_config=dl_cfg)
            splits_loaded = {split: ds}
        except Exception:
            ds = load_dataset(hf_id, download_config=dl_cfg)
            splits_loaded = dict(ds)

        elapsed = time.time() - t0
        log.info(f"  Downloaded in {elapsed:.1f}s")

        for sp, dset in splits_loaded.items():
            parquet_path = out_dir / f"{sp}.parquet"
            dset.to_parquet(str(parquet_path))
            result["row_counts"][sp] = len(dset)
            log.info(f"  {sp}: {len(dset):,} rows → {parquet_path.name}")

        result["out_dir"] = str(out_dir)
        result["status"] = "ok"

    except Exception as e:
        log.error(f"  FAILED {hf_id}: {e}")
        result["status"] = f"error: {e}"

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dataset", help="Run only this key (e.g. indicguard)")
    args = parser.parse_args()

    manifest = load_manifest()
    datasets_to_run = (
        {args.dataset: TIER0_DATASETS[args.dataset]}
        if args.dataset
        else TIER0_DATASETS
    )

    for key, cfg in datasets_to_run.items():
        if key in manifest and manifest[key].get("status") == "ok" and not args.dry_run:
            log.info(f"Skipping {key} (already downloaded)")
            continue
        result = download_dataset(key, cfg, args.dry_run)
        manifest[key] = result
        save_manifest(manifest)

    log.info("Tier 0 download complete. Manifest saved to %s", MANIFEST_PATH)


if __name__ == "__main__":
    main()

