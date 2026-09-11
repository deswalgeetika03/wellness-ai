from typing import Any
import time
import os

from fastapi import FastAPI, HTTPException
import requests
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from query_pipeline import OLLAMA_URL, answer_query, get_vector_db

CORS_ORIGINS = os.getenv(
    "WELLNESS_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
).split(",")

app = FastAPI(title="Wellness AI API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,

    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class ChatRequest(BaseModel):
    question: str = Field(max_length=2000)
    history: list[dict[str, Any]] = []


class ChatResponse(BaseModel):
    route: str | None = None
    answer: str
    sources: list[Any] = []
    context_chunks: list[Any] = []


_vector_db = None


def get_backend():
    global _vector_db

    if _vector_db is None:
        start = time.perf_counter()

        _vector_db = get_vector_db()

        elapsed = time.perf_counter() - start

        print(
            f"\n[PERFORMANCE] Backend initialization: "
            f"{elapsed:.3f}s\n"
        )

    return _vector_db


@app.get("/api/health")
def health():
    try:
        ollama_base_url = OLLAMA_URL.rsplit("/api/generate", 1)[0]

        response = requests.get(
           f"{ollama_base_url}/api/tags",
           timeout=2,
        )

        if response.ok:
            return {
                "status": "ok",
                "service": "Wellness AI API",
                "ollama": "ok",
            }

        return {
            "status": "degraded",
            "service": "Wellness AI API",
            "ollama": "unavailable",
        }

    except requests.RequestException:
        return {
            "status": "degraded",
            "service": "Wellness AI API",
            "ollama": "unavailable",
        }

@app.on_event("startup")
def startup_event():
    get_backend()

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        return ChatResponse(
            route="empty",
            answer="Please enter a question.",
        )

    try:
        vector_db = get_backend()

        result = answer_query(
            vector_db,
            question,
            history=request.history,
        )

        return ChatResponse(
            route=result.get("route"),
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            context_chunks=result.get("context_chunks", []),
        )

    except Exception as error:
        print(
            f"[ERROR] Chat request failed: "
            f"{type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=503,
            detail="Wellness AI is temporarily unavailable. Please try again.",
        )
