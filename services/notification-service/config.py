from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    DATABASE_URL: str


settings = Settings()
