import os
import json
import logging
import time
import boto3

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Config (NO API KEY NEEDED)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amistral.mistral-7b-instruct-v0:2")

# Create Bedrock client (uses EC2 IAM role automatically)
bedrock = boto3.client(
    "bedrock-runtime",
    region_name=AWS_REGION
)

# Retry utility
def _retry_call(func, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            logger.warning(f"⚠️ Bedrock call failed (Attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise

# Wrap response in Markdown if it looks like code
def wrap_markdown(text: str) -> str:
    code_keywords = ["def ", "SELECT ", "CREATE ", "import ", "if ", "while ", "class ", "try:"]
    is_code = any(kw in text for kw in code_keywords)

    if is_code:
        return f"```python\n{text.strip()}\n```"
    return text.strip()

# Main LLM function
def call_bedrock(
    prompt: str,
    temperature: float = 0.5,
    max_output_tokens: int = 2000,
) -> str:
    """
    Sends a prompt to Amazon Bedrock (Titan model)
    """

    def make_request():
        logger.info(f"📤 Sending prompt to Bedrock: {prompt[:80]}...")

        body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_output_tokens,
                "temperature": temperature,
                "topP": 0.9
            }
        }

        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body)
        )

        result = json.loads(response["body"].read())

        if "results" in result and len(result["results"]) > 0:
            output_text = result["results"][0]["outputText"]
            logger.info("✅ Bedrock response received.")
            return wrap_markdown(output_text)
        else:
            logger.warning("⚠️ Bedrock returned empty response.")
            return "⚠️ Model returned empty response."

    try:
        return _retry_call(make_request)
    except Exception as e:
        logger.error(f"❌ Bedrock API call failed after retries: {e}")
        return "❌ Unable to process request at the moment. Please try again later."

# Agent-style prompt wrapping
def agent_response(prompt: str, agent_type: str = "code_reviewer") -> str:
    prefix_map = {
        "code_reviewer": "Please review the following code:\n",
        "code_generator": "Generate code for the following instruction:\n",
        "sql_translator": "Convert this into an SQL query:\n"
    }

    full_prompt = prefix_map.get(agent_type, "") + prompt
    return call_bedrock(full_prompt)