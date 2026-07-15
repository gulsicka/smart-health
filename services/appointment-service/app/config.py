from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    TEMPORAL_HOST: str
    TEMPORAL_NAMESPACE: str = "default"
    APPOINTMENT_TASK_QUEUE: str
    KAFKA_BOOTSTRAP_SERVERS : str
    KAFKA_TOPIC: str


settings = Settings()
