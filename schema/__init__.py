from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Literal, List, Union


# Allowed field names — must stay in sync with the "Valid filter fields" and
# "Valid orderBy fields" lists in prompt.md. Anything outside these sets is an
# invented field and is rejected.
ALLOWED_FILTER_FIELDS = frozenset({
    "teams.city", "teams.postcode", "teams.country", "teams.region",
    "events.city", "events.postcode", "events.country", "events.region", "events.venue",
    "events.name", "events.sku",
    "events.start_time", "events.end_time", "matches.start_time", "matches.end_time",
    "teams.name", "teams.number", "teams.grade",
    "program_id", "season_id",
})

ALLOWED_ORDERBY_FIELDS = frozenset({
    "teams.best_skill_score", "teams.worst_skill_score", "teams.avg_skill_score",
    "events.skills_rank", "rankings.rank",
    "events.score", "matches.score",
    "teams.high_score", "teams.average_points", "teams.total_points",
    "events.time", "matches.time",
})


class FilterCondition(BaseModel):
    field: str
    op: Literal["eq", "neq", "gt", "lt", "contains", "in"]
    value: Union[str, int, float, List[Union[int, str]]]

    @model_validator(mode="after")
    def _check(self):
        if self.field not in ALLOWED_FILTER_FIELDS:
            raise ValueError(f'unknown filter field "{self.field}"')
        is_list = isinstance(self.value, list)
        if self.op == "in" and not is_list:
            raise ValueError('op "in" requires a list value')
        if self.op != "in" and is_list:
            raise ValueError(f'op "{self.op}" requires a scalar value, not a list')
        return self


class FilterGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    and_: Optional[List[FilterCondition]] = Field(None, alias="and")
    or_: Optional[List[FilterCondition]] = Field(None, alias="or")


class OrderBy(BaseModel):
    field: str
    direction: Literal["asc", "desc"]

    @model_validator(mode="after")
    def _check_field(self):
        if self.field not in ALLOWED_ORDERBY_FIELDS:
            raise ValueError(f'unknown orderBy field "{self.field}"')
        return self


class SearchQuery(BaseModel):
    entity: Optional[str] = Field(None, pattern="^(team|event|matches)$")
    filter: Optional[FilterGroup] = None
    orderBy: Optional[OrderBy] = None
    selectTop: Optional[int] = None


class IntentResult(BaseModel):
    """Output of the first (intent) LLM call."""
    command: bool = False
    entity: Optional[str] = Field(None, pattern="^(team|event|matches)$")
    season_year: Optional[int] = None
