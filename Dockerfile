FROM astral/uv:python3.11-bookworm-slim

COPY . .
# Disable development dependencies
ENV UV_NO_DEV=1
# Install requirements
RUN uv sync --locked

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

