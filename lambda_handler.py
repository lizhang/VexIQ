import json
import time
from datetime import datetime
from decimal import Decimal

import boto3
from pydantic import ValidationError

import config
from client import bedrock as bedrock_service
from schema import SearchQuery
from knowledge_service import retrieve

bedrock = bedrock_service.client()
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



def prepare_prompt(user_input: str) -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    # add knowledge base context
    retrieved = retrieve(user_input)
    if retrieved:
        return (
            f"Today's date is {today}.\n\n{_SYSTEM_PROMPT}\n\n"
            f"========================\nRETRIEVED CONTEXT\n========================\n{retrieved}"
        )
    return f"Today's date is {today}.\n\n{_SYSTEM_PROMPT}"


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    user_input = body.get("text")
    if not user_input:
        return {"statusCode": 400, "body": json.dumps({"error": "text parameter is required"})}

    # step 1: prepare the prompt
    system_prompt = prepare_prompt(user_input)

    # step 2: call the bedrock model
    start = time.time()
    try:
        response = bedrock.converse(
            modelId=config.MODEL_ID,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_input}]}],
        )
        # step 3: normalize the output
        output = normalize(response["output"]["message"]["content"][0]["text"])
    except Exception as e:
        output = json.dumps({"error": {"message": "bedrock call failed", "error": str(e)}})
    finally:
        end = time.time()
        duration = Decimal(str(round(end - start, 3)))

    # step 4: save the result to the database
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

    # step 5: call Athena to get the results
    return {"statusCode": 200, "body": output}
