# VEX IQ Robotics Competition Seasons

## Season Lookup Rules

Use these rules to resolve a season_id from user input:

1. **Explicit year range** — If the user provides both a start year and end year (e.g. "2024-2025" or "2024 to 2025"), match the row where `year_start` and `year_end` equal those values and return its `season_id`.

2. **"This year" / "current season"** — If the user mentions only a single year or says "this year" / "current season", check today's date against each row's `start` and `end` dates. Return the `season_id` of the season whose date range contains today. If today falls between seasons, prefer the upcoming season.

3. **"Last year" / "last season"** — Find the current season using rule 2, then return the `season_id` of the row immediately below it in the table (the season that ended just before the current one began).

4. **Single year ambiguity** — A year like "2025" can be either `year_start` or `year_end`. Resolve it by first checking if a season starts in that year; if none does, check if a season ends in that year.

---

| season_id | name | start | end | year_start | year_end |
|-----------|------|-------|-----|------------|----------|
| 203 | VEX IQ Robotics Competition 2026-2027: Level Up | 2026-04-30 | 2027-12-25 | 2026 | 2027 |
| 196 | VEX IQ Robotics Competition 2025-2026: Mix & Match | 2025-04-29 | 2025-12-25 | 2025 | 2026 |
| 189 | VEX IQ Robotics Competition 2024-2025: Rapid Relay | 2024-04-16 | 2024-12-19 | 2024 | 2025 |
| 180 | VIQRC 2023-2024: Full Volume | 2023-04-05 | 2023-12-15 | 2023 | 2024 |
| 174 | VIQC 2022-2023: Slapshot | 2022-04-18 | 2023-04-01 | 2022 | 2023 |
| 155 | VIQC 2021-2022: Pitching In | 2021-04-15 | 2022-04-18 | 2021 | 2022 |
| 138 | VIQC 2020-2021: Rise Above | 2020-04-25 | 2021-05-15 | 2020 | 2021 |
| 129 | VIQC 2019-2020: Squared Away | 2019-04-30 | 2020-04-16 | 2019 | 2020 |
| 124 | VIQC 2018-2019: Next Level | 2018-05-01 | 2019-04-16 | 2018 | 2019 |
| 121 | VIQC 2017-2018: Ringmaster | 2017-05-05 | 2018-04-18 | 2017 | 2018 |
| 114 | VIQC 2016-2017: Crossover | 2016-03-01 | 2017-02-14 | 2016 | 2017 |
| 109 | VIQC 2015-2016: Bank Shot | 2015-03-01 | 2016-02-14 | 2015 | 2016 |
| 101 | VIQC 2014-2015: Highrise | 2014-03-01 | 2015-02-14 | 2014 | 2015 |
| 96 | VIQC 2013-2014: Add It Up | 2013-03-01 | 2014-02-14 | 2013 | 2014 |
