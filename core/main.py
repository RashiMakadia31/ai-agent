from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

import os
from routes.routes_chat import router as chat_router
from services.vscode_ext import router as vscode_router
from services.mysql_ext import router as mysql_router
from core.commands import explain_code, fix_code, generate_code

app = FastAPI()

# === Security Headers Middleware ===
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

# === Mount static files ===
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# === Routers ===
app.include_router(vscode_router, prefix="/vscode")
app.include_router(mysql_router, prefix="/sql")
app.include_router(chat_router)

# === Frontend Routes ===
@app.get("/")
def serve_main_ui():
    return FileResponse(os.path.join("frontend", "extension_ui.html"))

@app.get("/vscode-ui")
def serve_vscode_ui():
    return FileResponse(os.path.join("frontend", "vscode_assistant.html"))

@app.get("/mysql-ui")
def serve_mysql_ui():
    return FileResponse(os.path.join("frontend", "mysql_assistant.html"))

@app.get("/login")
def serve_login():
    return FileResponse(os.path.join("frontend", "login.html"))

@app.get("/index")
def serve_index():
    return FileResponse(os.path.join("frontend", "index.html"))

# === Models ===
class PromptInput(BaseModel):
    prompt: str
    language: str = "Python"

# === API Endpoints ===
@app.post("/explain")
async def explain_endpoint(file: UploadFile = File(...)):
    content = (await file.read()).decode()
    explanation = explain_code(content)
    return {
        "response": f"```markdown\n{explanation}\n```"
    }

@app.post("/fix")
async def fix_endpoint(file: UploadFile = File(...)):
    content = (await file.read()).decode()
    fixed = fix_code(content)
    return {
        "response": f"```python\n{fixed}\n```"
    }

@app.post("/generate")
def generate_endpoint(input_data: PromptInput):
    full_prompt = f"Write a {input_data.language} code that satisfies the following request:\n{input_data.prompt}"
    result = generate_code(full_prompt)
    return {
        "response": f"```{input_data.language.lower()}\n{result}\n```"
    }

@app.post("/ask-code")
async def ask_code(file: UploadFile = File(...), prompt: str = Form(...)):
    content = (await file.read()).decode()
    if "fix" in prompt.lower():
        result = fix_code(content)
        lang = "python"
    elif "generate" in prompt.lower():
        result = generate_code(prompt)
        lang = "python"  # Or infer if you want
    else:
        result = explain_code(content)
        lang = "markdown"
    return {
        "response": f"```{lang}\n{result}\n```"
    }

# === Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
