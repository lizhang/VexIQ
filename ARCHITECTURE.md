# VEX Search (VexIQ) Architecture

Natural language in, structured `SearchQuery` JSON out. VEX Search translates free-form text into a validated search object for the VEX Robotics ecosystem (teams, events, matches, rankings, skills scores).

**The LLM is a query parser, not a search engine.** It converts natural language to a structured `SearchQuery`; a separate downstream service (Athena) executes the actual data lookup against VEX data.

## Request flow

```mermaid
flowchart LR
    A["POST /search<br/>{\"text\": \"...\"}"] --> B[API Gateway<br/>VexSearchHttpApi]
    B --> C[Lambda<br/>lambda_handler.py]
    C --> D[prepare_prompt<br/>RAG + system prompt]
    D --> E[Bedrock Converse<br/>amazon.nova-lite-v1:0]
    E --> F[normalize<br/>SearchQuery schema]
    F --> G[DynamoDB<br/>search-history table]
    G --> H[SearchQuery JSON<br/>HTTP 200 response]

    KB[(Bedrock Knowledge Base)] -.->|retrieve| D
```

1. **Client** sends `POST /search` with `{"text": "..."}`.
2. **API Gateway** (`VexSearchHttpApi`) routes the request to Lambda.
3. **Lambda** (`lambda_handler.py`) orchestrates the pipeline:
   - **`prepare_prompt()`** — loads `prompt.md` at cold start, injects today's date, and calls `knowledge_service.retrieve()` to fetch season/program context from the Bedrock Knowledge Base. Retrieved chunks above `KB_SCORE_THRESHOLD` (0.65) are appended as `RETRIEVED CONTEXT`.
   - **`bedrock.converse()`** — Nova Lite parses the user query into JSON using the prepared system prompt.
   - **`normalize()`** — validates output against the Pydantic `SearchQuery` schema, strips markdown fences if present, and caps `selectTop` at 25.
   - **DynamoDB** — logs request, result, and duration to the `search-history` table.
4. **Response** — validated `SearchQuery` JSON returned to the client.

### Downstream search

This service returns a validated `SearchQuery` object only. A separate **Athena** service performs the actual data lookup against VEX teams, events, matches, and rankings.

## Key modules

| File | Role |
|------|------|
| `lambda_handler.py` | Orchestrates prompt prep, Bedrock call, normalization, and DynamoDB logging |
| `prompt.md` | System prompt — NL parsing rules, field mappings, security constraints |
| `knowledge_service.py` | RAG retrieval from Bedrock KB (season/program context; demo-scale) |
| `schema/__init__.py` | Pydantic `SearchQuery` validation; caps `selectTop` at 25 |
| `config.py` | Env vars: `TABLE_NAME`, `MODEL_ID`, `KNOWLEDGE_BASE_ID`, `KB_SCORE_THRESHOLD` |
| `client/bedrock.py` | `bedrock-runtime` + `bedrock-agent-runtime` boto3 clients |
| `run_local.py` | Local REPL — invokes `lambda_handler` with mock API Gateway event |
| `.publish/template.yaml` | SAM deploy: HTTP API, Lambda, Bedrock KB, S3 vector store |

## Data and knowledge sources

### `prompt.md` (system)

Loaded at Lambda cold start. Defines output schema, filter fields, `orderBy` rules, date normalization, and security constraints for Nova Lite.

### Bedrock Knowledge Base (RAG)

S3-backed vector index (Titan Embed v2). `knowledge_service.py` retrieves top chunks above `KB_SCORE_THRESHOLD` and injects them as `RETRIEVED CONTEXT` into the system prompt.

### `knowledge/` (source documents)

| File | Content |
|------|---------|
| `season.md` | Season year → `season_id` mapping (2013–2027) |
| `vex-program.md` | Program abbreviation → `program_id` (V5RC=1, VIQRC=41, WORKSHOP=37, etc.) |

## SearchQuery output schema

### Fields

| Field | Description |
|-------|-------------|
| `entity` | `"team"` \| `"event"` \| `"matches"` |
| `filter` | Flat `and` or `or` group of conditions (never both) |
| `orderBy` | Single sort field + direction (`asc` / `desc`) |
| `selectTop` | Max 25 (default 25; 1 when user says "best"/"top" with no number) |

### Filter condition

```python
class FilterCondition(BaseModel):
    field: str                    # e.g. "teams.city", "season_id"
    op: Literal["eq", "neq", "gt", "lt", "contains"]
    value: Union[str, int, float]
```

### Example output

Query: *"find the best team in season 2026"* (from `test/test1.json`)

```json
{
  "entity": "team",
  "filter": {
    "and": [
      { "field": "season_id", "op": "eq", "value": 203 }
    ]
  },
  "orderBy": {
    "field": "teams.best_skill_score",
    "direction": "desc"
  },
  "selectTop": 1
}
```

When adding new fields, update both `schema/__init__.py` and `prompt.md`.

## Local development

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Configure environment** — copy `.env.example` to `.env`:

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

The local REPL calls the same `lambda_handler` path. AWS credentials must be configured (Bedrock and DynamoDB).

Reference inputs/outputs: `test/test1.json`, `test/test2.json`.

## Deploy

```bash
sam deploy --template-file .publish/template.yaml --config-file .publish/samconfig.toml
```

Deploys API Gateway, Lambda, and Bedrock Knowledge Base infrastructure to AWS.
