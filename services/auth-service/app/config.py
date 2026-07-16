from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TEMPORAL_HOST: str
    TEMPORAL_NAMESPACE: str = "default"
    USER_TASK_QUEUE: str
    REDIS_URL: str
    UPDATE_USER_ROLE_TASK_QUEUE: str


settings = Settings()
