from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_PORT: int = 8000
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    RATE_LIMIT_THRESHOLD: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    EXTERNAL_SERVICE_FAILURE_RATE: float = 0.5
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_RESET_TIMEOUT: int = 10
    CACHE_DEFAULT_TTL: int = 60

    class Config:
        env_file = ".env"

settings = Settings()