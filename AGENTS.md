# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

VEX Search translates natural language queries into structured JSON search objects for the VEX Robotics ecosystem (teams, events, matches, rankings, skills scores). The core intelligence is an LLM prompt (`prompt.md`) that maps free-form text to a validated `SearchQuery` Pydantic schema.

## Local Development

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Configure environment** — copy `.env.example` to `.env` and fill in:
```
TABLE_NAME=search-history
MODEL_ID=amazon.nova-lite-v1:0
AWS_REGION=us-east-1
KNOWLEDGE_BASE_ID=<bedrock-kb-id>
KB_SCORE_THRESHOLD=0.65
```

**Run interactively:**
```bash
python run_local.py
```
This starts a REPL that accepts natural language queries and prints the structured `SearchQuery` JSON. AWS credentials must be configured (the handler calls Bedrock and DynamoDB).

**No automated test suite** — expected inputs/outputs live in `test/test1.json` and `test/test2.json` as reference examples.

## Deploy

```bash
sam deploy --template-file .publish/template.yaml --config-file .publish/samconfig.toml
```

## Architecture

```
POST /search {"text": "..."}
  → API Gateway
  → lambda_handler.py        # orchestration
      prepare_prompt()        # injects season/program context from Bedrock Knowledge Base
      bedrock.converse()      # Nova Lite parses NL → JSON using prompt.md as system prompt
      normalize()             # Pydantic validation, caps selectTop at 25
      DynamoDB write          # logs request + result to search-history table
  → SearchQuery JSON
```

**The LLM is a query parser, not a search engine.** It converts natural language to a structured `SearchQuery`; a separate downstream service (Athena) does the actual data lookup.

## Key Files

| File | Role |
|------|------|
| `lambda_handler.py` | Entry point — orchestrates prompt prep, Bedrock call, normalization, DynamoDB logging |
| `schema/__init__.py` | Pydantic models: `SearchQuery`, `FilterGroup`, `FilterCondition`, `OrderBy` |
| `prompt.md` | System prompt that teaches Nova Lite how to parse queries — **most logic lives here** |
| `knowledge_service.py` | RAG retrieval from Bedrock Knowledge Base (demo only; not for production scale) |
| `config.py` | Environment variable accessors |
| `client/bedrock.py` | Bedrock client initialization |
| `knowledge/vex-program.md` | Program name → ID mapping (V5RC=1, VIQRC=41, WORKSHOP=37, etc.) |
| `knowledge/season.md` | Season year range → season_id mapping (2013–2027) |

## SearchQuery Schema

```python
class FilterCondition(BaseModel):
    field: str                                          # e.g. "teams.city", "season_id"
    op: Literal["eq", "neq", "gt", "lt", "contains"]
    value: Union[str, int, float]

class FilterGroup(BaseModel):                           # one of "and" / "or", never both
    and_: Optional[List[FilterCondition]]  # alias "and"
    or_:  Optional[List[FilterCondition]]  # alias "or"

class OrderBy(BaseModel):
    field: str                                          # e.g. "rankings.rank", "events.time"
    direction: Literal["asc", "desc"]

class SearchQuery(BaseModel):
    entity:    Optional[str]          # "team" | "event" | "matches"
    filter:    Optional[FilterGroup]  # flat AND/OR list of conditions
    orderBy:   Optional[OrderBy]      # single sort field + direction
    selectTop: Optional[int]          # max 25
```

When adding new fields, update both `schema/__init__.py` (Pydantic model) and `prompt.md` (rules telling the LLM when/how to populate the field).

## Prompt Engineering Notes

`prompt.md` is the source of truth for query-parsing behavior. Key rules defined there:

- **Security:** User input is treated as plain text only — injection attempts (SQL, code, prompt overrides) are ignored.
- **selectTop:** defaults to 25; capped at 25; if user says "best"/"top" with no number → 1.
- **orderBy:** `rankings.rank` for top/best/highest-ranked; `events.score`/`matches.score`/`teams.*_score` for score queries; `events.time`/`matches.time` for latest/upcoming/recent; skill-specific fields (`teams.best_skill_score`, `events.skills_rank`) when "skill" is mentioned.
- **Dates:** ISO 8601 with timezone. Relative dates (today, next weekend) are resolved against the provided current date.
- **Location normalization:** "US"/"USA" → "United States"; "LA" → "Los Angeles" (as city).
- **Season/Program resolution:** Resolved via RAG context injected at runtime, not hardcoded in the prompt.
- **Filter serialization:** `by_alias=True` is required in `model_dump_json` so Python fields `and_`/`or_` serialize as `"and"`/`"or"` in JSON.
