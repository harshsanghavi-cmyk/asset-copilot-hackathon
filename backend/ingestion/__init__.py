"""Immutable-source ingestion for the provisional, replaceable retrieval adapter."""
from .loader import build_index, IngestionError

__all__ = ["build_index", "IngestionError"]
