FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app

ENV UV_NO_DEV=1

WORKDIR /app

RUN uv sync --locked

CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]
