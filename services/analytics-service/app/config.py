from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_TOPIC: str
    PATIENT_KAFKA_TOPIC: str
    AI_KAFKA_TOPIC: str = "ai.events"
    REDIS_URL: str
    RABBITMQ_URL: str
    DATABASE_URL: str


settings = Settings()
