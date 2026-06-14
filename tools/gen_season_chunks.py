"""Generate per-year season knowledge chunks for the Bedrock Knowledge Base.

Reads the consolidated seasons JSON and writes one markdown chunk per year
(grouped by ``years_start``) plus a ``.md.metadata.json`` sidecar, mirroring the
per-program chunk pattern in ``knowledge/``. Each chunk lists every season that
starts in that year (one per program) so a single retrieved chunk contains all
season_id values a year maps to.

Usage:
    python tools/gen_season_chunks.py

Source: ``tools/seasons_source.json`` (the raw seasons array). Output:
``knowledge/seasons/<year>.md`` and ``knowledge/seasons/<year>.md.metadata.json``.
"""

import json
import os
from collections import defaultdict
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "tools", "seasons_source.json")
LEGACY_MD = os.path.join(ROOT, "knowledge", "season.md")
OUT_DIR = os.path.join(ROOT, "knowledge", "seasons")
VERSION = date.today().isoformat()


def load_seasons():
    """Load the seasons array.

    Prefers ``tools/seasons_source.json``. On first run (before that file
    exists) it bootstraps from the legacy ``knowledge/season.md`` JSON fence and
    persists the extracted array as the canonical source.
    """
    if os.path.exists(SOURCE):
        with open(SOURCE, "r", encoding="utf-8") as f:
            return json.load(f)

    with open(LEGACY_MD, "r", encoding="utf-8") as f:
        text = f.read()
    fence = text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
    seasons = json.loads(fence)
    with open(SOURCE, "w", encoding="utf-8") as f:
        json.dump(seasons, f, indent=2)
        f.write("\n")
    return seasons


def write_year(year, seasons):
    seasons = sorted(seasons, key=lambda s: s["id"])
    ids = [s["id"] for s in seasons]
    body = [
        f"# VEX IQ Seasons {year}",
        f"## examples: {year} season, {year}-{year + 1} season, year {year}, "
        f"season {year}, {year} competitions",
        f"## season ids: {', '.join(str(i) for i in ids)}",
        "",
        "```json",
        json.dumps(seasons, indent=2),
        "```",
        "",
    ]
    md_path = os.path.join(OUT_DIR, f"{year}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(body))

    meta = {
        "metadataAttributes": {
            "type": "season",
            "year": str(year),
            "season_ids": ",".join(str(i) for i in ids),
            "version": VERSION,
            "status": "active",
        }
    }
    with open(md_path + ".metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
        f.write("\n")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    by_year = defaultdict(list)
    for season in load_seasons():
        by_year[season["years_start"]].append(season)
    for year, seasons in sorted(by_year.items()):
        write_year(year, seasons)
    print(f"Wrote {len(by_year)} year chunks to {OUT_DIR}")


if __name__ == "__main__":
    main()
