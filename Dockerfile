FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install --only-binary=llama-cpp-python \
       --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu \
       -r requirements.txt

COPY app ./app
RUN mkdir -p /var/data/models

EXPOSE 10000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
