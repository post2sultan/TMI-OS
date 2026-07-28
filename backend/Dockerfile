FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends espeak-ng ffmpeg fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system tmi \
    && useradd --system --gid tmi --create-home tmi \
    && mkdir -p /app/media \
    && chown tmi:tmi /app/media

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /opt/kokoro \
    && python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx','/opt/kokoro/kokoro-v1.0.onnx'); urllib.request.urlretrieve('https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin','/opt/kokoro/voices-v1.0.bin')"

COPY --chown=tmi:tmi alembic.ini ./alembic.ini
COPY --chown=tmi:tmi alembic ./alembic
COPY --chown=tmi:tmi app ./app
COPY --chown=tmi:tmi prompts ./prompts

USER tmi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-server-header"]
