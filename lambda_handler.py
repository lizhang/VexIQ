import json
import time
from datetime import datetime
from decimal import Decimal

import boto3
from pydantic import ValidationError

import config
from client import bedrock as bedrock_service
from schema import SearchQuery, IntentResult
from knowledge_service import retrieve_season, retrieve_programs

bedrock = bedrock_service.client()
dynamodb = boto3.resource("dynamodb", region_name=config.AWS_REGION)
table = dynamodb.Table(config.TABLE_NAME)

_USER_INPUT_MARKER = "========================\nUSER INPUT\n========================"

with open("prompt.md", "r") as f:
    _SYSTEM_PROMPT = f.read().split(_USER_INPUT_MARKER)[0].strip()

with open("intent_prompt.md", "r") as f:
    _INTENT_PROMPT = f.read().split(_USER_INPUT_MARKER)[0].strip()


def _strip_fence(raw: str) -> str:
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return raw


def _converse(system_prompt: str, user_input: str) -> str:
    response = bedrock.converse(
        modelId=config.MODEL_ID,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_input}]}],
    )
    return response["output"]["message"]["content"][0]["text"]


def extract_intent(user_input: str) -> IntentResult:
    """First LLM call: classify the request and extract a concrete season year."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    system_prompt = f"Today's date is {today}.\n\n{_INTENT_PROMPT}"
    raw = _strip_fence(_converse(system_prompt, user_input))
    return IntentResult.model_validate(json.loads(raw))


def normalize(raw: str) -> str:
    raw = _strip_fence(raw)
    try:
        validated = SearchQuery.model_validate(json.loads(raw))
        if validated.selectTop is not None and validated.selectTop > 25:
            validated = validated.model_copy(update={"selectTop": 25})
        return validated.model_dump_json(exclude_none=True, by_alias=True)
    except (ValidationError, json.JSONDecodeError) as e:
        return json.dumps({"error": {"message": "bedrock output json validation error", "error": str(e), "raw": raw}})


def prepare_prompt(user_input: str, intent: IntentResult) -> str:
    """Second LLM system prompt: parser + filtered RAG context + extracted hints."""
    today = datetime.utcnow().strftime("%Y-%m-%d")

    contexts = []
    if intent.season_year is not None:
        season_ctx = retrieve_season(intent.season_year)
        if season_ctx:
            contexts.append(season_ctx)
    program_ctx = retrieve_programs(user_input)
    if program_ctx:
        contexts.append(program_ctx)
    retrieved = "\n\n---\n\n".join(contexts)

    extracted = {}
    if intent.entity:
        extracted["entity"] = intent.entity
    if intent.season_year is not None:
        extracted["season_year"] = intent.season_year

    prompt = f"Today's date is {today}.\n\n{_SYSTEM_PROMPT}"
    if extracted:
        prompt += (
            "\n\n========================\nEXTRACTED\n========================\n"
            f"{json.dumps(extracted)}"
        )
    if retrieved:
        prompt += (
            "\n\n========================\nRETRIEVED CONTEXT\n========================\n"
            f"{retrieved}"
        )
    return prompt


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    user_input = body.get("text")
    if not user_input:
        return {"statusCode": 400, "body": json.dumps({"error": "text parameter is required"})}

    start = time.time()
    intent = None
    status_code = 200
    try:
        # step 1: classify intent + extract season year
        intent = extract_intent(user_input)
        print(intent)
        if intent.command or not intent.entity:
            # command -> injection/instruction attempt; missing entity -> off-topic
            status_code = 400
            output = json.dumps({"error": {"message": "unsupported request"}})
        else:
            # step 2: filtered RAG + parse into a SearchQuery
            system_prompt = prepare_prompt(user_input, intent)
            output = normalize(_converse(system_prompt, user_input))
    except Exception as e:
        output = json.dumps({"error": {"message": "bedrock call failed", "error": str(e)}})
    finally:
        end = time.time()
        duration = Decimal(str(round(end - start, 3)))

    # step 3: log request + result
    try:
        table.put_item(Item={
            "eventid": context.aws_request_id,
            "date_time": Decimal(str(round(end, 3))),
            "duration": duration,
            "input": user_input,
            "intent": intent.model_dump_json(exclude_none=True) if intent else None,
            "output": output,
        })
    except Exception as e:
        print(f"[dynamodb] put_item failed: {e}")

    # step 4: downstream service (Athena) consumes the SearchQuery
    return {"statusCode": status_code, "body": output}
