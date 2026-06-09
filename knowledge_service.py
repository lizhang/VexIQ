# knowledge_service.py
# This file is used to retrieve knowledge from the knowledge base
# using RAG just for demo purpose
# in production, we will use a more efficient way to retrieve knowledge, like table lookup

import re

import config
from client import bedrock as bedrock_service

bedrock_agent = bedrock_service.agent_client()

_PROGRAM_ABBRS = re.compile(
    r"\b(V5RC|VURC|WORKSHOP|VIQRC|FAC|VAIRC|VEX_AIR_Drone_Competition)\b",
    re.IGNORECASE,
)


def retrieve(query: str) -> str:
    # add season knowledge#
    query = re.sub(r"\b(\d{4})\b", r"# VEX IQ Seasons \1", query)
    # add program knowledge
    # if _PROGRAM_ABBRS.search(query):
    #    query = "# VEX Program Organizations " + query
    # call the bedrock agent
    try:
        response = bedrock_agent.retrieve(
            knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}},
        )
        results = response.get("retrievalResults", [])
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
    except Exception:
        return ""
