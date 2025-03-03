FROM python:3.13

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=1
ENV PYTHONFAULTHANDLER=1

WORKDIR /app
COPY . /app
RUN uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "-m", "mastodon_update_bot"]
