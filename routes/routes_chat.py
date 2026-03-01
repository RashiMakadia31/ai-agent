from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.llm import call_gemini
from agents.master_agent import MasterAgent
import logging

# Initialize FastAPI router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# Create a singleton MasterAgent instance
agent = MasterAgent()

# Request model
class PromptRequest(BaseModel):
    prompt: str
    language: str = "Python"
    code: str = ""
    use_agent: bool = True  # Optional toggle to enable/disable agentic behavior

# Response model
class PromptResponse(BaseModel):
    response: str

# Helper function to auto-wrap response in code block if it looks like code
def auto_wrap_code(answer: str, lang: str) -> str:
    """
    Auto-wraps the LLM answer in a markdown code block if code patterns are detected
    and not already wrapped.
    """
    if "```" in answer:
        return answer

    code_keywords = [
        "def ", "class ", "import ", "print(", "if ", "else:", "elif ",
        "for ", "while ", "return ", "try:", "except ", "public ",
        "private ", "void ", "function ", "SELECT ", "from pyspark"
    ]
    if any(kw in answer for kw in code_keywords):
        return f"```{lang.lower()}\n{answer.strip()}\n```"

    return answer

# Route to handle chat requests with optional agentic processing
@router.post("/chat", response_model=PromptResponse)
async def chat_with_gemini(request: PromptRequest):
    """
    Processes chat requests. If use_agent=True, routes through MasterAgent
    for agentic behavior (ethics check, judgment, explanation, comments).
    Otherwise, uses the original Gemini logic.
    """
    try:
        logger.info(f"ðŸ“¥ Prompt: {request.prompt} | Lang: {request.language} | Code size: {len(request.code)} chars")

        if request.use_agent:
            # Use MasterAgent for agentic response
            user_code_example = request.code.strip() if request.code else None
            result = agent.run(prompt=request.prompt, user_code_example=user_code_example)
            return PromptResponse(response=result["response"])

        # === Fallback: Original Gemini logic (non-agentic path) ===
        prompt_lower = request.prompt.lower()
        lang = request.language

        if request.code.strip() and ("debug" in prompt_lower or "fix" in prompt_lower):
            full_prompt = (
                f"Please debug and correct this {lang} code. "
                f"Provide corrected code and brief explanation if needed.\n\n"
                f"{request.code}"
            )
        elif request.code.strip() and ("explain" in prompt_lower or "describe" in prompt_lower):
            full_prompt = f"Please explain the following {lang} code in detail:\n\n{request.code}"
        elif "generate" in prompt_lower or "write" in prompt_lower or "script" in prompt_lower:
            full_prompt = f"Write a {lang} code that satisfies this request:\n{request.prompt}"
        else:
            if request.code.strip():
                full_prompt = (
                    f"Considering the following {lang} code:\n{request.code}\n\n{request.prompt}"
                )
            else:
                full_prompt = f"Provide a response in {lang} for the following request:\n{request.prompt}"

        logger.info(f"ðŸ“¤ Sending composed prompt to Gemini: {full_prompt[:150]}...")

        answer = call_gemini(full_prompt)
        wrapped = auto_wrap_code(answer, lang)
        return PromptResponse(response=wrapped)

    except Exception as e:
        logger.error(f"âŒ Gemini chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get response from Gemini")

