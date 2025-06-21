from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.routes_chat import router as chat_router

app = FastAPI()

# ✅ Allow frontend requests from localhost:5500 (your HTML app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],  # or ["*"] if testing more openly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Gemini-based chat route
app.include_router(chat_router)
