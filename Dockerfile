FROM astral/uv:python3.11-bookworm-slim
# Setup UV
COPY . .

# Disable development dependencies
ENV UV_NO_DEV=1
#install requirements
RUN uv sync --locked


CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

