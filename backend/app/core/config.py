from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    allowed_origins: str = "http://localhost:3000"
    max_upload_size: int = 50 * 1024 * 1024
    temp_file_ttl: int = 300
    rate_limit_requests: int = 60
    rate_limit_window: int = 3600
    conversion_timeout: int = 120
    temp_root: str = ""
    libreoffice_path: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [part.strip() for part in self.allowed_origins.split(",") if part.strip()]

    @property
    def storage_root(self) -> Path:
        return Path(self.temp_root) if self.temp_root else Path(__file__).resolve().parents[1] / "temp"


settings = Settings()
