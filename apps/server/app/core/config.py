from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    EVOLUTION_API_URL: str
    EVOLUTION_API_KEY: str
    EVOLUTION_INSTANCE: str
    MAX_RETRIES: int = 3
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
