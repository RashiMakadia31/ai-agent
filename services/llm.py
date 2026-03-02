import os
import logging
import time
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env from project root (local/dev) and normal environment (EC2/systemd)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(dotenv_path=os.path.join(project_root, ".env"))
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment. Configure it before starting the app.")
    raise EnvironmentError("Missing GEMINI_API_KEY in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _retry_call(func, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            logger.warning(f"Gemini call failed (Attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


def wrap_markdown(text: str) -> str:
    code_keywords = ["def ", "SELECT ", "CREATE ", "import ", "if ", "while ", "class ", "try:"]
    is_code = any(kw in text for kw in code_keywords)
    if is_code:
        return f"```python\\n{text.strip()}\\n```"
    return text.strip()


def call_gemini(
    prompt: str,
    model_name: str | None = None,
    temperature: float = 0.5,
    max_output_tokens: int = 5000,
) -> str:
    selected_model = model_name or DEFAULT_GEMINI_MODEL

    def make_request():
        logger.info(f"Sending prompt to Gemini: {prompt[:80]}...")
        model = genai.GenerativeModel(selected_model)

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )

        if hasattr(response, "text") and response.text and response.text.strip():
            logger.info("Gemini response received.")
            return wrap_markdown(response.text)

        logger.warning("Gemini returned empty response.")
        return "Model returned an empty response."

    try:
        return _retry_call(make_request)
    except Exception as e:
        logger.error(f"Gemini API call failed after retries: {e}")
        return "Unable to process request at the moment. Please try again later."


def agent_response(prompt: str, agent_type: str = "code_reviewer") -> str:
    prefix_map = {
        "code_reviewer": "Please review the following code:\\n",
        "code_generator": "Generate code for the following instruction:\\n",
        "sql_translator": "Convert this into an SQL query:\\n",
    }
    full_prompt = prefix_map.get(agent_type, "") + prompt
    return call_gemini(full_prompt)
