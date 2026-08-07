from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    DATABASE_URL: str
    PATIENT_KAFKA_TOPIC: str = "patients.events"
    PROVIDER_KAFKA_TOPIC: str = "providers.events"
    APPOINTMENT_KAFKA_TOPIC: str = "appointments.events"
    AI_KAFKA_TOPIC: str = "ai.events"
    KAFKA_BOOTSTRAP_SERVERS: str
    AUTH_SERVICE_URL: str
    SYSTEM_EMAIL: str
    SYSTEM_PASSWORD: str
    PROVIDER_SERVICE_URL: str
    APPOINTMENT_SERVICE_URL: str
    PATIENT_SERVICE_URL: str
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    TEMPORAL_HOST: str
    TEMPORAL_NAMESPACE: str = "default"
    REMINDER_TASK_QUEUE: str = "appointment_reminder_queue"

settings = Settings()
