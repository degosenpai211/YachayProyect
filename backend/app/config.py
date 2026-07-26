from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    groq_api_key: str = ""
    zavu_api_key: str = ""
    zavu_webhook_secret: str = ""
    zavu_send_url: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    exa_api_key: str = ""
    exa_enabled: bool = False
    database_url: str = "sqlite:///./yachay.db"
    demo_mode: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    telegram_bot_username: str = "YachayBot"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def has_claude(self) -> bool:
        return bool(self.anthropic_api_key.strip())

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key.strip())

    @property
    def has_elevenlabs(self) -> bool:
        return bool(self.elevenlabs_api_key.strip())

    @property
    def has_exa(self) -> bool:
        return self.exa_enabled and bool(self.exa_api_key.strip())

    @property
    def has_zavu(self) -> bool:
        return bool(self.zavu_api_key.strip() and self.zavu_send_url.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
