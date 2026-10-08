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
    SECRET_KEY: str
    PATIENT_SERVICE_URL: str = "http://patient-service:8000"
    PROVIDER_SERVICE_URL: str = "http://provider-service:8000"
    ALGORITHM: str = "HS256"


settings = Settings()
