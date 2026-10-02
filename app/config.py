"""Environment-backed configuration for the model service."""
from dataclasses import dataclass
import os
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    model_repo_id: str
    model_filename: str
    model_revision: str
    model_dir: Path
    model_api_key: str
    download_on_start: bool
    context_size: int
    threads: int
    default_max_tokens: int
    request_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            model_repo_id=os.getenv(
                "MODEL_REPO_ID", "bartowski/Llama-3.2-1B-Instruct-GGUF"
            ),
            model_filename=os.getenv(
                "MODEL_FILENAME", "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
            ),
            model_revision=os.getenv("MODEL_REVISION", "main"),
            model_dir=Path(os.getenv("MODEL_DIR", "models")),
            model_api_key=os.getenv("MODEL_API_KEY", "").strip(),
            download_on_start=_bool("MODEL_DOWNLOAD_ON_START", True),
            context_size=max(512, _int("MODEL_CONTEXT_SIZE", 2048)),
            threads=max(1, _int("MODEL_THREADS", 4)),
            default_max_tokens=max(32, _int("MODEL_MAX_TOKENS", 256)),
            request_timeout_seconds=max(5, _int("MODEL_REQUEST_TIMEOUT", 120)),
        )
