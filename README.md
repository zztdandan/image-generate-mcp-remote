# image-generate-mcp-remote

Remote MCP server for image generation, built with UV + Python.

> Use the workspace root `.venv` via `UV_PROJECT_ENVIRONMENT=../.venv` when running UV commands from this subproject.

## Quick start

```bash
uv sync
cp .env.example .env
# fill OPENAI_API_KEY
uv run image-generate-mcp-remote --help
```

## Run

```bash
# Remote HTTP (default transport is streamable-http)
uv run image-generate-mcp-remote --transport streamable-http --host 127.0.0.1 --port 3001

# Remote SSE
uv run image-generate-mcp-remote --transport sse --host 127.0.0.1 --port 3001

# Local stdio (debug / compatibility only)
uv run image-generate-mcp-remote --transport stdio
```

## Tools

- `health_check`: report server status
- `generate_image`: generate an image with OpenAI Images API and save locally
