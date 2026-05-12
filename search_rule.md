# Search Rule Reference

## Filter

Each filter condition has a `field`, an `op` (operation), and a `value`.
Conditions are grouped under a single `"and"` or `"or"` key (one level only, no nesting).

### Operations
| op       | Meaning              |
|----------|----------------------|
| eq       | exact match          |
| neq      | not equal            |
| gt       | greater than         |
| lt       | less than            |
| contains | substring / partial  |

### Filter Fields

**Location** (applies to teams or events)

| Field           | op       | Notes                        |
|-----------------|----------|------------------------------|
| teams.city      | eq       | full city name               |
| teams.postcode  | eq       |                              |
| teams.country   | eq       | full country name            |
| teams.region    | contains |                              |
| events.city     | eq       | full city name               |
| events.postcode | eq       |                              |
| events.country  | eq       | full country name            |
| events.region   | contains |                              |
| events.venue    | contains |                              |

**Event**

| Field       | op       |
|-------------|----------|
| events.name | contains |
| events.sku  | eq       |

**Time** — always a range: `gt` on start + `lt` on end

| Field               | op |
|---------------------|----|
| events.start_time   | gt |
| events.end_time     | lt |
| matches.start_time  | gt |
| matches.end_time    | lt |

**Team**

| Field        | op       |
|--------------|----------|
| teams.name   | contains |
| teams.number | eq       |

**Program / Season**

| Field      | op |
|------------|----|
| program_id | eq |
| season_id  | eq |

---

## orderBy

Single object: `{"field": "<field>", "direction": "asc" | "desc"}`

### Skill score
Only valid with `season_id` / `program_id` filter. Cannot be combined with location, event, or time filters.

| Field                  | When to use                      |
|------------------------|----------------------------------|
| teams.best_skill_score | user asks for best skill score   |
| teams.worst_skill_score| user asks for worst skill score  |
| teams.avg_skill_score  | user asks for average skill score|

### Skills rank
Supports event / team / location / season_id / program_id filters. Not valid with matches time filter.

| Field             | When to use              |
|-------------------|--------------------------|
| events.skills_rank| user mentions skill rank |

### Rankings
Supports event / team / location / season_id / program_id filters. Not valid with matches time filter.

| Field         | When to use                              |
|---------------|------------------------------------------|
| rankings.rank | user says "top", "best", "highest ranked"|

### Score

| Field               | When to use                                            | Filter restriction              |
|---------------------|--------------------------------------------------------|---------------------------------|
| events.score        | score in event context                                 | not valid with matches time     |
| matches.score       | score in matches context                               |                                 |
| teams.high_score    | user mentions team's high score                        | team + season_id / program_id only |
| teams.average_points| user mentions team's average points                    | team + season_id / program_id only |
| teams.total_points  | user mentions team's total points                      | team + season_id / program_id only |

### Time

| Field        | When to use                                      |
|--------------|--------------------------------------------------|
| events.time  | user says "latest", "upcoming", "recent" (events)|
| matches.time | user says "latest", "upcoming", "recent" (matches)|
