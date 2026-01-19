from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # TELEGRAM
    API_ID: int
    API_HASH: str
    PHONE_NUMBER: str
    ADMIN_USER: str

    # UAZAPI
    WA_INSTANCE_TOKEN: str
    WA_TARGET_NUMBER: str
    WA_BASE_URL: str

    # IA
    GROQ_API_KEY: str
    GEMINI_API_KEY: Optional[str] = None

    # AFILIADOS
    AMAZON_TAG: Optional[str] = None

    # TWITTER
    X_API_KEY: Optional[str] = None
    X_API_SECRET: Optional[str] = None
    X_ACCESS_TOKEN: Optional[str] = None
    X_ACCESS_TOKEN_SECRET: Optional[str] = None
    X_BEARER_TOKEN: Optional[str] = None
    X_CLIENT_ID: Optional[str] = None
    X_CLIENT_SECRET: Optional[str] = None
    LIMITE_DIARIO_X: int = 15

    # LOJAS DESATIVADAS (Chaves Desnecessárias no .env, mas mantidas no código)
    AWIN_AFFILIATE_ID: Optional[str] = None
    PREFIXO_ADMITAD_ALI: Optional[str] = None
    PREFIXO_LOMADEE: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


try:
    config = Settings()
except Exception as e:
    print(f"❌ ERRO CRÍTICO no .env: {e}")
    raise e