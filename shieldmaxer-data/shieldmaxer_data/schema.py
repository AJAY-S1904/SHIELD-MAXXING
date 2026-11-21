"""Canonical record schema shared by every source adapter.

One row == one *prompt* (user turn). Response moderation is carried in
``response``/``response_label`` for future use but must never influence the
prompt-level training label.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

LABELS = ("safe", "unsafe", "ambiguous")


def stable_hash(*parts: object, size: int = 20) -> str:
    """Deterministic short hash used for ids and group keys."""
    payload = "\x1f".join("" if p is None else str(p) for p in parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:size]


#: Canonical harm taxonomy. Kept deliberately small so the classifier head can
#: learn it; Indian-specific categories (caste / communal / regional) are
#: first-class because generic English taxonomies collapse them into "hate".
CATEGORIES: dict[str, str] = {
    "violence": "Violence, threats or incitement",
    "weapons": "Weapons and explosives",
    "hate": "Hate speech, harassment or discrimination",
    "caste": "Caste-based abuse or discrimination",
    "communal": "Communal or religious hatred",
    "regional": "Regional, ethnic or racist abuse",
    "sexual": "Sexual content, exploitation or trafficking",
    "csam": "Child sexual abuse material",
    "self_harm": "Suicide and self-harm",
    "drugs": "Drugs and regulated substances",
    "criminal": "Criminal planning or wrongdoing",
    "cyber": "Cyber abuse, malware or unauthorised access",
    "fraud": "Fraud, scams or deception",
    "privacy": "Privacy, PII or doxxing",
    "misinfo": "Harmful misinformation",
    "other": "Other harmful content",
}

SCRIPTS = ("native", "latin", "mixed", "unknown")


@dataclass
class CanonicalRecord:
    """A single normalised training/eval example."""

    record_id: str
    text: str
    label: str  # safe | unsafe | ambiguous
    categories: list[str] = field(default_factory=list)

    # Input-form metadata (FR-02: native / Romanized / code-mixed coverage)
    language: str | None = None  # ISO-639-1 where known
    script: str = "latin"  # native | latin | mixed | unknown
    romanized: bool = False
    code_mixed: bool = False

    # Task metadata
    is_jailbreak: bool = False
    is_benign_sensitive: bool = False
    template: str | None = None

    # Optional response-side supervision (not used for prompt labels)
    response: str | None = None
    response_label: str | None = None

    # Provenance
    source_dataset: str = ""
    source_config: str | None = None
    source_split: str | None = None
    source_id: str | None = None
    license: str | None = None
    parent_id: str | None = None
    group_id: str = ""
    text_hash: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.label not in LABELS:
            raise ValueError(f"bad label {self.label!r} for {self.record_id}")
        self.categories = sorted(set(self.categories))
        if self.script not in SCRIPTS:
            self.script = "unknown"
        if not self.text_hash:
            self.text_hash = stable_hash(normalize_text(self.text))
        if not self.group_id:
            self.group_id = f"txt:{self.text_hash}"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["categories"] = list(self.categories)
        d["tags"] = list(self.tags)
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


_WS = re.compile(r"\s+")
_ZW = re.compile(r"[\u200b-\u200f\u202a-\u202e\ufeff]")


def normalize_text(text: str | None) -> str:
    """Whitespace/zero-width normalisation used for hashing and modelling."""
    if not text:
        return ""
    import unicodedata

    t = unicodedata.normalize("NFC", str(text))
    t = _ZW.sub("", t)
    t = t.replace("\u00a0", " ")
    return _WS.sub(" ", t).strip()


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it and it not in seen:
            seen.add(it)
            out.append(it)
    return out
