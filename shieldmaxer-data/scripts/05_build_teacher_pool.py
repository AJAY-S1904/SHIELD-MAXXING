"""
05_build_teacher_pool.py – Build stratified prompt pool for teacher labeling
=============================================================================
Assembles ~50k prompts across 4 strata for teacher model annotation:
  - benign          60% (30k) — real Indic/Hinglish benign prompts
  - sensitive_benign 15% (7.5k) — medical, legal, journalism seeds
  - harmful         15% (7.5k) — from red-team sources
  - jailbreak_attempt 10% (5k) — injection + jailbreak prompts

Also:
  - Flags potential Romanized/code-mixed text using heuristics
  - Writes pool.parquet + pool_manifest.json to teacher_labeled/

Usage:
    python scripts/05_build_teacher_pool.py [--size 50000] [--seed 42]
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1]))
from config import (
    PROCESSED, TEACHER, LOGS,
    TEACHER_POOL_SIZE, TEACHER_POOL_STRATA
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS / "05_build_teacher_pool.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Romanized / code-mixed heuristic detector
# Checks for Latin-script text that contains Hindi loanwords / particles
# ---------------------------------------------------------------------------
HINDI_PARTICLES = re.compile(
    r"\b(hai|hain|ho|hoga|kya|kyun|kyunki|nahi|nhi|mat|kar|karo|karna|"
    r"mera|meri|mujhe|tumhara|aap|yeh|woh|lekin|aur|ya|se|ko|ke|ki|ka|"
    r"bhi|sirf|ab|phir|toh|theek|accha|bilkul|zaroor|samajh|batao|dedo|"
    r"bol|sun|dekh|jao|ruko|lao|raha|rahi|gaya|gaye|chahiye)\b",
    re.IGNORECASE,
)
DEVANAGARI = re.compile(r"[\u0900-\u097F]")
LATIN_DOMINANT = re.compile(r"^[A-Za-z0-9\s\.,!?'\"\-:;()\[\]@#%&*]+$")


def is_romanized(text: str) -> bool:
    """Return True if text is Romanized/Hinglish (Latin script, Hindi vocab)."""
    if DEVANAGARI.search(text):
        return False   # script-native, not romanized
    if not LATIN_DOMINANT.match(text.strip()):
        return False
    return bool(HINDI_PARTICLES.search(text))


# ---------------------------------------------------------------------------
# Sensitive-benign seed prompts (hand-authored, high-leverage gap)
# ---------------------------------------------------------------------------
SENSITIVE_BENIGN_SEEDS = [
    # Medical
    "मुझे बुखार है और सिरदर्द हो रहा है, क्या करूं?",
    "डायबिटीज के मरीज को कौन सी दवाएं नहीं लेनी चाहिए?",
    "बच्चे को टीका कब लगवाना चाहिए?",
    "क्या पेरासिटामोल और आइबूप्रोफेन एक साथ ले सकते हैं?",
    "गर्भावस्था में कौन से आहार से बचना चाहिए?",
    "What are the side effects of metformin in elderly patients?",
    "Is it safe to take antidepressants during pregnancy?",
    "My child has a rash after eating peanuts, what should I do?",
    "Can I stop taking blood pressure medication if I feel better?",
    "What is the difference between Type 1 and Type 2 diabetes?",
    # Legal
    "भारत में FIR दर्ज करने की प्रक्रिया क्या है?",
    "किरायेदार को कितने दिन पहले नोटिस देना होता है?",
    "बाल हिरासत के मामले में कानून क्या कहता है?",
    "POCSO act के तहत क्या प्रावधान हैं?",
    "What are my rights if I am arrested without a warrant?",
    "How do I file a consumer complaint in India?",
    "What constitutes wrongful termination under Indian labour law?",
    # Journalistic / research
    "भारत में सांप्रदायिक हिंसा की घटनाओं का इतिहास क्या है?",
    "What is the historical context of Partition violence in 1947?",
    "Can you explain the caste system and its impact on modern India?",
    "How does dowry-related violence get reported in rural India?",
    "What are the documented cases of police brutality in India?",
    # Academic / self-harm support
    "मैं बहुत उदास हूं और जीना नहीं चाहता, मुझे किससे बात करनी चाहिए?",
    "What helplines are available for suicide prevention in India?",
    "How do therapists handle disclosures of self-harm from minors?",
    "What is the difference between suicidal ideation and intent?",
    "How can a teacher support a student who is being bullied?",
    # Hindi variants
    "क्या मैं किसी को ब्लॉक करने के बाद उनसे बात कर सकता हूं?",
    "मेरे पड़ोसी बहुत शोर करते हैं, मैं कानूनी कार्रवाई कैसे करूं?",
    "बैंक खाते में अनधिकृत लेनदेन होने पर क्या करें?",
    # Bengali
    "আমার সন্তান স্কুলে বুলিং-এর শিকার হচ্ছে, আমার কী করা উচিত?",
    "ডায়াবেটিস রোগীর ডায়েট চার্ট কেমন হওয়া উচিত?",
    # Tamil
    "தற்கொலை தடுப்பு தொலைபேசி எண்கள் என்ன?",
    "குழந்தை தொழிலாளர் சட்டம் என்ன சொல்கிறது?",
]


def load_all_processed() -> pd.DataFrame:
    """Load all normalized parquet files from processed/ directory."""
    frames = []
    for p in sorted(Path(PROCESSED).rglob("normalized.parquet")):
        try:
            df = pd.read_parquet(p)
            df["_source_path"] = str(p)
            frames.append(df)
            log.info(f"  Loaded {p.relative_to(PROCESSED)}: {len(df):,} rows")
        except Exception as e:
            log.warning(f"  Could not load {p}: {e}")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def sample_stratum(df: pd.DataFrame, decision_filter: str | list, budget: int, seed: int) -> pd.DataFrame:
    if isinstance(decision_filter, str):
        mask = df["decision"] == decision_filter
    else:
        mask = df["decision"].isin(decision_filter)
    subset = df[mask].copy()
    n = min(budget, len(subset))
    if n == 0:
        return pd.DataFrame()
    return subset.sample(n=n, random_state=seed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=TEACHER_POOL_SIZE)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    TEACHER.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    log.info("Loading all processed datasets ...")
    all_data = load_all_processed()

    if all_data.empty:
        log.error("No processed data found. Run scripts 01-03 first.")
        sys.exit(1)

    # Tag Romanized prompts
    log.info("Detecting Romanized/code-mixed prompts ...")
    all_data["romanized"] = all_data["prompt"].apply(lambda x: is_romanized(str(x)))
    roman_count = all_data["romanized"].sum()
    log.info(f"  Detected {roman_count:,} Romanized/Hinglish prompts")

    strata_frames = []
    strata_stats = {}

    # --- Stratum 1: benign (60%) ---
    budget_benign = int(args.size * TEACHER_POOL_STRATA["benign"])
    log.info(f"\n[Stratum: benign] budget={budget_benign:,}")
    benign = sample_stratum(all_data, "safe", budget_benign, args.seed)
    benign["_stratum"] = "benign"
    strata_frames.append(benign)
    strata_stats["benign"] = len(benign)
    log.info(f"  Sampled {len(benign):,}")

    # --- Stratum 2: sensitive_benign (15%) ---
    budget_sens = int(args.size * TEACHER_POOL_STRATA["sensitive_benign"])
    log.info(f"\n[Stratum: sensitive_benign] budget={budget_sens:,}")
    # Use hand-authored seeds + oversample from benign
    seed_rows = []
    for i, text in enumerate(SENSITIVE_BENIGN_SEEDS):
        seed_rows.append({
            "id": f"seed_{i:04d}",
            "source": "hand_authored",
            "tier": -1,
            "language": "hi" if DEVANAGARI.search(text) else "en",
            "prompt": text,
            "response": "",
            "decision": "safe",
            "risk_categories": [],
            "jailbreak": False,
            "refusal": None,
            "romanized": is_romanized(text),
            "split": "train",
            "license": "CC0-1.0",
            "_raw_label": "safe",
            "_stratum": "sensitive_benign",
            "_source_path": "hand_authored",
        })
    seed_df = pd.DataFrame(seed_rows)
    # Pad with benign rows not already sampled
    remaining_safe = all_data[
        (all_data["decision"] == "safe") &
        (~all_data.index.isin(benign.index))
    ]
    pad_n = max(0, budget_sens - len(seed_df))
    pad_df = remaining_safe.sample(n=min(pad_n, len(remaining_safe)), random_state=args.seed)
    pad_df["_stratum"] = "sensitive_benign"
    sens_benign = pd.concat([seed_df, pad_df], ignore_index=True)
    strata_frames.append(sens_benign)
    strata_stats["sensitive_benign"] = len(sens_benign)
    log.info(f"  Sampled {len(sens_benign):,} (seeds={len(seed_df)}, padded={len(pad_df)})")

    # --- Stratum 3: harmful (15%) ---
    budget_harm = int(args.size * TEACHER_POOL_STRATA["harmful"])
    log.info(f"\n[Stratum: harmful] budget={budget_harm:,}")
    harmful = sample_stratum(all_data, "unsafe", budget_harm, args.seed)
    harmful["_stratum"] = "harmful"
    strata_frames.append(harmful)
    strata_stats["harmful"] = len(harmful)
    log.info(f"  Sampled {len(harmful):,}")

    # --- Stratum 4: jailbreak_attempt (10%) ---
    budget_jb = int(args.size * TEACHER_POOL_STRATA["jailbreak_attempt"])
    log.info(f"\n[Stratum: jailbreak_attempt] budget={budget_jb:,}")
    jb = all_data[all_data["jailbreak"] == True].copy()
    n_jb = min(budget_jb, len(jb))
    jb = jb.sample(n=n_jb, random_state=args.seed) if n_jb > 0 else pd.DataFrame()
    if not jb.empty:
        jb["_stratum"] = "jailbreak_attempt"
    strata_frames.append(jb)
    strata_stats["jailbreak_attempt"] = len(jb)
    log.info(f"  Sampled {len(jb):,}")

    # Combine
    pool = pd.concat([f for f in strata_frames if not f.empty], ignore_index=True)
    pool = pool.drop_duplicates(subset=["prompt"]).reset_index(drop=True)
    log.info(f"\nPool total (after dedup): {len(pool):,}")

    # Add placeholder teacher columns (to be filled by teacher model)
    pool["teacher_decision"] = None
    pool["teacher_jev_score"] = None
    pool["teacher_risk_categories"] = None
    pool["teacher_jailbreak_detected"] = None
    pool["teacher_reason_code"] = None
    pool["teacher_rationale_short"] = None
    pool["teacher_model"] = None
    pool["teacher_version"] = None
    pool["teacher_labeled_at"] = None
    pool["human_reviewed"] = False

    # Save
    pool_path = TEACHER / "pool.parquet"
    pool.to_parquet(str(pool_path), index=False)
    log.info(f"Pool saved → {pool_path}")

    manifest = {
        "created_at": datetime.utcnow().isoformat(),
        "seed": args.seed,
        "target_size": args.size,
        "actual_size": len(pool),
        "strata": strata_stats,
        "romanized_count": int(pool["romanized"].sum()) if "romanized" in pool.columns else 0,
        "language_dist": pool["language"].value_counts().to_dict() if "language" in pool.columns else {},
        "source_dist": pool["source"].value_counts().to_dict() if "source" in pool.columns else {},
    }
    with open(TEACHER / "pool_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    log.info(f"Manifest saved → {TEACHER / 'pool_manifest.json'}")


if __name__ == "__main__":
    main()

