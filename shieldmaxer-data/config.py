"""
ShieldMaxer Data Pipeline – Central Configuration
==================================================
All dataset identifiers, target languages, label schema, and
composition ratios live here. Edit this file; the scripts stay clean.
"""

from pathlib import Path

ROOT = Path(__file__).parent.resolve()
RAW = ROOT / "raw"
PROCESSED = ROOT / "processed"
COMPOSED = ROOT / "composed"
BENCHMARKS = ROOT / "benchmarks"
TEACHER = ROOT / "teacher_labeled"
LOGS = ROOT / "logs"

# ---------------------------------------------------------------------------
# Target languages (ISO 639-1 / common HF codes)
# ---------------------------------------------------------------------------
INDIC_LANGS = ["hi", "bn", "gu", "mr", "pa", "ta", "te", "kn", "ml", "ur"]
ALL_LANGS = INDIC_LANGS + ["en"]

# ---------------------------------------------------------------------------
# Unified label schema  (align with AEGIS 2.0 + WildGuard 3-head)
# ---------------------------------------------------------------------------
LABEL_SCHEMA = {
    "decision": ["safe", "unsafe"],          # primary binary head
    "risk_categories": [                      # multi-label
        "violence",
        "hate_speech",
        "sexual_explicit",
        "self_harm",
        "misinformation",
        "privacy_pii",
        "cyberattack",
        "caste_communal",        # Indic-specific
        "jailbreak_attempt",
        "prompt_injection",
        "other",
        "none",
    ],
    "jailbreak_detected": [True, False],
    "romanized": [True, False],              # Hinglish / code-mixed flag
    "reason_code": [                          # structured rationale token
        "RC00_SAFE",
        "RC01_VIOLENCE",
        "RC02_HATE",
        "RC03_SEXUAL",
        "RC04_SELF_HARM",
        "RC05_MISINFO",
        "RC06_PRIVACY",
        "RC07_CYBER",
        "RC08_CASTE",
        "RC09_JAILBREAK",
        "RC10_INJECTION",
        "RC11_OVERBLOCKED",    # false-positive flag
        "RC12_OTHER",
    ],
}

# ---------------------------------------------------------------------------
# Tier 0 – Core training datasets
# ---------------------------------------------------------------------------
TIER0_DATASETS = {
    "indicguard": {
        "hf_id": "l3cube-pune/IndicGuard",
        "license": "CC-BY-4.0",
        "langs": INDIC_LANGS + ["en"],
        "label_cols": ["prompt_label", "violated_categories"],
        "train_budget": 135_000,   # ~45% of 300k target
        "split": "train",
    },
    "nemotron_v3": {
        "hf_id": "nvidia/Nemotron-Safety-Guard-Dataset-v3",
        "license": "CC-BY-4.0",
        "langs": ["en", "hi"],
        "label_cols": ["label", "category"],
        "train_budget": 45_000,    # ~15%
        "split": "train",
    },
    "polyguard_mix": {
        "hf_id": "ToxicityPrompts/PolyGuardMix",
        "license": "CC-BY-4.0",
        "langs": ["hi", "en"],
        "label_cols": ["prompt_harm", "response_harm", "refusal"],
        "train_budget": 45_000,    # ~15%
        "split": "train",
    },
    "aya_redteaming": {
        "hf_id": "CohereLabs/aya_redteaming",
        "license": "Apache-2.0",
        "langs": ["hi"],
        "label_cols": ["global_or_local", "literal_translation"],
        "train_budget": 8_000,
        "split": "train",
    },
    "aegis_2": {
        "hf_id": "nvidia/Aegis-AI-Content-Safety-Dataset-2.0",
        "license": "CC-BY-4.0",
        "langs": ["en"],
        "label_cols": ["label", "category"],
        "train_budget": 10_000,
        "split": "train",
    },
    "wildguardmix": {
        "hf_id": "allenai/wildguardmix",
        "license": "ODC-BY",
        "langs": ["en"],
        "label_cols": ["prompt_harm_label", "response_harm_label", "refusal_label"],
        "train_budget": 10_000,
        "split": "train",
        "gated": True,
    },
    "salad_data": {
        "hf_id": "OpenSafetyLab/Salad-Data",
        "license": "Apache-2.0",
        "langs": ["en"],
        "label_cols": ["category", "sub_category"],
        "train_budget": 7_000,
        "split": "train",
    },
}

# ---------------------------------------------------------------------------
# Tier 1 – Jailbreak & prompt injection
# ---------------------------------------------------------------------------
TIER1_DATASETS = {
    "in_the_wild_jailbreaks": {
        "hf_id": "TrustAIRLab/in-the-wild-jailbreak-prompts",
        "license": "MIT",
        "train_budget": 5_000,
    },
    "multijail": {
        "hf_id": "DAMO-NLP-SG/MultiJail",
        "license": "MIT",
        "langs": ["hi", "bn"],
        "train_budget": 2_000,
    },
    "harmbench": {
        "hf_id": "walledai/HarmBench",
        "license": "MIT",
        "train_budget": 1_200,
        "gated": True,
    },
    "strongreject": {
        "hf_id": "walledai/StrongREJECT",
        "license": "MIT",
        "train_budget": 313,
        "gated": True,
    },
    "hackaprompt": {
        "hf_id": "hackaprompt/hackaprompt-dataset",
        "license": "MIT",
        "train_budget": 3_000,
    },
    "guard_reasoner": {
        "hf_id": "yueliu1999/GuardReasonerTrain",
        "license": "MIT",
        "train_budget": 5_000,
    },
}

