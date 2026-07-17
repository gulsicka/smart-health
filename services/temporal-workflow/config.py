from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TEMPORAL_HOST: str
    TEMPORAL_NAMESPACE: str = "default"
    AUTH_SERVICE_URL: str
    PATIENT_SERVICE_URL: str
    PROVIDER_SERVICE_URL: str
    APPOINTMENT_SERVICE_URL: str
    SYSTEM_EMAIL: str
    SYSTEM_PASSWORD: str
    USER_TASK_QUEUE: str
    UPDATE_USER_ROLE_TASK_QUEUE: str
    APPOINTMENT_TASK_QUEUE: str
    RABBITMQ_URL: str


settings = Settings()
