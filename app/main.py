"""OpenAI-compatible API for a small local GGUF model."""
from contextlib import asynccontextmanager
from datetime import UTC, datetime
import secrets
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .config import Settings
from .model_manager import ModelManager

settings = Settings.from_env()
manager = ModelManager(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    manager.start()
    yield


app = FastAPI(title="Thunder Models", version="1.0.0", lifespan=lifespan)


class Message(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[Message] = Field(min_length=1, max_length=40)
    max_tokens: int | None = Field(default=None, ge=1, le=2048)
    temperature: float = Field(default=0.25, ge=0, le=2)
    stream: bool = False


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    expected = settings.model_api_key
    if not expected:
        return
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid model API key")


@app.get("/")
def index() -> dict[str, str]:
    return {"service": "thunder-models", "health": "/health", "chat": "/v1/chat/completions"}


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "service": "thunder-models",
        "checked_at": datetime.now(UTC).isoformat(),
        **manager.status(),
    }


@app.get("/v1/models", dependencies=[Depends(require_api_key)])
def models() -> dict[str, Any]:
    return {
        "object": "list",
        "data": [{"id": settings.model_filename, "object": "model", "owned_by": "thunder"}],
    }


@app.post("/v1/chat/completions", dependencies=[Depends(require_api_key)])
def chat(payload: ChatRequest) -> dict[str, Any]:
    if payload.stream:
        raise HTTPException(status_code=400, detail="Streaming is not enabled; use stream=false")
    model = manager.get_model()
    if model is None:
        raise HTTPException(status_code=503, detail=manager.status())
    messages = [{"role": item.role, "content": item.content} for item in payload.messages]
    try:
        result = model.create_chat_completion(
            messages=messages,
            max_tokens=payload.max_tokens or settings.default_max_tokens,
            temperature=payload.temperature,
        )
        content = result["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model generation failed: {exc}") from exc
    return {
        "id": f"chatcmpl-{uuid4().hex}",
        "object": "chat.completion",
        "created": int(datetime.now(UTC).timestamp()),
        "model": payload.model or settings.model_filename,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
