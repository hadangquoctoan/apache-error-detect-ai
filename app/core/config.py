# Core Configuration
import os
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class LLMGeminiSettings(BaseSettings):
    """Gemini configuration."""
    api_key: str = Field(default="", alias="GEMINI_API_KEY")
    model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")
    temperature: float = Field(default=0.0, alias="GEMINI_TEMPERATURE")
    max_tokens: int = Field(default=2048, alias="GEMINI_MAX_TOKENS")

    class Config:
        env_file = ".env"
        extra = "ignore"


class LLMOpenAISettings(BaseSettings):
    """OpenAI configuration."""
    api_key: str = Field(default="", alias="OPENAI_API_KEY")
    model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_MODEL")
    temperature: float = Field(default=0.0, alias="OPENAI_TEMPERATURE")
    max_tokens: int = Field(default=2048, alias="OPENAI_MAX_TOKENS")

    class Config:
        env_file = ".env"
        extra = "ignore"


class LLMAnthropicSettings(BaseSettings):
    """Anthropic configuration."""
    api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    model: str = Field(default="claude-3-opus-20240229", alias="ANTHROPIC_MODEL")
    max_tokens: int = Field(default=2048, alias="ANTHROPIC_MAX_TOKENS")

    class Config:
        env_file = ".env"
        extra = "ignore"


class LLMSettings(BaseSettings):
    """Common LLM configuration."""
    provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    gemini: LLMGeminiSettings = LLMGeminiSettings()
    openai: LLMOpenAISettings = LLMOpenAISettings()
    anthropic: LLMAnthropicSettings = LLMAnthropicSettings()

    class Config:
        env_file = ".env"
        extra = "ignore"


class LokiSettings(BaseSettings):
    """Loki configuration."""
    host: str = Field(default="loki", alias="LOKI_HOST")
    port: int = Field(default=3100, alias="LOKI_PORT")
    base_url: str = Field(default="http://loki:3100", alias="LOKI_BASE_URL")
    max_lines: int = Field(default=1000, alias="LOKI_MAX_LINES")
    query_timeout: int = Field(default=60, alias="LOKI_QUERY_TIMEOUT")

    class Config:
        env_file = ".env"
        extra = "ignore"


class RedisSettings(BaseSettings):
    """Redis configuration."""
    host: str = Field(default="redis", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    db: int = Field(default=0, alias="REDIS_DB")

    class Config:
        env_file = ".env"
        extra = "ignore"


class AnalysisSettings(BaseSettings):
    """Analysis configuration."""
    max_logs_per_request: int = Field(default=500, alias="MAX_LOGS_PER_ANALYSIS")
    timeout: int = Field(default=120, alias="ANALYSIS_TIMEOUT")
    streaming_enabled: bool = Field(default=True, alias="STREAMING_ENABLED")

    class Config:
        env_file = ".env"
        extra = "ignore"


class APISettings(BaseSettings):
    """API configuration."""
    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    workers: int = Field(default=4, alias="API_WORKERS")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], alias="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        extra = "ignore"


class AppSettings(BaseSettings):
    """Application configuration."""
    env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        extra = "ignore"


class Settings(BaseSettings):
    """Primary application settings."""
    app: AppSettings = AppSettings()
    loki: LokiSettings = LokiSettings()
    llm: LLMSettings = LLMSettings()
    redis: RedisSettings = RedisSettings()
    analysis: AnalysisSettings = AnalysisSettings()
    api: APISettings = APISettings()

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()


# Global settings instance
settings = get_settings()
