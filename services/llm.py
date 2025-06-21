import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# ✅ Load environment variables from .env file
load_dotenv()

# ✅ Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Fetch Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY not found in environment. Check your .env file.")
    raise EnvironmentError("Missing GEMINI_API_KEY in environment variables.")

# ✅ Configure the Gemini API with the key
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Core function to send a prompt to Gemini and return the response
def call_gemini(prompt: str, model_name: str = "gemini-1.5-flash", temperature: float = 0.5) -> str:
    """
    Sends a prompt to the Gemini LLM and retrieves its response.

    Args:
        prompt (str): The input prompt to send.
        model_name (str): The Gemini model variant to use.
        temperature (float): Sampling temperature for creativity.

    Returns:
        str: The LLM-generated response text.
    """
    try:
        logger.info(f"📤 Sending prompt to Gemini: {prompt[:80]}...")  # Log first 80 chars for brevity
        model = genai.GenerativeModel(model_name)

        # Send prompt to Gemini
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature
            )
        )

        if response.parts:
            # Extract and clean the LLM's output text
            output = response.text.strip()
            logger.info("✅ Gemini response received.")

            # (Optional) Auto-wrap code if desired — currently commented out
            # if "```" not in output:
            #     code_keywords = [
            #         "def ", "class ", "import ", "print(", "if ", "else:", "elif ", 
            #         "for ", "while ", "return ", "try:", "except ", "public ", 
            #         "private ", "void ", "function "
            #     ]
            #     if any(kw in output for kw in code_keywords):
            #         output = f"```python\n{output}\n```"

            return output
        else:
            # Empty response edge case
            logger.warning("⚠️ Gemini returned empty response.")
            return ""

    except Exception as e:
        logger.error(f"❌ Gemini API call failed: {e}")
        raise RuntimeError("Gemini API call failed")

# ✅ Wrapper function to prepend specific agent instructions to the prompt
def agent_response(prompt: str, agent_type: str = "code_reviewer") -> str:
    """
    Provides an agent-specific response by modifying the prompt context.

    Args:
        prompt (str): User's prompt or code to process.
        agent_type (str): Type of agent (e.g., code_reviewer, code_generator, sql_translator).

    Returns:
        str: LLM-generated response text.
    """
    # Define prefix instructions for different agent types
    prefix_map = {
        "code_reviewer": "Please review the following code:\n",
        "code_generator": "Generate code for the following instruction:\n",
        "sql_translator": "Convert this into an SQL query:\n"
    }
    # Compose the full prompt
    full_prompt = prefix_map.get(agent_type, "") + prompt

    # Call Gemini using the composed prompt
    return call_gemini(full_prompt)