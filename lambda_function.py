import json
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
    try:
        response = bedrock_agent.retrieve(
            knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 5}},
        )
        chunks = [
            r["content"]["text"]
            for r in response.get("retrievalResults", [])
            if r.get("content", {}).get("text")
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
    context = retrieve_context(f"{today} {user_input}")
    if context:
        system_prompt = (
            f"Today's date is {today}.\n\n{_SYSTEM_PROMPT}\n\n"
            f"========================\nRETRIEVED CONTEXT\n========================\n{context}"
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

    table.put_item(Item={
        "eventid": context.aws_request_id,
        "date_time": Decimal(str(round(end, 3))),
        "duration": duration,
        "input": user_input,
        "output": output,
    })

    return {"statusCode": 200, "body": output}
