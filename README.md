# VEX Search

VEX Search is a natural language search application for VEX Robotics players, teams, and organizers.

As a VEX player, are you tired of searching for next week’s tournament schedule or checking the current skills rankings in your region?

VEX Search is built to answer those questions using AI-powered search.

Simply type your question, and VEX Search will return information about:

* Teams
* Events
* Matches
* Rankings
* Skills scores

## Example

### Type

```text
Find the top 10 teams in Los Angeles for the 2025 season.
```

### Return

```json
[
  {
    "team": "Chicken Bucket",
    "ranking": 1,
    "skill_score": 198,
    "organization": "Magic Kid",
    "city": "San Diego"
  }
]
```

## Features

* Natural language search
* AI-powered query translation
* Team and event lookup
* Regional ranking search
* Structured JSON responses

## Architecture

```text
User Query
   ↓
AWS API Gateway
   ↓
AWS Lambda
   ↓
Amazon Bedrock (Nova Lite)
   ↓
Structured Search JSON
   ↓
Athena / Database Query
   ↓
Search Results
```

## Tech Stack

* Python
* AWS Lambda
* Amazon Bedrock
* Amazon Nova Lite
* AWS Athena
* DynamoDB
* API Gateway
* Pydantic

## Goal

The goal of this project is to make VEX Robotics data easier to access through conversational AI and natural language search.

## Getting Started

### Install

```bash
pip install -r requirements.txt
```

### Configure

Copy `.env.example` to `.env` and fill in:

```
TABLE_NAME=search-history
MODEL_ID=amazon.nova-lite-v1:0
AWS_REGION=us-east-1
KNOWLEDGE_BASE_ID=<bedrock-kb-id>
KB_SCORE_THRESHOLD=0.65
```

AWS credentials must also be configured in your environment.

### Run Locally

```bash
python run_local.py
```

Starts an interactive REPL — type natural language queries and see the structured `SearchQuery` JSON output.

### Build

```bash
sam build --template-file .publish/template.yaml
```

### Deploy

```bash
sam deploy --template-file .publish/template.yaml --config-file .publish/samconfig.toml
```

## Notes

RAG is used here for demo purposes only.
