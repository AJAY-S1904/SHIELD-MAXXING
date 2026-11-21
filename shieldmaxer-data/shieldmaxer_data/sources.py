"""Source adapters — each returns an iterable of CanonicalRecord.

Only *public / ungated* datasets are imported by default. Gated ones live behind
``--include-gated`` and require a valid ``HF_TOKEN``.

Every adapter:
* streams the HF dataset (no local disk copy)
* maps each row → CanonicalRecord
* fills provenance fields (source_dataset, source_id, license, group_id, ...)
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from itertools import islice
from typing import Iterable, Iterator

from datasets import load_dataset

from .schema import (
    CATEGORIES,
    CanonicalRecord,
    SCRIPTS,
    dedupe_preserve_order,
    normalize_text,
    stable_hash,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ROMANIZED_HINDI = re.compile(
    r"\b(?:hai|hoon|hun|kya|kaise|kahan|kab|kyun|kya|kaun|mujhe|mere|mera|aap|tum|hum|yeh|woh|kuch|kuchh|sab|abhi|kal|aaj|nahi|nahin|han|haan|acha|theek|sahi|galat|bura|accha|badiya|badhiya|khush|dukh|pyar|ishq|mohabbat|dost|yaar|bhai|behen|maa|papa|ghar|kaam|school|college|office|job|paisa|rupiya|time|din|raat|subah|shaam|raat|din|hafte|mahina|saal|din|raat)\b",
    re.IGNORECASE,
)


def _infer_script(text: str) -> str:
    """Return 'native' | 'latin' | 'mixed' | 'unknown' for a given text."""
    if not text:
        return "unknown"
    has_deva = any("\u0900" <= c <= "\u097f" for c in text)
    has_arab = any("\u0600" <= c <= "\u06ff" for c in text)
    has_beng = any("\u0980" <= c <= "\u09ff" for c in text)
    has_taml = any("\u0b80" <= c <= "\u0bff" for c in text)
    has_telu = any("\u0c00" <= c <= "\u0c7f" for c in text)
    has_knda = any("\u0c80" <= c <= "\u0cff" for c in text)
    has_mlym = any("\u0d00" <= c <= "\u0d7f" for c in text)
    has_gujr = any("\u0a80" <= c <= "\u0aff" for c in text)
    has_guru = any("\u0a00" <= c <= "\u0a7f" for c in text)
    has_oriy = any("\u0b00" <= c <= "\u0b7f" for c in text)
    has_tibt = any("\u0f00" <= c <= "\u0fff" for c in text)
    native = any(
        [
            has_deva,
            has_arab,
            has_beng,
            has_taml,
            has_telu,
            has_knda,
            has_mlym,
            has_gujr,
            has_guru,
            has_oriy,
            has_tibt,
        ]
    )
    ascii_letters = sum(1 for c in text if c.isalpha() and ord(c) < 128)
    latin = ascii_letters > len(text) * 0.3
    if native and latin:
        return "mixed"
    if native:
        return "native"
    if latin:
        return "latin"
    return "unknown"


def _infer_romanized(text: str) -> bool:
    """Heuristic: Hinglish word list hit + mostly ASCII letters."""
    if not text:
        return False
    ascii_frac = sum(1 for c in text if ord(c) < 128) / max(1, len(text))
    if ascii_frac < 0.7:
        return False
    return bool(_ROMANIZED_HINDI.search(text))


def _infer_code_mixed(text: str) -> bool:
    """True if both native Indic and Latin scripts appear."""
    return _infer_script(text) == "mixed"


def _norm_cat(raw: str | list[str] | None) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [s.strip() for s in re.split(r"[|,;/]", raw) if s.strip()]
    out = []
    for c in raw:
        cl = c.lower().replace(" ", "_").replace("-", "_")
        # map common synonyms → canonical keys
        for canon, desc in CATEGORIES.items():
            if canon in cl or canon.replace("_", " ") in cl or desc.lower() in cl.lower():
                out.append(canon)
                break
    return dedupe_preserve_order(out)


def _mk_record(
    *,
    text: str,
    label: str,
    categories: list[str],
    language: str | None,
    source_dataset: str,
    source_config: str | None = None,
    source_split: str | None = None,
    source_id: str | None = None,
    license_: str | None = None,
    is_jailbreak: bool = False,
    is_benign_sensitive: bool = False,
    template: str | None = None,
    response: str | None = None,
    response_label: str | None = None,
    parent_id: str | None = None,
    provenance: dict | None = None,
    tags: list[str] | None = None,
    _row_index: int | None = None,
) -> CanonicalRecord:
    script = _infer_script(text)
    romanized = _infer_romanized(text)
    code_mixed = _infer_code_mixed(text)
    # Unique ID: source + config + split + source_id + row_index + text prefix
    id_parts = [
        source_dataset,
        source_config or "",
        source_split or "",
        source_id or "",
        str(_row_index) if _row_index is not None else "",
        text[:60],
    ]
    rec = CanonicalRecord(
        record_id=stable_hash(*id_parts),
        text=normalize_text(text),
        label=label,
        categories=categories,
        language=language,
        script=script,
        romanized=romanized,
        code_mixed=code_mixed,
        is_jailbreak=is_jailbreak,
        is_benign_sensitive=is_benign_sensitive,
        template=template,
        response=normalize_text(response) if response else None,
        response_label=response_label,
        source_dataset=source_dataset,
        source_config=source_config,
        source_split=source_split,
        source_id=source_id,
        license=license_,
        parent_id=parent_id,
        provenance=provenance or {},
        tags=tags or [],
    )
    return rec


# ---------------------------------------------------------------------------
# Adapter implementations
# ---------------------------------------------------------------------------


def iter_indicguard(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """l3cube-pune/IndicGuard — 11 Indian languages, CC-BY-4.0."""
    ds = load_dataset("l3cube-pune/IndicGuard", "default", split="train", streaming=True)
    for i, row in enumerate(ds):
        if max_rows and i >= max_rows:
            break
        text = row.get("prompt") or ""
        label_raw = row.get("prompt_label", "ambiguous")
        label = "unsafe" if label_raw == "unsafe" else ("safe" if label_raw == "safe" else "ambiguous")
        cats = _norm_cat(row.get("violated_categories"))
        lang = row.get("language")
        yield _mk_record(
            text=text,
            label=label,
            categories=cats,
            language=lang.lower()[:2] if lang else None,
            source_dataset="l3cube-pune/IndicGuard",
            source_config="default",
            source_split="train",
            source_id=row.get("id"),
            license_="CC-BY-4.0",
            provenance={
                "prompt_label_source": row.get("prompt_label_source"),
                "tag": row.get("tag"),
                "reconstruction_id_if_redacted": row.get("reconstruction_id_if_redacted"),
            },
            tags=[row.get("tag", "")],
            _row_index=i,
        )


def iter_nemotron_v3(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """nvidia/Nemotron-Safety-Guard-Dataset-v3 — 12 langs incl. Hindi, CC-BY-4.0."""
    ds = load_dataset("nvidia/Nemotron-Safety-Guard-Dataset-v3", "default", split="train", streaming=True)
    for i, row in enumerate(ds):
        if max_rows and i >= max_rows:
            break
        text = row.get("prompt") or ""
        label_raw = row.get("prompt_label", "ambiguous")
        label = "unsafe" if label_raw == "unsafe" else ("safe" if label_raw == "safe" else "ambiguous")
        cats = _norm_cat(row.get("violated_categories"))
        lang = row.get("language")
        yield _mk_record(
            text=text,
            label=label,
            categories=cats,
            language=lang.lower()[:2] if lang else None,
            source_dataset="nvidia/Nemotron-Safety-Guard-Dataset-v3",
            source_config="default",
            source_split="train",
            source_id=row.get("id"),
            license_="CC-BY-4.0",
            provenance={"tag": row.get("tag"), "reconstruction_id_if_redacted": row.get("reconstruction_id_if_redacted")},
            tags=[row.get("tag", "")],
            _row_index=i,
        )


def iter_aegis_2(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """nvidia/Aegis-AI-Content-Safety-Dataset-2.0 — English, CC-BY-4.0."""
    ds = load_dataset("nvidia/Aegis-AI-Content-Safety-Dataset-2.0", "default", split="train", streaming=True)
    for i, row in enumerate(ds):
        if max_rows and i >= max_rows:
            break
        text = row.get("prompt") or ""
        label_raw = row.get("prompt_label", "ambiguous")
        label = "unsafe" if label_raw == "unsafe" else ("safe" if label_raw == "safe" else "ambiguous")
        cats = _norm_cat(row.get("violated_categories"))
        yield _mk_record(
            text=text,
            label=label,
            categories=cats,
            language="en",
            source_dataset="nvidia/Aegis-AI-Content-Safety-Dataset-2.0",
            source_config="default",
            source_split="train",
            source_id=row.get("id"),
            license_="CC-BY-4.0",
            provenance={"reconstruction_id_if_redacted": row.get("reconstruction_id_if_redacted")},
            response=row.get("response"),
            response_label=row.get("response_label"),
            _row_index=i,
        )


def iter_aya_redteaming(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """CohereLabs/aya_redteaming — 8 langs incl. Hindi, Apache-2.0."""
    # Configs are per-language splits
    for lang_code in ("hindi", "bengali", "tamil", "telugu", "marathi", "gujarati", "kannada", "malayalam"):
        try:
            ds = load_dataset("CohereLabs/aya_redteaming", "default", split=lang_code, streaming=True)
        except Exception:
            continue
        for i, row in enumerate(ds):
            if max_rows and i >= max_rows:
                break
            text = row.get("prompt") or ""
            cats_raw = row.get("harm_category")
            if isinstance(cats_raw, str):
                try:
                    cats_raw = json.loads(cats_raw)
                except Exception:
                    cats_raw = [cats_raw]
            cats = _norm_cat(cats_raw)
            lit = row.get("literal_translation")
            yield _mk_record(
                text=text,
                label="unsafe",
                categories=cats,
                language=lang_code[:2],
                source_dataset="CohereLabs/aya_redteaming",
                source_config="default",
                source_split=lang_code,
                source_id=row.get("prompt")[:40] if text else None,
                license_="Apache-2.0",
                provenance={
                    "global_or_local": row.get("global_or_local"),
                    "literal_translation": lit,
                    "semantic_translation": row.get("semantic_translation"),
                    "explanation": row.get("explanation"),
                },
                is_jailbreak=False,
                is_benign_sensitive=False,
                _row_index=i,
            )


def iter_multijail(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """DAMO-NLP-SG/MultiJail — 9 langs incl. Bengali, MIT."""
    ds = load_dataset("DAMO-NLP-SG/MultiJail", "default", split="train", streaming=True)
    lang_map = {
        "bn": "bn",
        "zh": "zh",
        "it": "it",
        "vi": "vi",
        "ar": "ar",
        "ko": "ko",
        "th": "th",
        "sw": "sw",
        "jv": "jv",
    }
    for i, row in enumerate(ds):
        if max_rows and i >= max_rows:
            break
        cats_raw = row.get("tags")
        if isinstance(cats_raw, str):
            try:
                cats_raw = json.loads(cats_raw)
            except Exception:
                cats_raw = [cats_raw]
        cats = _norm_cat(cats_raw)
        # Yield one record per language
        for j, (code, col) in enumerate(lang_map.items()):
            text = row.get(col) or ""
            if not text:
                continue
            yield _mk_record(
                text=text,
                label="unsafe",
                categories=cats,
                language=code,
                source_dataset="DAMO-NLP-SG/MultiJail",
                source_config="default",
                source_split="train",
                source_id=f"{row.get('id')}_{code}",
                license_="MIT",
                provenance={"source": row.get("source"), "tags_raw": row.get("tags")},
                parent_id=row.get("en"),
                template="multijail_translation",
                _row_index=i * 10 + j,
            )


def iter_salad_base(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """OpenSafetyLab/Salad-Data base_set — 21k seed prompts, Apache-2.0."""
    ds = load_dataset("OpenSafetyLab/Salad-Data", "base_set", split="train", streaming=True)
    for i, row in enumerate(ds):
        if max_rows and i >= max_rows:
            break
        text = row.get("question") or ""
        cat1 = row.get("1-category")
        cat2 = row.get("2-category")
        cat3 = row.get("3-category")
        cats = _norm_cat([c for c in (cat1, cat2, cat3) if c])
        # Label is unsafe if any O1/O2/O3/O4 category present
        label = "unsafe" if cats else "safe"
        yield _mk_record(
            text=text,
            label=label,
            categories=cats,
            language="en",
            source_dataset="OpenSafetyLab/Salad-Data",
            source_config="base_set",
            source_split="train",
            source_id=row.get("qid"),
            license_="Apache-2.0",
            provenance={"source": row.get("source")},
            tags=[cat1, cat2, cat3],
            _row_index=i,
        )


def iter_salad_attack(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """Salad attack_enhanced_set — jailbreak / prompt-injection variants."""
    ds = load_dataset("OpenSafetyLab/Salad-Data", "attack_enhanced_set", split="train", streaming=True)
    for i, row in enumerate(ds):
        if max_rows and i >= max_rows:
            break
        text = row.get("augq") or ""
        base = row.get("baseq") or ""
        cats = _norm_cat([row.get("1-category"), row.get("2-category"), row.get("3-category")])
        yield _mk_record(
            text=text,
            label="unsafe",
            categories=cats,
            language="en",
            source_dataset="OpenSafetyLab/Salad-Data",
            source_config="attack_enhanced_set",
            source_split="train",
            source_id=row.get("aid"),
            license_="Apache-2.0",
            provenance={"method": row.get("method"), "baseq": base},
            parent_id=row.get("qid"),
            is_jailbreak=True,
            template="salad_attack",
            _row_index=i,
        )


def iter_or_bench(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """bench-llm/or-bench — benign (over-refusal) + hard/toxic, CC-BY-4.0."""
    for cfg in ("or-bench-80k", "or-bench-hard-1k", "or-bench-toxic"):
        try:
            ds = load_dataset("bench-llm/or-bench", cfg, split="train", streaming=True)
        except Exception:
            continue
        for i, row in enumerate(ds):
            if max_rows and i >= max_rows:
                break
            text = row.get("prompt") or ""
            label = "safe" if cfg == "or-bench-80k" else "unsafe"
            cats = _norm_cat([row.get("category")])
            yield _mk_record(
                text=text,
                label=label,
                categories=cats,
                language="en",
                source_dataset="bench-llm/or-bench",
                source_config=cfg,
                source_split="train",
                source_id=text[:40],
                license_="CC-BY-4.0",
                is_benign_sensitive=(cfg == "or-bench-80k"),
                _row_index=i,
            )


def iter_prompt_injections(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """deepset/prompt-injections — binary labels (0 benign / 1 injection), Apache-2.0."""
    ds = load_dataset("deepset/prompt-injections", "default", split="train", streaming=True)
    for i, row in enumerate(ds):
        if max_rows and i >= max_rows:
            break
        text = row.get("text") or ""
        label = "unsafe" if str(row.get("label", "0")) == "1" else "safe"
        yield _mk_record(
            text=text,
            label=label,
            categories=["cyber"] if label == "unsafe" else [],
            language="en",
            source_dataset="deepset/prompt-injections",
            source_config="default",
            source_split="train",
            source_id=text[:40],
            license_="Apache-2.0",
            is_jailbreak=(label == "unsafe"),
            template="prompt_injection",
            _row_index=i,
        )


def iter_jbb_behaviors(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """JailbreakBench/JBB-Behaviors — harmful + benign pairs, MIT."""
    for split_name in ("harmful", "benign"):
        ds = load_dataset("JailbreakBench/JBB-Behaviors", "behaviors", split=split_name, streaming=True)
        for i, row in enumerate(ds):
            if max_rows and i >= max_rows:
                break
            text = row.get("Goal") or row.get("Behavior") or ""
            label = "unsafe" if split_name == "harmful" else "safe"
            cats = _norm_cat([row.get("Category")])
            yield _mk_record(
                text=text,
                label=label,
                categories=cats,
                language="en",
                source_dataset="JailbreakBench/JBB-Behaviors",
                source_config="behaviors",
                source_split=split_name,
                source_id=row.get("Index"),
                license_="MIT",
                provenance={"target": row.get("Target"), "source_field": row.get("Source")},
                is_benign_sensitive=(split_name == "benign"),
                _row_index=i,
            )


def iter_wild_jailbreak(max_rows: int | None = None) -> Iterator[CanonicalRecord]:
    """TrustAIRLab/in-the-wild-jailbreak-prompts — real jailbreaks, MIT."""
    for cfg in ("jailbreak_2023_12_25", "regular_2023_12_25"):
        try:
            ds = load_dataset("TrustAIRLab/in-the-wild-jailbreak-prompts", cfg, split="train", streaming=True)
        except Exception:
            continue
        for i, row in enumerate(ds):
            if max_rows and i >= max_rows:
                break
            text = row.get("prompt") or ""
            is_jb = str(row.get("jailbreak", "False")).lower() == "true"
            label = "unsafe" if is_jb else "safe"
            yield _mk_record(
                text=text,
                label=label,
                categories=[],
                language="en",
                source_dataset="TrustAIRLab/in-the-wild-jailbreak-prompts",
                source_config=cfg,
                source_split="train",
                source_id=text[:40],
                license_="MIT",
                provenance={"platform": row.get("platform"), "source_field": row.get("source")},
                is_jailbreak=is_jb,
                _row_index=i,
            )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ADAPTERS: dict[str, tuple] = {
    "indicguard": (iter_indicguard, "Tier 0 — primary Indic safety, CC-BY-4.0"),
    "nemotron_v3": (iter_nemotron_v3, "Tier 0 — multilingual incl. Hindi, CC-BY-4.0"),
    "aegis_2": (iter_aegis_2, "Tier 0 — English refusal set, CC-BY-4.0"),
    "aya_redteaming": (iter_aya_redteaming, "Tier 0 — Hindi/Bengali/Tamil/... red-teaming, Apache-2.0"),
    "multijail": (iter_multijail, "Tier 0 — 9-way translations incl. Bengali, MIT"),
    "salad_base": (iter_salad_base, "Tier 0 — 21k seed prompts, Apache-2.0"),
    "salad_attack": (iter_salad_attack, "Tier 0 — jailbreak variants, Apache-2.0"),
    "or_bench": (iter_or_bench, "Tier 1 — benign over-refusal + hard, CC-BY-4.0"),
    "prompt_injections": (iter_prompt_injections, "Tier 0 — prompt injection, Apache-2.0"),
    "jbb_behaviors": (iter_jbb_behaviors, "Tier 1 — harmful/benign pairs, MIT"),
    "wild_jailbreak": (iter_wild_jailbreak, "Tier 1 — in-the-wild jailbreaks, MIT"),
    # Gated (require HF_TOKEN & --include-gated)
    "wildguardmix": (None, "GATED — ODC-BY"),
    "xstest": (None, "GATED — CC-BY-4.0"),
    "harmbench": (None, "GATED — MIT"),
    "strongreject": (None, "GATED — MIT"),
    "lmsys_chat_1m": (None, "GATED — ODC-BY"),
    "wildchat_1m": (None, "GATED — ODC-BY"),
    # CC-BY-NC (opt-in only)
    "beavertails": (None, "CC-BY-NC — opt-in only"),
    "indic_safety_eval": (None, "CC-BY-NC — opt-in only"),
}


def list_adapters() -> list[tuple[str, str]]:
    return [(k, v[1]) for k, v in ADAPTERS.items()]


def get_adapter(name: str):
    if name not in ADAPTERS:
        raise KeyError(f"unknown adapter {name}. run list_adapters()")
    fn, _ = ADAPTERS[name]
    if fn is None:
        raise RuntimeError(f"{name} is gated or NC; enable with --include-gated / --include-nc and HF_TOKEN")
    return fn