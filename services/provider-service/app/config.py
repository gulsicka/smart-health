from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_TOPIC: str = "providers.events"
    USERS_KAFKA_TOPIC: str = "users.events"
    

settings = Settings()
