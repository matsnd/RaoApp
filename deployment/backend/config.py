from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    RAO_DATABASE_URL: str = "mysql+aiomysql://rao_user:<<DB_PASSWORD_PLACEHOLDER>>@localhost:3306/rao_new"
    RAO_SECRET_KEY: str = "change-me"
    RAO_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    RAO_SMTP_HOST: str = "localhost"
    RAO_SMTP_PORT: int = 1025
    RAO_SMTP_USER: str = ""
    RAO_SMTP_PASSWORD: str = ""
    RAO_SMTP_FROM: str = "noreply@rao-app.pl"
    RAO_SMTP_TLS: bool = False
    RAO_FRONTEND_URL: str = "http://localhost:5173"
    RAO_GUS_API_KEY: str = ""
    RAO_NOMINATIM_BASE_URL: str = "https://nominatim.openstreetmap.org"
    RAO_CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:5174","http://localhost:5175"]'
    RAO_PDF_RENDERER: str = "weasyprint"
    # RAO-P2-012: Fernet key for Fakturownia API token encryption
    # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Must be 32 URL-safe base64-encoded bytes (44 chars). Empty = encryption disabled.
    RAO_FAKTUROWNIA_ENC_KEY: str = ""

    def get_cors_origins(self) -> List[str]:
        return json.loads(self.RAO_CORS_ORIGINS)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
