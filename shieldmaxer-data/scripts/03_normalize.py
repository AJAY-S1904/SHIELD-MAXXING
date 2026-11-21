"""
03_normalize.py – Normalize all downloaded datasets into a unified schema
=========================================================================
Reads parquet files from raw/, maps source-specific columns to the
ShieldMaxer canonical schema, and writes normalized parquet to processed/.

Canonical row:
{
  "id":               str (sha256[:16] of source+split+index),
  "source":           str (dataset key),
  "tier":             int (0|1|2),
  "language":         str (ISO 639-1),
  "prompt":           str,
  "response":         str | None,
  "decision":         str ("safe" | "unsafe" | "unknown"),
  "risk_categories":  list[str],
  "jailbreak":        bool,
  "refusal":          bool | None,
  "romanized":        bool,
  "split":            str ("train" | "test" | "val"),
  "license":          str,
  "_raw_label":       str  (original label for audit trail),
}

Usage:
    python scripts/03_normalize.py [--tier 0|1|2] [--dataset <key>]
"""

import hashlib
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1]))
from config import (
    TIER0_DATASETS, TIER1_DATASETS, TIER2_DATASETS,
    RAW, PROCESSED, LOGS
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS / "03_normalize.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)


def make_id(source: str, split: str, idx: int) -> str:
    raw = f"{source}::{split}::{idx}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def safe_str(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


# ---------------------------------------------------------------------------
# Per-source mappers  (add new ones as sources grow)
# ---------------------------------------------------------------------------

def map_indicguard(df: pd.DataFrame, split: str) -> pd.DataFrame:
    """l3cube-pune/IndicGuard"""
    rows = []
    for i, r in df.iterrows():
        label = safe_str(r.get("prompt_label", "")).lower()
        decision = "unsafe" if label in ("1", "unsafe", "harmful", "yes") else "safe"
        cats = []
        vc = r.get("violated_categories", "")
        if vc and str(vc) not in ("nan", "None", ""):
            cats = [c.strip() for c in str(vc).split(",") if c.strip()]
        rows.append({
            "id": make_id("indicguard", split, i),
            "source": "indicguard",
            "tier": 0,
            "language": safe_str(r.get("language", r.get("lang", "hi"))),
            "prompt": safe_str(r.get("prompt", r.get("text", ""))),
            "response": safe_str(r.get("response", "")),
            "decision": decision,
            "risk_categories": cats,
            "jailbreak": "jailbreak" in cats,
            "refusal": None,
            "romanized": False,
            "split": split,
            "license": "CC-BY-4.0",
            "_raw_label": safe_str(r.get("prompt_label", "")),
        })
    return pd.DataFrame(rows)


def map_nemotron(df: pd.DataFrame, split: str) -> pd.DataFrame:
    """nvidia/Nemotron-Safety-Guard-Dataset-v3"""
    rows = []
    for i, r in df.iterrows():
        label = safe_str(r.get("label", "")).lower()
        decision = "safe" if label in ("safe", "0") else "unsafe"
        cats = []
        cat = safe_str(r.get("category", ""))
        if cat and cat not in ("nan", "none", ""):
            cats = [cat]
        rows.append({
            "id": make_id("nemotron_v3", split, i),
            "source": "nemotron_v3",
            "tier": 0,
            "language": safe_str(r.get("language", r.get("lang", "en"))),
            "prompt": safe_str(r.get("prompt", r.get("text", ""))),
            "response": safe_str(r.get("response", "")),
            "decision": decision,
            "risk_categories": cats,
            "jailbreak": False,
            "refusal": None,
            "romanized": False,
            "split": split,
            "license": "CC-BY-4.0",
            "_raw_label": label,
        })
    return pd.DataFrame(rows)


def map_polyguard(df: pd.DataFrame, split: str) -> pd.DataFrame:
    """ToxicityPrompts/PolyGuardMix"""
    rows = []
    for i, r in df.iterrows():
        ph = safe_str(r.get("prompt_harm", "0"))
        decision = "unsafe" if ph in ("1", "true", "True", "harmful") else "safe"
        cats = []
        cat = safe_str(r.get("category", ""))
        if cat and cat not in ("nan", "none", ""):
            cats = [cat]
        refusal_val = r.get("refusal", None)
        refusal = None if refusal_val is None else bool(str(refusal_val) in ("1","True","true"))
        rows.append({
            "id": make_id("polyguard_mix", split, i),
            "source": "polyguard_mix",
            "tier": 0,
            "language": safe_str(r.get("language", r.get("lang", "en"))),
            "prompt": safe_str(r.get("prompt", r.get("text", ""))),
            "response": safe_str(r.get("response", "")),
            "decision": decision,
            "risk_categories": cats,
            "jailbreak": False,
            "refusal": refusal,
            "romanized": False,
            "split": split,
            "license": "CC-BY-4.0",
            "_raw_label": ph,
        })
    return pd.DataFrame(rows)


def map_aya_redteam(df: pd.DataFrame, split: str) -> pd.DataFrame:
    """CohereLabs/aya_redteaming"""
    rows = []
    for i, r in df.iterrows():
        cats = []
        gol = safe_str(r.get("global_or_local", ""))
        if gol:
            cats = [f"cultural_{gol}"]
        rows.append({
            "id": make_id("aya_redteaming", split, i),
            "source": "aya_redteaming",
            "tier": 0,
            "language": safe_str(r.get("language", r.get("lang", "hi"))),
            "prompt": safe_str(r.get("prompt", r.get("text", ""))),
            "response": "",
            "decision": "unsafe",   # all aya_redteaming rows are harmful by design
            "risk_categories": cats,
            "jailbreak": False,
            "refusal": None,
            "romanized": False,
            "split": split,
            "license": "Apache-2.0",
            "_raw_label": gol,
        })
    return pd.DataFrame(rows)


def map_aegis2(df: pd.DataFrame, split: str) -> pd.DataFrame:
    """nvidia/Aegis-AI-Content-Safety-Dataset-2.0"""
    rows = []
    for i, r in df.iterrows():
        label = safe_str(r.get("label", "safe")).lower()
        decision = "safe" if label in ("safe", "0") else "unsafe"
        cats = []
        cat = safe_str(r.get("category", ""))
        if cat and cat not in ("nan", "none", ""):
            cats = [cat]
        rows.append({
            "id": make_id("aegis_2", split, i),
            "source": "aegis_2",
            "tier": 0,
            "language": "en",
            "prompt": safe_str(r.get("prompt", r.get("text", ""))),
            "response": safe_str(r.get("response", "")),
            "decision": decision,
            "risk_categories": cats,
            "jailbreak": False,
            "refusal": None,
            "romanized": False,
            "split": split,
            "license": "CC-BY-4.0",
            "_raw_label": label,
        })
    return pd.DataFrame(rows)


def map_wildguard(df: pd.DataFrame, split: str) -> pd.DataFrame:
    """allenai/wildguardmix"""
    rows = []
    for i, r in df.iterrows():
        ph = safe_str(r.get("prompt_harm_label", "safe")).lower()
        decision = "unsafe" if "harm" in ph or ph == "1" else "safe"
        refusal_val = r.get("refusal_label", None)
        refusal = None if refusal_val is None else str(refusal_val).lower() in ("1","true","refusal")
        rows.append({
            "id": make_id("wildguardmix", split, i),
            "source": "wildguardmix",
            "tier": 0,
            "language": "en",
            "prompt": safe_str(r.get("prompt", "")),
            "response": safe_str(r.get("response", "")),
            "decision": decision,
            "risk_categories": [],
            "jailbreak": False,
            "refusal": refusal,
            "romanized": False,
            "split": split,
            "license": "ODC-BY",
            "_raw_label": ph,
        })
    return pd.DataFrame(rows)


def map_salad(df: pd.DataFrame, split: str) -> pd.DataFrame:
    """OpenSafetyLab/Salad-Data"""
    rows = []
    for i, r in df.iterrows():
        cats = []
        for col in ("category", "sub_category"):
            v = safe_str(r.get(col, ""))
            if v and v not in ("nan", "none", ""):
                cats.append(v)
        rows.append({
            "id": make_id("salad_data", split, i),
            "source": "salad_data",
            "tier": 0,
            "language": "en",
            "prompt": safe_str(r.get("prompt", r.get("augq", r.get("question", "")))),
            "response": "",
            "decision": "unsafe",
            "risk_categories": cats,
            "jailbreak": "jailbreak" in " ".join(cats).lower(),
            "refusal": None,
            "romanized": False,
            "split": split,
            "license": "Apache-2.0",
            "_raw_label": cats[0] if cats else "",
        })
    return pd.DataFrame(rows)


def map_generic_harmful(df: pd.DataFrame, split: str, source: str, tier: int, license: str) -> pd.DataFrame:
    """Fallback mapper for jailbreak / injection datasets (Tier 1)."""
    prompt_col = next((c for c in ["prompt", "text", "goal", "question", "instruction"] if c in df.columns), df.columns[0])
    rows = []
    for i, r in df.iterrows():
        rows.append({
            "id": make_id(source, split, i),
            "source": source,
            "tier": tier,
            "language": safe_str(r.get("language", r.get("lang", "en"))),
            "prompt": safe_str(r[prompt_col]),
            "response": safe_str(r.get("response", r.get("output", ""))),
            "decision": "unsafe",
            "risk_categories": ["jailbreak_attempt"],
            "jailbreak": True,
            "refusal": None,
            "romanized": False,
            "split": split,
            "license": license,
            "_raw_label": "jailbreak",
        })
    return pd.DataFrame(rows)


def map_generic_benign(df: pd.DataFrame, split: str, source: str, license: str) -> pd.DataFrame:
    """Fallback mapper for benign / over-refusal datasets (Tier 2)."""
    prompt_col = next((c for c in ["prompt", "text", "question", "instruction", "input"] if c in df.columns), df.columns[0])
    rows = []
    for i, r in df.iterrows():
        rows.append({
            "id": make_id(source, split, i),
            "source": source,
            "tier": 2,
            "language": safe_str(r.get("language", r.get("lang", "en"))),
            "prompt": safe_str(r[prompt_col]),
            "response": safe_str(r.get("response", r.get("output", r.get("assistant", "")))),
            "decision": "safe",
            "risk_categories": [],
            "jailbreak": False,
            "refusal": None,
            "romanized": False,
            "split": split,
            "license": license,
            "_raw_label": "safe",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Source → mapper routing table
# ---------------------------------------------------------------------------
MAPPER_REGISTRY = {
    "indicguard":      (0, map_indicguard),
    "nemotron_v3":     (0, map_nemotron),
    "polyguard_mix":   (0, map_polyguard),
    "aya_redteaming":  (0, map_aya_redteam),
    "aegis_2":         (0, map_aegis2),
    "wildguardmix":    (0, map_wildguard),
    "salad_data":      (0, map_salad),
}


def normalize_source(key: str, tier: int, cfg: dict):
    tier_dir = RAW / f"tier{tier}" / key
    out_dir = PROCESSED / f"tier{tier}" / key
    out_dir.mkdir(parents=True, exist_ok=True)

    parquet_files = sorted(tier_dir.glob("*.parquet"))
    if not parquet_files:
        log.warning(f"  No parquet files found in {tier_dir} — skipping")
        return

    all_frames = []
    for pf in parquet_files:
        split_name = pf.stem
        log.info(f"  Reading {pf.name} ...")
        df = pd.read_parquet(pf)
        log.info(f"    {len(df):,} rows, columns: {list(df.columns)}")

        # Route to mapper
        if key in MAPPER_REGISTRY:
            _, mapper_fn = MAPPER_REGISTRY[key]
            mapped = mapper_fn(df, split_name)
        elif tier == 1:
            mapped = map_generic_harmful(df, split_name, key, tier, cfg.get("license", "unknown"))
        elif tier == 2:
            mapped = map_generic_benign(df, split_name, key, cfg.get("license", "unknown"))
        else:
            log.warning(f"  No mapper for {key} — skipping")
            continue

        all_frames.append(mapped)

    if not all_frames:
        return

    combined = pd.concat(all_frames, ignore_index=True)
    # Deduplicate by prompt text
    before = len(combined)
    combined = combined.drop_duplicates(subset=["prompt"]).reset_index(drop=True)
    after = len(combined)
    log.info(f"  Deduplication: {before:,} → {after:,} rows ({before - after:,} removed)")

    out_path = out_dir / "normalized.parquet"
    combined.to_parquet(str(out_path), index=False)
    log.info(f"  Saved → {out_path} ({after:,} rows)")

    # Print label distribution
    dist = combined["decision"].value_counts()
    log.info(f"  Label distribution:\n{dist.to_string()}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", type=int, choices=[0, 1, 2], default=None)
    parser.add_argument("--dataset", type=str, default=None)
    args = parser.parse_args()

    tier_map = {
        0: TIER0_DATASETS,
        1: TIER1_DATASETS,
        2: TIER2_DATASETS,
    }

    tiers_to_run = [args.tier] if args.tier is not None else [0, 1, 2]

    for tier_id in tiers_to_run:
        datasets = tier_map[tier_id]
        log.info(f"=== Normalizing Tier {tier_id} ===")
        for key, cfg in datasets.items():
            if args.dataset and key != args.dataset:
                continue
            log.info(f"Processing: {key} ({cfg['hf_id']})")
            normalize_source(key, tier_id, cfg)

    log.info("Normalization complete.")


if __name__ == "__main__":
    main()

