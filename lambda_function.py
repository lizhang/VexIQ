import json
import re
import time
from datetime import datetime
from decimal import Decimal

import boto3
from pydantic import ValidationError

import config
from schema import SearchQuery

bedrock = boto3.client("bedrock-runtime", region_name=config.AWS_REGION)
bedrock_agent = boto3.client("bedrock-agent-runtime", region_name=config.AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=config.AWS_REGION)
table = dynamodb.Table(config.TABLE_NAME)

with open("prompt.md", "r") as f:
    _raw = f.read()

_SYSTEM_PROMPT = _raw.split("========================\nUSER INPUT\n========================")[0].strip()

_PROGRAM_ABBRS = re.compile(
    r"\b(V5RC|VURC|WORKSHOP|VIQRC|FAC|VAIRC|VEX_AIR_Drone_Competition)\b",
    re.IGNORECASE,
)


def normalize(raw: str) -> str:
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        validated = SearchQuery.model_validate(json.loads(raw))
        if validated.selectTop is not None and validated.selectTop > 25:
            validated = validated.model_copy(update={"selectTop": 25})
        return validated.model_dump_json(exclude_none=True)
    except (ValidationError, json.JSONDecodeError) as e:
        return json.dumps({"error": {"message": "bedrock output json validation error", "error" : str(e), "raw" : raw } })


def retrieve_context(query: str) -> str:
    query = re.sub(r"\b(\d{4})\b", r"# VEX IQ Seasons \1", query)
    if _PROGRAM_ABBRS.search(query):
        query = "# VEX Program Organizations " + query
    try:
        response = bedrock_agent.retrieve(
            knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}},
        )
        results = response.get("retrievalResults", [])
        #for i, r in enumerate(results):
        #    print(f"[retrieve_context #{i}] score={r.get('score')} text={r.get('content', {}).get('text')!r}")
        chunks = [
            r["content"]["text"]
            for r in results
            if r.get("content", {}).get("text") and r.get('score') > 0.65    
        ]
        return "\n\n---\n\n".join(chunks) if chunks else ""
    except Exception:
        return ""


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    user_input = body.get("text")
    if not user_input:
        return {"statusCode": 400, "body": json.dumps({"error": "text parameter is required"})}

    today = datetime.utcnow().strftime("%Y-%m-%d")
    retrieved = retrieve_context(user_input)
   
    if retrieved:
        system_prompt = (
            f"Today's date is {today}.\n\n{_SYSTEM_PROMPT}\n\n"
            f"========================\nRETRIEVED CONTEXT\n========================\n{retrieved}"
        )
    else:
        system_prompt = f"Today's date is {today}.\n\n{_SYSTEM_PROMPT}"

    start = time.time()
    try:
        response = bedrock.converse(
            modelId=config.MODEL_ID,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_input}]}],
        )
        output = normalize(response["output"]["message"]["content"][0]["text"])
    except Exception as e:
        output = json.dumps({"error": {"message": "bedrock call failed", "error": str(e)}})
    finally:
        end = time.time()
        duration = Decimal(str(round(end - start, 3)))

    try:
        table.put_item(Item={
            "eventid": context.aws_request_id,
            "date_time": Decimal(str(round(end, 3))),
            "duration": duration,
            "input": user_input,
            "output": output,
        })
    except Exception as e:
        print(f"[dynamodb] put_item failed: {e}")

    return {"statusCode": 200, "body": output}
