# Plan: Two-step LLM pipeline (intent/year extraction → filtered RAG → query parse)

## Context

Previously `lambda_handler` made a **single** Nova Lite call: `prepare_prompt()` ran one
RAG retrieval (`knowledge_service.retrieve`, top-3, with a `\d{4}` → `# VEX IQ Seasons`
query hack) and fed `prompt.md` to the model, which both guarded against prompt injection
and parsed the query. This conflated security, season resolution, and parsing in one shot.

We split this into **two LLM calls**:

1. **Intent call** — classify the request and extract the season year.
   - Prompt injection (execute/follow/interpret commands) → **return an error**, skip the rest.
   - Classify a coarse `entity` (team | event | matches).
   - Extract a concrete `season_year`: range → **start year**; single year → that year;
     relative terms ("last year", "current season") → resolved to a concrete year via today.
2. **Retrieval + parse call**:
   - `season_year` present → KB retrieval filtered to the **season chunk** (`year` metadata, top 1).
   - Always retrieve **program chunks** (`type=program`, top 2) using the user text.
   - Feed both chunks + user input + `entity`/`season_year` hints into `prompt.md` → `SearchQuery`.

Decisions: single KB with metadata filters; step-1 also classifies entity; step-1 resolves
relative years.

## Changes

1. **`intent_prompt.md`** (new) — call-1 system prompt. Returns JSON only:
   `{ "command": bool, "entity": "team|event|matches", "season_year": int }`.
2. **`schema/__init__.py`** — add `IntentResult(command: bool, entity: Optional[str], season_year: Optional[int])`.
3. **Metadata `type` attribute** — program sidecars (`knowledge/*.md.metadata.json`, 7) get
   `"type": "program"`; season sidecars (`knowledge/seasons/*.md.metadata.json`) get
   `"type": "season"` (also emitted by `tools/gen_season_chunks.py`). Re-ingest KB (owner: user).
4. **`knowledge_service.py`** — replace `retrieve()` with `retrieve_season(year)` (filter
   `year==year`, top 1) and `retrieve_programs(text)` (filter `type==program`, top 2); drop the
   regex hack; shared per-result formatting helper.
5. **`lambda_handler.py`** — load both prompts; `extract_intent(user_input) -> IntentResult`;
   command → error (400) + log + stop; build filtered RETRIEVED CONTEXT + EXTRACTED hints;
   second converse → normalize. Remove the `this year: {now.year}` append.
6. **`prompt.md`** — note that `season_year`/`entity` may be supplied in an EXTRACTED block and
   should be trusted (no re-derivation). Security section kept as defense-in-depth.

## Verification
1. Intent unit check (no AWS): command/injection → `command=true`; "best team in 2025" →
   2025/team; "2022 to 2023 season" → 2022; "last year" (today 2026-06-13) → 2025.
2. Retrieval (AWS + re-ingested KB): `retrieve_season(2025)` → chunk with 196,197,198,199,201;
   `retrieve_programs("VIQRC teams")` → program chunks only.
3. `python run_local.py`: "best team in 2025 VIQRC" → `season_id eq 196`; "best team in 2025"
   → `season_id in [196,197,198,199,201]`; injection → error; no year/program → program ctx only.
