from functools import lru_cache
from pathlib import Path
from typing import Literal

import openai
from pydantic import (
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    OPENAI_API_KEY: SecretStr = Field(
        ...,
        description="Project-scoped OpenAI API key starting with sk-.",
    )

    OPENAI_MODEL_WORKER: str = "gpt-4o-mini"
    OPENAI_MODEL_GUARDRAIL: str = "gpt-4o-mini"
    OPENAI_MODEL_ASTRA: str = "gpt-4o"

    OPENAI_TIMEOUT_SECONDS: float = Field(
        default=30.0,
        gt=0.0,
        le=120.0,
        description="Maximum seconds to wait for an OpenAI response before raising TimeoutError.",
    )

    OPENAI_MAX_TOKENS_WORKER: int = Field(
        default=2048,
        gt=0,
        le=16384,
        description="Hard output token ceiling for worker and synthesis agents.",
    )

    OPENAI_MAX_TOKENS_GUARDRAIL: int = Field(
        default=512,
        gt=0,
        le=2048,
        description="Hard output token ceiling for guardrail and routing checks.",
    )

    DATABASE_URL: SecretStr = Field(
        default=SecretStr(
            "postgresql+asyncpg://postgres:postgres@localhost:5434/planmytrip"
        ),
        description="Async SQLAlchemy database connection string.",
    )

    DATABASE_POOL_MIN: int = Field(
        default=5,
        ge=1,
        description="Minimum active connections maintained in the async pool.",
    )

    DATABASE_POOL_MAX: int = Field(
        default=20,
        ge=5,
        description="Maximum concurrent connections permitted before queuing.",
    )

    REDIS_URL: SecretStr = Field(
        default=SecretStr("redis://localhost:6380/0"),
        description="Redis connection URI for circuit breakers and response caching.",
    )

    AVIATIONSTACK_API_KEY: SecretStr | None = Field(
        default=None,
        description="Optional AviationStack key for real-time flight telemetry.",
    )

    OPENWEATHER_API_KEY: SecretStr | None = Field(
        default=None,
        description="Optional OpenWeather key for forecast data.",
    )

    TAVILY_API_KEY: SecretStr | None = Field(
        default=None,
        description="Tavily search API key for travel context and indicative pricing.",
    )

    JWT_SECRET: SecretStr = Field(
        ...,
        min_length=32,
        description="Cryptographic secret used to sign HS256 authentication tokens.",
    )

    JWT_ALGORITHM: str = "HS256"

    JWT_EXPIRE_MINUTES: int = Field(
        default=43200,
        ge=5,
        description="Access token lifespan in minutes.",
    )

    MCP_FLIGHT_URL: str = "http://localhost:8001"
    MCP_WEATHER_URL: str = "http://localhost:8002"
    MCP_PLACES_URL: str = "http://localhost:8003"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()

        if not raw:
            raise ValueError("OPENAI_API_KEY cannot be empty.")

        if not raw.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'.")

        return value

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value().strip()

        if len(raw) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long.")

        return value

    @model_validator(mode="after")
    def validate_pool_bounds(self) -> "Settings":
        if self.DATABASE_POOL_MAX < self.DATABASE_POOL_MIN:
            raise ValueError(
                f"DATABASE_POOL_MAX ({self.DATABASE_POOL_MAX}) must be greater than "
                f"or equal to DATABASE_POOL_MIN ({self.DATABASE_POOL_MIN})."
            )

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def get_openai_client() -> openai.AsyncOpenAI:
    settings = get_settings()

    return openai.AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY.get_secret_value(),
        timeout=settings.OPENAI_TIMEOUT_SECONDS,
        max_retries=2,
    )


async def validate_openai_credentials() -> None:
    client = get_openai_client()
    settings = get_settings()

    try:
        await client.chat.completions.create(
            model=settings.OPENAI_MODEL_GUARDRAIL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            temperature=0.0,
        )

    except openai.AuthenticationError as err:
        raise RuntimeError(
            f"OpenAI Authentication Failed during startup: {err}"
        ) from err

    except openai.RateLimitError as err:
        raise RuntimeError(
            f"OpenAI Quota Exceeded during startup: {err}"
        ) from err

    except Exception as err:
        raise RuntimeError(
            f"OpenAI Startup Probe Failed ({type(err).__name__}): {err}"
        ) from err