"""Shield Maxer data preparation pipeline.

Pulls multilingual + Indic safety datasets, normalises them onto one schema,
deduplicates, and produces leakage-safe train/val/test splits.

Entry point: ``python -m shieldmaxer_data build --out data/processed``
"""

from .schema import CanonicalRecord, CATEGORIES, normalize_text, stable_hash
from .sources import ADAPTERS, get_adapter, list_adapters

__version__ = "0.1.0"

__all__ = [
    "CanonicalRecord",
    "CATEGORIES",
    "normalize_text",
    "stable_hash",
    "ADAPTERS",
    "get_adapter",
    "list_adapters",
]
