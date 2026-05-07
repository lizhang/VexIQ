import re

import config
from client import bedrock as bedrock_service

bedrock_agent = bedrock_service.agent_client()

_PROGRAM_ABBRS = re.compile(
    r"\b(V5RC|VURC|WORKSHOP|VIQRC|FAC|VAIRC|VEX_AIR_Drone_Competition)\b",
    re.IGNORECASE,
)


def retrieve(query: str) -> str:
    # add season knowledge
    query = re.sub(r"\b(\d{4})\b", r"# VEX IQ Seasons \1", query)
    # add program knowledge
    if _PROGRAM_ABBRS.search(query):
        query = "# VEX Program Organizations " + query
    # call the bedrock agent
    try:
        response = bedrock_agent.retrieve(
            knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}},
        )
        results = response.get("retrievalResults", [])
        chunks = [
            r["content"]["text"]
            for r in results
            if r.get("content", {}).get("text") and r.get("score", 0) > config.KB_SCORE_THRESHOLD
        ]
        return "\n\n---\n\n".join(chunks) if chunks else ""
    except Exception:
        return ""
