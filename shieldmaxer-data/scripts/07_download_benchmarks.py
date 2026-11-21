"""
07_download_benchmarks.py – Download held-out evaluation benchmarks
====================================================================
Downloads EVAL-ONLY datasets to benchmarks/.
These are NEVER touched by the training pipeline.

Usage:
    python scripts/07_download_benchmarks.py [--dry-run]
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from config import BENCHMARK_DATASETS, TIER1_DATASETS, BENCHMARKS, LOGS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS / "07_download_benchmarks.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)

# Additional eval sets not in BENCHMARK_DATASETS config
EXTRA_EVAL = {
    "xstest_eval": {
        "hf_id": "walledai/XSTest",
        "license": "CC-BY-4.0",
        "note": "250 safe-but-scary prompts for over-refusal eval",
        "gated": True,
    },
    "jbb_behaviors": {
        "hf_id": "JailbreakBench/JBB-Behaviors",
        "license": "MIT",
        "note": "100 behaviors × matched benign",
    },
    "multijail_eval": {
        "hf_id": "DAMO-NLP-SG/MultiJail",
        "license": "MIT",
        "note": "3k jailbreaks across 10 langs",
    },
}


def download_eval(key: str, hf_id: str, cfg: dict, out_base: Path, dry_run: bool) -> dict:
    out_dir = out_base / key
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "key": key,
        "hf_id": hf_id,
        "note": cfg.get("note", ""),
        "license": cfg.get("license", "unknown"),
        "downloaded_at": datetime.utcnow().isoformat(),
        "status": "pending",
        "row_counts": {},
    }

    if dry_run:
        log.info(f"[DRY-RUN] Would download {hf_id}")
        result["status"] = "dry_run"
        return result

    try:
        from datasets import load_dataset, DownloadConfig
        dl_cfg = DownloadConfig(resume_download=True, num_proc=4)
        log.info(f"Downloading benchmark: {hf_id} ...")
        t0 = time.time()
        try:
            ds = load_dataset(hf_id, download_config=dl_cfg)
        except Exception:
            ds = load_dataset(hf_id, split="test", download_config=dl_cfg)
            ds = {"test": ds}

        for sp, dset in (ds.items() if hasattr(ds, "items") else {"test": ds}.items()):
            p = out_dir / f"{sp}.parquet"
            dset.to_parquet(str(p))
            result["row_counts"][sp] = len(dset)
            log.info(f"  {sp}: {len(dset):,} rows → {p.name}")

        result["out_dir"] = str(out_dir)
        result["status"] = "ok"
        log.info(f"  Done in {time.time()-t0:.1f}s")

    except Exception as e:
        log.error(f"  FAILED {hf_id}: {e}")
        result["status"] = f"error: {e}"

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    BENCHMARKS.mkdir(parents=True, exist_ok=True)
    manifest_path = BENCHMARKS / "benchmark_manifest.json"
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    all_evals = {**BENCHMARK_DATASETS, **EXTRA_EVAL}

    for key, cfg in all_evals.items():
        if key in manifest and manifest[key].get("status") == "ok" and not args.dry_run:
            log.info(f"Skipping {key} (already downloaded)")
            continue
        hf_id = cfg["hf_id"]
        result = download_eval(key, hf_id, cfg, BENCHMARKS, args.dry_run)
        manifest[key] = result

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    log.info(f"Benchmark manifest → {manifest_path}")


if __name__ == "__main__":
    main()

