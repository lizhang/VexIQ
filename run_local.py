import uuid
import json
from dotenv import load_dotenv

load_dotenv()

from lambda_handler import lambda_handler

class MockContext:
    def __init__(self):
        self.aws_request_id = str(uuid.uuid4())


if __name__ == "__main__":
    print("Enter input (press Enter to submit, Ctrl+C to quit):")
    while True:
        try:
            user_input = input("> ")
            if not user_input.strip():
                continue
            context = MockContext()
            result = lambda_handler({"body": json.dumps({"text": user_input})}, context)
            print(json.dumps(json.loads(result["body"]), indent=2))
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
