"""Runtime configuration for the MCP server."""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    image_model: str = Field(default="gpt-image-1", alias="IMAGE_MODEL")
    image_output_dir: Path = Field(default=Path("storage/images"), alias="IMAGE_OUTPUT_DIR")
    image_base_url: str = Field(default="", alias="IMAGE_BASE_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
