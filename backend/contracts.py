"""Application schemas; provider data is versioned and never tied to storage tables."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, AliasChoices


class MemoryDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["preference", "work_context", "plan", "observation", "guidance", "hypothesis", "correction", "rule"]
    scope: Literal["private", "shared"] = "shared"
    subject_kind: Literal["user", "asset", "equipment", "type", "team", "organization"] = "asset"
    subject_ids: list[str] = Field(default_factory=list, max_length=30)
    statement: str = Field(min_length=1, max_length=1600)
    source_quote: str = Field(min_length=1, max_length=2500)
    valid_from: str | None = None
    valid_to: str | None = None
    planned_start: str | None = None
    planned_end: str | None = None
    qualifier: str = "attributed"
    target_record_id: str | None = None
    field: str | None = None
    value: Any = None
    reason: str | None = None
    rule_id: str | None = None
    well_type: str | None = None
    equipment_kind: str | None = None
    threshold: float | None = None
    lookback_months: int = 12
    supersedes: str | None = None

    @field_validator("valid_from", "valid_to", "planned_start", "planned_end")
    @classmethod
    def iso_date(cls, value):
        if value is not None:
            from datetime import date
            return date.fromisoformat(value).isoformat()
        return value

    @model_validator(mode="after")
    def valid_intervals(self):
        for start, end in ((self.valid_from, self.valid_to), (self.planned_start, self.planned_end)):
            if start and end and end <= start:
                raise ValueError("Memory validity end must follow its start")
        return self


class EvidenceSearch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    terms: str = Field(min_length=1, max_length=512, validation_alias=AliasChoices("terms", "query"))
    asset_id: str | None = None
    kind: Literal["manual", "sop", "report"] | None = None

    @field_validator("terms")
    @classmethod
    def nonempty(cls, value):
        if not value.strip():
            raise ValueError("Search terms must not be empty")
        return value.strip()


class PlannerOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    intent: str = "answer"
    title: str | None = Field(default=None, max_length=90)
    clarification: str | None = None
    direct_response: str | None = Field(default=None, max_length=2000)
    queries: list[dict[str, Any]] = Field(default_factory=list, max_length=8)
    evidence_searches: list[EvidenceSearch] = Field(default_factory=list, max_length=3)
    memory_proposals: list[MemoryDraft] = Field(default_factory=list, max_length=8)
    requested_visuals: list[Literal["status", "table", "line", "bar", "heatmap", "map", "diagram"]] = Field(default_factory=list, max_length=8)
    reference_text: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_search_contract(cls, values):
        if not isinstance(values, dict):
            return values
        if "queries" not in values:
            for key in ("plan", "planner", "plan_output"):
                if isinstance(values.get(key), dict) and "queries" in values[key]:
                    values = values[key]
                    break
        values = dict(values);queries = list(values.get("queries") or []);searches = []
        normalized_queries = []
        for query in queries:
            if isinstance(query, dict) and not query.get("collection"):
                for key in ("query", "query_params", "parameters", "args"):
                    nested = query.get(key)
                    if isinstance(nested, dict) and nested.get("collection") and nested.get("metric"):
                        query = nested
                        break
            normalized_queries.append(query)
        queries = normalized_queries
        for item in values.get("evidence_searches") or []:
            if isinstance(item, str):
                searches.append({"terms": item})
            elif isinstance(item, dict) and not item.get("terms") and not item.get("query") and isinstance(item.get("query_params"), dict):
                query = item["query_params"]
                if not query.get("collection") or not query.get("metric"):
                    raise ValueError("A record query needs explicit collection and metric")
                if query not in queries:
                    queries.append(query)
            else:
                searches.append(item)
        values.update(queries=queries, evidence_searches=searches)
        return values

    @field_validator("queries", "evidence_searches", "memory_proposals", "requested_visuals", mode="before")
    @classmethod
    def absent_arrays(cls, value):
        return [] if value is None else value

    @field_validator("requested_visuals", mode="before")
    @classmethod
    def visual_names(cls, value):
        if value is None:
            return []
        if isinstance(value, dict):
            value = [value]
        if isinstance(value, list):
            aliases = {"status_card": "status", "statuscard": "status", "line_chart": "line", "bar_chart": "bar", "heat_map": "heatmap"}
            names = []
            for item in value:
                item = item.get("type", item.get("chart_type", item.get("kind"))) if isinstance(item, dict) else item
                if isinstance(item, str):
                    item = item.strip().casefold().replace(" ", "_")
                    item = aliases.get(item, item)
                names.append(item)
            return names
        return value


class ViewBlock(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["status", "table", "line", "bar", "heatmap", "map", "diagram"]
    title: str = Field(max_length=180)
    result_set_id: str
    evidence_ids: list[str] = Field(default_factory=list)
    encoding: dict[str, str] = Field(default_factory=dict)
    span: Literal[1, 2, 3] = 2


class ValueReference(BaseModel):
    result_set_id: str = Field(validation_alias=AliasChoices("result_set_id", "result_id"))
    row_index: int = Field(ge=0, validation_alias=AliasChoices("row_index", "row"))
    column: str = Field(validation_alias=AliasChoices("column", "column_key", "field"))


class AnswerClaim(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    kind: Literal["fact", "inference", "suggestion"] = "fact"
    evidence_ids: list[str] = Field(default_factory=list)
    value_refs: list[ValueReference] = Field(default_factory=list)

    @field_validator("evidence_ids", "value_refs", mode="before")
    @classmethod
    def normalize_single(cls, value):
        if value is None:return []
        if isinstance(value, (str, dict)):return [value]
        return value


class ViewPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    narrative: str = Field(max_length=10000)
    blocks: list[ViewBlock] = Field(default_factory=list, max_length=12)
    claims: list[AnswerClaim] = Field(default_factory=list, max_length=30)

    @model_validator(mode="before")
    @classmethod
    def unwrap_view(cls, value):
        if isinstance(value, dict) and "narrative" not in value:
            for key in ("answer", "view_plan", "response"):
                if isinstance(value.get(key), dict) and "narrative" in value[key]:
                    return value[key]
        return value


class SuggestionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suggestions: list[str] = Field(min_length=3, max_length=3)

    @field_validator("suggestions")
    @classmethod
    def short_questions(cls, value):
        if any(not 5 <= len(v.strip()) <= 120 for v in value) or len({v.strip().casefold() for v in value}) != 3:
            raise ValueError("Three distinct short questions are required")
        return [v.strip() for v in value]


class ProviderUnavailable(RuntimeError):
    pass


class ModelUnavailable(RuntimeError):
    def __init__(self, code: str, message: str, *, retry_after: float | None = None):
        super().__init__(message)
        self.code, self.retry_after = code, retry_after


def json_safe(value: Any) -> Any:
    """Keep provider values, normalizing serialization only, never recomputing facts."""
    import json
    return json.loads(json.dumps(value, default=str, ensure_ascii=False))
