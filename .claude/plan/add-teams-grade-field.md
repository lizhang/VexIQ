# Plan: Add `teams.grade` filter field

## Context

Users search by school level ("elementary school teams", "university team"). We add a new
filter field **`teams.grade`** with four allowed values: `"Elementary School"`,
`"Middle School"`, `"High School"`, `"College"`.

A grade phrase also implies a program, resolved the existing way — via RAG over the program
chunks (VIQRC examples mention "elementary school", V5RC says "advanced middle school and
high school", VURC says "college and university"). So `teams.grade` is always set from the
grade phrase; `program_id` is added only when `retrieve_programs()` surfaces a matching
program. No fixed grade→program table, no schema-level value check.

Decisions: RAG-driven program resolution; field name `teams.grade`; value set constrained in
the prompt only (the field name is still added to the schema allow-list).

## Changes

### 1. `prompt.md`
- Add to Valid filter fields (Team block):
  `teams.grade   eq   one of: "Elementary School", "Middle School", "High School", "College"`
- Add grade-phrase mapping: elementary→"Elementary School", middle school→"Middle School",
  high school→"High School", college/university/uni→"College". Note the grade phrase also
  helps identify the program via RETRIEVED CONTEXT; add `program_id` only if surfaced.
- Add one example (e.g. "best elementary school teams in 2025").

### 2. `schema/__init__.py`
- Add `"teams.grade"` to `ALLOWED_FILTER_FIELDS`. No value validation.

## Non-changes
KB/metadata (no re-ingest), `intent_prompt.md`/`IntentResult`, `knowledge_service.py`,
`lambda_handler.py` — all unchanged.

## Verification
1. Schema unit check (no AWS): `teams.grade eq "Elementary School"` validates; invented field
   still rejected; existing season `in` checks still pass.
2. `python run_local.py` (AWS + KB): "best elementary school teams in 2025" →
   `teams.grade eq "Elementary School"` (+ program_id 41 if surfaced, + season_id);
   "top university teams" → `teams.grade eq "College"` (+ program_id 4 if surfaced);
   no-grade query → no `teams.grade`.
