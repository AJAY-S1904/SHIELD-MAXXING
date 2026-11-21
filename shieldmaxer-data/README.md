# Shield Maxer Data Pipeline

Prepares the training / validation / test splits for **Shield Maxer** — an
Indic-language-aware safety middleware (prompt risk / jailbreak classifier).

## What it does

1. **Pulls** from 11 public safety datasets (Tier 0 + Tier 1) covering:
   - 11 Indian languages (IndicGuard, Nemotron v3, Aya Red-teaming)
   - 9-way parallel jailbreak translations (MultiJail, Bengali included)
   - Prompt injection, jailbreak, benign-over-refusal, hard adversarial sets
2. **Normalises** every row onto one canonical schema with:
   - Label: `safe | unsafe | ambiguous`
   - Harm categories (16 incl. Indian-specific: `caste`, `communal`, `regional`)
   - Script detection: `native | latin | mixed` (auto-detected)
   - Romanized / code-mixed flags
   - Full provenance (source, license, translation group)
3. **Deduplicates**:
   - Exact text (normalised)
   - Near-duplicate via MinHash LSH (Jaccard ≥ 0.8)
   - Explicit translation groups (`parent_id`)
4. **Splits** at **group level** (80/10/10 by default) so no paraphrase of the
   same seed leaks across splits.
5. **Reports** JSON + console summary with label/language/script/category/license breakdowns.

## Install

```bash
pip install -r requirements.txt
# datasketch is needed for near-dup dedupe
pip install datasketch
```

## Quick start

```bash
# dry run on 1k rows per source (fast, no HF_TOKEN needed)
python -m shieldmaxer_data --max-per-source 1000 --out data/processed

# full run (Tier 0 + 1, public only)
python -m shieldmaxer_data --out data/processed

# include gated sets (wildguardmix, XSTest, HarmBench, StrongREJECT, etc.)
export HF_TOKEN=hf_xxx
python -m shieldmaxer_data --include-gated --out data/processed

# include CC-BY-NC sets (BeaverTails, Indic-Safety-Eval) — NON-COMMERCIAL ONLY
python -m shieldmaxer_data --include-nc --out data/processed
```

## Output structure

```
data/processed/
├── train.jsonl
├── val.jsonl
├── test.jsonl
├── split_stats.json     # per-split label/language/script/category counts
├── report.json          # global stats + license audit
└── manifest.json        # schema_version, counts, total_groups
```

Each `.jsonl` line is a `CanonicalRecord` — see `shieldmaxer_data/schema.py`.

## Available sources

Run `python -m shieldmaxer_data --list-sources` for the current list.

| Key | Dataset | Tier | License | Notes |
|-----|---------|------|---------|-------|
| `indicguard` | l3cube-pune/IndicGuard | 0 | CC-BY-4.0 | 11 Indic langs, 334k samples |
| `nemotron_v3` | nvidia/Nemotron-Safety-Guard-Dataset-v3 | 0 | CC-BY-4.0 | 12 langs incl. Hindi |
| `aegis_2` | nvidia/Aegis-AI-Content-Safety-Dataset-2.0 | 0 | CC-BY-4.0 | English refusal set |
| `aya_redteaming` | CohereLabs/aya_redteaming | 0 | Apache-2.0 | 8 langs incl. Hindi/Bengali/Tamil |
| `multijail` | DAMO-NLP-SG/MultiJail | 0 | MIT | 9-way parallel (Bengali!) |
| `salad_base` | OpenSafetyLab/Salad-Data base_set | 0 | Apache-2.0 | 21k seed prompts |
| `salad_attack` | OpenSafetyLab/Salad-Data attack_enhanced_set | 0 | Apache-2.0 | Jailbreak variants |
| `or_bench` | bench-llm/or-bench | 1 | CC-BY-4.0 | Benign + hard + toxic |
| `prompt_injections` | deepset/prompt-injections | 0 | Apache-2.0 | Prompt injection binary |
| `jbb_behaviors` | JailbreakBench/JBB-Behaviors | 1 | MIT | Harmful/benign pairs |
| `wild_jailbreak` | TrustAIRLab/in-the-wild-jailbreak-prompts | 1 | MIT | Real jailbreaks |
| **Gated** | wildguardmix, XSTest, HarmBench, StrongREJECT, lmsys-chat-1m, WildChat-1M | — | various | `--include-gated` + `HF_TOKEN` |
| **NC** | BeaverTails, anna-sarvam/indic-safety-eval | — | CC-BY-NC | `--include-nc` (non-comm only) |

## Canonical schema (key fields)

```python
record_id: str              # stable hash
text: str                   # normalised prompt
label: "safe" | "unsafe" | "ambiguous"
categories: list[str]       # from 16-key taxonomy
language: str | None        # ISO-639-1
script: "native" | "latin" | "mixed" | "unknown"
romanized: bool             # Hinglish-style Latin-script Indic
code_mixed: bool            # both native + Latin scripts
is_jailbreak: bool
is_benign_sensitive: bool   # over-refusal probes (OR-Bench)
template: str | None        # e.g. "multijail_translation", "salad_attack"
response: str | None        # optional, not used for prompt label
response_label: str | None
source_dataset: str
source_config: str | None
source_split: str | None
source_id: str | None
license: str | None
parent_id: str | None       # original English prompt id
group_id: str               # leakage-safe split key
text_hash: str              # normalised text hash
provenance: dict            # source-specific extras
tags: list[str]
```

## License compliance

- **Default run** (no flags): only permissive / commercial-friendly licences (CC-BY-4.0, Apache-2.0, MIT, ODC-BY).
- `--include-gated`: adds gated permissive sets (ODC-BY, MIT, CC-BY-4.0) — you must accept their HF terms.
- `--include-nc`: adds CC-BY-NC sets — **output cannot be used commercially**.

The `report.json` includes a per-licence count for audit trails.

## Extending

Add a new adapter in `sources.py` following the pattern:
```python
def iter_my_dataset(max_rows=None):
    ds = load_dataset(...)
    for row in ds:
        yield _mk_record(...)
```
Register in `ADAPTERS` dict with tier/license note.

## Requirements

- Python 3.11+
- `datasets`, `pyyaml`, `tqdm`, `datasketch`

## Related docs

- `Shield_Maxer_SRS.md` — JEV definition, data requirements (§7)
- `Shield_Maxer_PRD.md` — success metrics, overblocking risk
- `Shield_Maxer_Milestones.md` — Week 2 dataset milestone