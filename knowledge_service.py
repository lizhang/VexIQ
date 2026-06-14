# knowledge_service.py
# Retrieve knowledge from the Bedrock Knowledge Base using RAG (demo only;
# in production a table lookup would be more efficient).
#
# Two focused retrievals, distinguished by chunk metadata:
#   - retrieve_season(year): the one per-year season chunk (filter type=season + year)
#   - retrieve_programs(text): program chunks only (filter type=program)

import config
from client import bedrock as bedrock_service

bedrock_agent = bedrock_service.agent_client()


def _format(results) -> str:
    """Join retrieval results above the score threshold, appending [metadata]."""
    chunks = []
    for r in results:
        if not (r.get("content", {}).get("text") and r.get("score", 0) > config.KB_SCORE_THRESHOLD):
            continue
        text = r["content"]["text"]
        metadata = r.get("metadata", {})
        if metadata:
            meta_lines = "\n".join(f"{k}: {v}" for k, v in metadata.items())
            text = f"{text}\n[metadata]\n{meta_lines}"
        chunks.append(text)
    return "\n\n---\n\n".join(chunks) if chunks else ""


def _retrieve(query: str, filter_: dict, num_results: int) -> str:
    try:
        response = bedrock_agent.retrieve(
            knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": num_results,
                    "filter": filter_,
                }
            },
        )
        print("query: ", query)
        print("filter: ", filter_)
        print("num_results: ", num_results)
        print(response)
        return _format(response.get("retrievalResults", []))
    except Exception:
        return ""


def retrieve_season(year: int) -> str:
    """Return the season chunk for a year (all season_ids that start that year)."""
    return _retrieve(
        query=f"VEX seasons {year}",
        filter_={
            "andAll": [
                {"equals": {"key": "type", "value": "season"}},
                {"equals": {"key": "year", "value": str(year)}},
            ]
        },
        num_results=1,
    )


def retrieve_programs(text: str) -> str:
    """Return up to two program chunks relevant to the user text."""
    return _retrieve(
        query=text,
        filter_={"equals": {"key": "type", "value": "program"}},
        num_results=2,
    )
