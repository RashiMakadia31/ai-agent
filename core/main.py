import sys
import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from services.mysql_ext import router as mysql_router
from services.llm import call_gemini

# === Include project path ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# === Router & Service Imports ===
from routes.routes_chat import router as chat_router, agent as chat_agent
from core.commands import explain_code, fix_code, generate_code

# === Initialize app ===
app = FastAPI()

# === Security Middleware ===
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        return response

# === Mount routers ===
app.include_router(mysql_router, prefix="/sql")
app.include_router(chat_router)

# === Request models ===
class PromptInput(BaseModel):
    prompt: str
    language: str = "Python"

class SQLPrompt(BaseModel):
    prompt: str

class FolderAnalysisRequest(BaseModel):
    files: dict[str, str]

class ProjectContextRequest(BaseModel):
    folder_path: str

# === Code Assistant API Endpoints ===
@app.post("/explain")
async def explain_endpoint(file: UploadFile = File(...)):
    content = (await file.read()).decode()
    explanation = explain_code(content)
    return {"response": f"```markdown\n{explanation}\n```"}

@app.post("/fix")
async def fix_endpoint(file: UploadFile = File(...)):
    content = (await file.read()).decode()
    fixed = fix_code(content)
    return {"response": f"```python\n{fixed}\n```"}

@app.post("/generate")
def generate_endpoint(input_data: PromptInput):
    full_prompt = f"Write a {input_data.language} code that satisfies the following request:\n{input_data.prompt}"
    result = generate_code(full_prompt)
    return {"response": f"```{input_data.language.lower()}\n{result}\n```"}

@app.post("/ask-code")
async def ask_code(file: UploadFile = File(...), prompt: str = Form(...)):
    content = (await file.read()).decode()
    if "fix" in prompt.lower():
        result = fix_code(content)
        lang = "python"
    elif "generate" in prompt.lower():
        result = generate_code(prompt)
        lang = "python"
    else:
        result = explain_code(content)
        lang = "markdown"
    return {"response": f"```{lang}\n{result}\n```"}

# === SQL AI Endpoint using Gemini ===
@app.post("/sql/ask-ai")
async def ask_ai_sql(prompt_data: SQLPrompt):
    user_prompt = prompt_data.prompt.strip()
    if not user_prompt:
        return {"response": "âš ï¸ Prompt is empty. Please enter a valid question."}
    try:
        gemini_response = call_gemini(
            f"You are an AI MySQL assistant. Answer the following question based on the schema and database knowledge:\n\n{user_prompt}"
        )
        return {"response": gemini_response.strip()}
    except Exception as e:
        return {"response": f"âŒ Error processing request: {str(e)}"}

@app.post("/analyze-folder")
async def analyze_folder(_: FolderAnalysisRequest):
    # Placeholder endpoint used by the frontend folder workflow.
    return {}

@app.post("/load_project_context")
async def load_project_context(payload: ProjectContextRequest):
    # Placeholder endpoint used by the frontend folder workflow.
    return {
        "message": f"Project context load request received for: {payload.folder_path}",
        "thinking_log": []
    }

# === SSE Stream: Agentic Thinking Log ===
@app.get("/thinking-log")
async def thinking_log():
    async def stream():
        prev_len = 0
        keepalive_interval_secs = 15
        loop = asyncio.get_running_loop()
        next_keepalive_at = loop.time() + keepalive_interval_secs
        while not chat_agent.finished:
            new_logs = chat_agent.thinking_log[prev_len:]
            for entry in new_logs:
                yield f"data: {entry}\n\n"
            prev_len += len(new_logs)
            now = loop.time()
            if now >= next_keepalive_at:
                # SSE keepalive comment to keep proxies/load balancers from closing idle streams.
                yield ": keepalive\n\n"
                next_keepalive_at = now + keepalive_interval_secs
            await asyncio.sleep(0.5)

        # Send any remaining logs and end the stream
        remaining_logs = chat_agent.thinking_log[prev_len:]
        for entry in remaining_logs:
            yield f"data: {entry}\n\n"
        yield "data: âœ… Done\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# === Health Check ===
@app.get("/ping")
def ping():
    return {"message": "Server is live âœ…"}

# === Frontend Mount ===
frontend_path = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path, html=True), name="frontend")

# === Individual HTML Routes ===
@app.get("/login")
def serve_login():
    return FileResponse(frontend_path / "login.html")

@app.get("/register")
def serve_register():
    return FileResponse(frontend_path / "register.html")

@app.get("/index")
def serve_index():
    return FileResponse(frontend_path / "index.html")

@app.get("/")
def serve_root():
    return FileResponse(frontend_path / "index.html")

@app.get("/mysql-ui")
def serve_mysql_ui():
    return FileResponse(frontend_path / "mysql_assistant.html")

@app.get("/vscode-ui")
def serve_vscode_ui():
    return FileResponse(frontend_path / "vscode_assistant.html")

@app.get("/extension-ui")
def serve_extension_ui():
    return FileResponse(frontend_path / "extension_ui.html")

# === Middleware ===
def _get_cors_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "")
    if raw_origins.strip():
        parsed = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
        if parsed:
            return parsed
    return [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)

