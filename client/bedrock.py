import boto3
import config


def client():
    return boto3.client("bedrock-runtime", region_name=config.AWS_REGION)


def agent_client():
    return boto3.client("bedrock-agent-runtime", region_name=config.AWS_REGION)
