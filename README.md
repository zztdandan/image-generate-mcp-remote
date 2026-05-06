# image-generate-mcp-remote

Remote MCP server for image generation, built with UV + Python.

## Quick start

```bash
uv sync
cp .env.example .env
# fill OPENAI_API_KEY
uv run image-generate-mcp-remote --help
```

## Run

```bash
# stdio
uv run image-generate-mcp-remote

# HTTP
uv run image-generate-mcp-remote --transport streamable-http --host 127.0.0.1 --port 3001

# SSE
uv run image-generate-mcp-remote --transport sse --host 127.0.0.1 --port 3001
```

## Tools

- `health_check`: report server status
- `generate_image`: generate an image with OpenAI Images API and save locally
