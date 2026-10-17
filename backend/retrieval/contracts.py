"""Public provider contracts. Chat and memory must depend on these, not SQLite."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Protocol, Callable


class RetrievalError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class AuthoritySnapshot:
    knowledge_revision: int = 0
    corrections: list[dict[str, Any]] = field(default_factory=list)
    rule_overrides: list[dict[str, Any]] = field(default_factory=list)
    shared_claims: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class RetrievalProvider(Protocol):
    provider_id: str
    namespace: str

    def catalog(self) -> dict[str, Any]: ...
    def query(self, plan: dict[str, Any], context: dict[str, Any], authority: AuthoritySnapshot | dict | None = None) -> dict[str, Any]: ...
    def evidence(self, handle: str, context: dict[str, Any]) -> dict[str, Any]: ...
    def search(self, terms: str | list[str], context: dict[str, Any], **filters) -> dict[str, Any]: ...


class GemmaEnricher(Protocol):
    """Optional future injection, owned/rate-limited by backend chain. Not called by index build."""
    def __call__(self, *, source_spans: list[dict], requested_predicates: list[str], model: str = "gemma-4-31b-it") -> dict: ...
