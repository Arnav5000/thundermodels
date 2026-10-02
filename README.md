# Thunder Models

Small Render-ready model gateway for Thunder AI CRM. It exposes an OpenAI-compatible chat endpoint while keeping model management separate from the CRM application.

## Why this model

The default is `bartowski/Llama-3.2-1B-Instruct-GGUF` with `Llama-3.2-1B-Instruct-Q4_K_M.gguf`. It is an instruction/chat model and is a better fit for the assistant than `all-MiniLM-L6-v2`, which is an embedding model. TinyLlama can be selected without code changes:

```text
MODEL_REPO_ID=TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
MODEL_FILENAME=tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

## Download-once behavior

At startup the service checks `MODEL_DIR/MODEL_FILENAME`. If a valid file is already there, it does not download it again. Otherwise it downloads the configured file from Hugging Face into that directory. On Render, mount a persistent disk at `/var/data` and use `MODEL_DIR=/var/data/models`.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 10000
```

Health: `GET /health`

Models: `GET /v1/models`

Chat: `POST /v1/chat/completions`

The API accepts `Authorization: Bearer <MODEL_API_KEY>` when `MODEL_API_KEY` is configured. Keep that key private and configure the same key in ThunderAI-CRM.
