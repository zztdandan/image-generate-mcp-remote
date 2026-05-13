# image-generate-mcp-remote

Remote MCP server for image generation, built with UV + Python.

> Use the workspace root `.venv` via `UV_PROJECT_ENVIRONMENT=../.venv` when running UV commands from this subproject.

## Quick start

```bash
uv sync
cp .env.example .env
# fill the IMG_GEN_* API keys you need
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

- `list_image_tools_catalog`: report defaults, env surface, and effective non-secret config
- `gpt_image_2_official`: OpenAI Images compatible generate/edit tool
- `nano_banana_2_official`: Gemini generateContent compatible generate/edit tool

## Environment

- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY`
- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_BASE_URL`
- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_MODEL`
- `IMG_GEN_GPT_IMAGE_2_OFFICIAL_SUPPORTED_MODELS`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_BASE_URL`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_MODEL`
- `IMG_GEN_NANO_BANANA_2_OFFICIAL_SUPPORTED_MODELS`
- `IMAGE_OUTPUT_DIR`
- `IMAGE_BASE_URL`
- `LOG_LEVEL`
