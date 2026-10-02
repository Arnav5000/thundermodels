"""Download-once and lazy-load management for a single GGUF model."""
from __future__ import annotations

import importlib.util
import shutil
import threading
from pathlib import Path
from typing import Any

from .config import Settings


class ModelManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._model: Any = None
        self._model_path: Path | None = None
        self._download_error: str | None = None
        self._downloading = False
        self._download_lock = threading.Lock()
        self._load_lock = threading.Lock()

    @property
    def expected_path(self) -> Path:
        return self.settings.model_dir / self.settings.model_filename

    def _runtime_available(self) -> bool:
        return importlib.util.find_spec("llama_cpp") is not None

    def status(self) -> dict[str, Any]:
        path = self.expected_path
        file_exists = path.is_file() and path.stat().st_size > 1024 * 1024
        runtime_available = self._runtime_available()
        if self._downloading:
            label = "Downloading model"
        elif self._download_error:
            label = "Model download needs attention"
        elif file_exists and runtime_available:
            label = "Model ready"
        elif file_exists:
            label = "Model downloaded; runtime unavailable"
        else:
            label = "Model not downloaded"
        return {
            "service_ready": True,
            "model_ready": bool(file_exists and runtime_available),
            "model_loaded": self._model is not None,
            "model_file": file_exists,
            "runtime_available": runtime_available,
            "downloading": self._downloading,
            "download_error": self._download_error,
            "label": label,
            "repo_id": self.settings.model_repo_id,
            "filename": self.settings.model_filename,
        }

    def start(self) -> None:
        self.settings.model_dir.mkdir(parents=True, exist_ok=True)
        if self.settings.download_on_start and not self.expected_path.is_file():
            thread = threading.Thread(target=self.download_if_missing, daemon=True)
            thread.start()

    def download_if_missing(self) -> Path | None:
        self.settings.model_dir.mkdir(parents=True, exist_ok=True)
        with self._download_lock:
            if self.expected_path.is_file() and self.expected_path.stat().st_size > 1024 * 1024:
                return self.expected_path
            if self._downloading:
                return None
            self._downloading = True
            self._download_error = None
            try:
                from huggingface_hub import hf_hub_download

                downloaded = hf_hub_download(
                    repo_id=self.settings.model_repo_id,
                    filename=self.settings.model_filename,
                    revision=self.settings.model_revision,
                    local_dir=str(self.settings.model_dir),
                )
                downloaded_path = Path(downloaded)
                if downloaded_path.resolve() != self.expected_path.resolve():
                    shutil.copyfile(downloaded_path, self.expected_path)
                return self.expected_path
            except Exception as exc:  # download failures must not kill the API
                self._download_error = str(exc)[:500]
                return None
            finally:
                self._downloading = False

    def get_model(self) -> Any | None:
        path = self.expected_path
        if not path.is_file() or path.stat().st_size <= 1024 * 1024:
            path = self.download_if_missing()
        if path is None or not self._runtime_available():
            return None
        with self._load_lock:
            if self._model is not None and self._model_path == path:
                return self._model
            try:
                from llama_cpp import Llama

                self._model = Llama(
                    model_path=str(path),
                    n_ctx=self.settings.context_size,
                    n_threads=self.settings.threads,
                    verbose=False,
                )
                self._model_path = path
                return self._model
            except Exception as exc:
                self._model = None
                self._model_path = None
                self._download_error = f"Model load failed: {exc}"[:500]
                return None
