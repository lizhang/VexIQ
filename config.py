import os


TABLE_NAME = os.environ["TABLE_NAME"]
MODEL_ID = os.environ["MODEL_ID"]
AWS_REGION = os.environ["AWS_REGION"]
KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
KB_SCORE_THRESHOLD = float(os.environ.get("KB_SCORE_THRESHOLD", "0.65"))
