from pydantic_settings import BaseSettings, SettingsConfigDict
from decimal import Decimal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_TOPIC: str = "appointments.events"
    REDIS_URL: str
    CONSULTATION_FEE: Decimal = Decimal("100.00")


settings = Settings()