# ---------------------------------------------------------------------------
# Tier 2 – Benign / hard negatives (over-refusal fix)
# ---------------------------------------------------------------------------
TIER2_DATASETS = {
    "xstest": {
        "hf_id": "walledai/XSTest",
        "license": "CC-BY-4.0",
        "train_budget": 250,
        "gated": True,
    },
    "or_bench": {
        "hf_id": "bench-llm/or-bench",
        "license": "CC-BY-4.0",
        "train_budget": 10_000,
    },
    "indic_instruct": {
        "hf_id": "ai4bharat/indic-instruct-data-v0.1",
        "license": "CC-BY-4.0",
        "langs": INDIC_LANGS,
        "train_budget": 8_000,
    },
    "samvaad_hi": {
        "hf_id": "sarvamai/samvaad-hi-v1",
        "license": "Apache-2.0",
        "langs": ["hi"],
        "train_budget": 5_000,
    },
    "oasst2": {
        "hf_id": "OpenAssistant/oasst2",
        "license": "Apache-2.0",
        "langs": ["en", "bn"],
        "train_budget": 5_000,
    },
}

# ---------------------------------------------------------------------------
# Tier 3 – Encoder adaptation (MLM corpus, not safety-labelled)
# ---------------------------------------------------------------------------
TIER3_DATASETS = {
    "sangraha": {
        "hf_id": "ai4bharat/sangraha",
        "license": "CC-BY-4.0",
        "langs": INDIC_LANGS,
        "role": "continued_mlm",
    },
    "bhasha_abhijnaanam": {
        "hf_id": "ai4bharat/Bhasha-Abhijnaanam",
        "license": "CC0-1.0",
        "role": "language_id",
    },
}

# ---------------------------------------------------------------------------
# Benchmarks (eval only – NEVER in training mix)
# ---------------------------------------------------------------------------
BENCHMARK_DATASETS = {
    "polyguard_prompts": {
        "hf_id": "ToxicityPrompts/PolyGuardPrompts",
        "license": "CC-BY-4.0",
        "note": "Held-out 29k human-verified benchmark",
    },
    "jbb_behaviors": {
        "hf_id": "JailbreakBench/JBB-Behaviors",
        "license": "MIT",
    },
    "multijail_bench": {
        "hf_id": "DAMO-NLP-SG/MultiJail",
        "license": "MIT",
    },
}

# ---------------------------------------------------------------------------
# Final composition targets (~300k rows total)
# ---------------------------------------------------------------------------
COMPOSITION = {
    "indicguard":           0.45,   # 135k
    "nemotron_aegis":       0.15,   #  45k
    "polyguard_mix":        0.15,   #  45k
    "teacher_romanized":    0.10,   #  30k
    "benign_hard_neg":      0.10,   #  30k
    "jailbreak_injection":  0.05,   #  15k
}
TOTAL_TARGET = 300_000

# ---------------------------------------------------------------------------
# Teacher labeling schema (JSON output spec)
# ---------------------------------------------------------------------------
TEACHER_OUTPUT_SCHEMA = {
    "decision": "str: safe|unsafe",
    "jev_score": "float 0.0-1.0 (jailbreak-evasion score)",
    "risk_categories": "list[str] from LABEL_SCHEMA['risk_categories']",
    "jailbreak_detected": "bool",
    "romanized": "bool",
    "reason_code": "str from LABEL_SCHEMA['reason_code']",
    "rationale_short": "str <=30 tokens, NO chain-of-thought, decision-visible only",
    "_meta": {
        "teacher_model": "str",
        "teacher_version": "str",
        "prompt_hash": "str sha256[:16]",
        "labeled_at": "ISO8601",
    },
}

# ---------------------------------------------------------------------------
# Sampling strata for teacher prompt pool (~50k total)
# ---------------------------------------------------------------------------
TEACHER_POOL_STRATA = {
    "benign":               0.60,   # 30k — real Indic/Hinglish benign
    "sensitive_benign":     0.15,   #  7.5k — medical, legal, journalism
    "harmful":              0.15,   #  7.5k — from red-team sources
    "jailbreak_attempt":    0.10,   #  5k — injection + jailbreak prompts
}
TEACHER_POOL_SIZE = 50_000

# ---------------------------------------------------------------------------
# Baselines to compare against
# ---------------------------------------------------------------------------
BASELINES = [
    "Qwen/Qwen3Guard-Gen-8B",
    "nvidia/NemoGuard-8B-ContentSafety",
    "meta-llama/Llama-Guard-3-8B",
    "meta-llama/Llama-Guard-4-12B",
    "google/shieldgemma-9b",
    "l3cube-pune/IndicGuard",   # fine-tuned checkpoint
]

