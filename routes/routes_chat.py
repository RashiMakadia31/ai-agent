from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.llm import call_gemini
import logging

# Initialize FastAPI router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# Request model defining the expected input JSON body for /chat endpoint
class PromptRequest(BaseModel):
    prompt: str  # The user's natural language prompt or question
    language: str = "Python"  # Target programming language (default: Python)
    code: str = ""  # Optional code snippet sent from frontend

# Response model defining the structure of response JSON
class PromptResponse(BaseModel):
    response: str  # LLM's response (possibly wrapped in code formatting)

# Helper function to auto-wrap response in code block if it looks like code
def auto_wrap_code(answer: str, lang: str) -> str:
    """
    Auto-wraps the LLM answer in a markdown code block if code patterns are detected
    and not already wrapped.
    """
    if "```" in answer:
        # If already contains code block markers, return as-is
        return answer
    
    # List of keywords indicative of code
    code_keywords = [
        "def ", "class ", "import ", "print(", "if ", "else:", "elif ",
        "for ", "while ", "return ", "try:", "except ", "public ",
        "private ", "void ", "function ", "SELECT ", "from pyspark"
    ]
    
    # If any code-like keyword found, wrap the answer in code block
    if any(kw in answer for kw in code_keywords):
        return f"```{lang.lower()}\n{answer.strip()}\n```"
    
    # Otherwise, return as-is
    return answer

# Route to handle chat requests using Gemini LLM
@router.post("/chat", response_model=PromptResponse)
async def chat_with_gemini(request: PromptRequest):
    """
    Processes chat requests, composes a prompt for Gemini, 
    calls the LLM service, and returns a formatted response.
    """
    try:
        # Log input prompt details
        logger.info(f"📥 Prompt: {request.prompt} | Lang: {request.language} | Code size: {len(request.code)} chars")

        prompt_lower = request.prompt.lower()
        lang = request.language

        # Compose full prompt based on intent detected in user's prompt
        if request.code.strip() and ("debug" in prompt_lower or "fix" in prompt_lower):
            # User likely wants code debugging / fixing
            full_prompt = (
                f"Please debug and correct this {lang} code. "
                f"Provide corrected code and brief explanation if needed.\n\n"
                f"{request.code}"
            )
        elif request.code.strip() and ("explain" in prompt_lower or "describe" in prompt_lower):
            # User likely wants code explanation
            full_prompt = (
                f"Please explain the following {lang} code in detail:\n\n{request.code}"
            )
        elif "generate" in prompt_lower or "write" in prompt_lower or "script" in prompt_lower:
            # User likely wants new code generation
            full_prompt = (
                f"Write a {lang} code that satisfies this request:\n{request.prompt}"
            )
        else:
            # General case: combine code and prompt if code exists
            if request.code.strip():
                full_prompt = (
                    f"Considering the following {lang} code:\n{request.code}\n\n"
                    f"{request.prompt}"
                )
            else:
                full_prompt = (
                    f"Provide a response in {lang} for the following request:\n{request.prompt}"
                )

        # Log the composed prompt (trimmed for brevity)
        logger.info(f"📤 Sending composed prompt to Gemini: {full_prompt[:150]}...")

        # Call the LLM service (synchronously)
        answer = call_gemini(full_prompt)

        # Wrap response in code block if applicable
        wrapped = auto_wrap_code(answer, lang)

        # Return structured response
        return PromptResponse(response=wrapped)

    except Exception as e:
        # Handle and log unexpected errors
        logger.error(f"❌ Gemini chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get response from Gemini")
