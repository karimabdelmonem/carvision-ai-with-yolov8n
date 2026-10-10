"""
إعدادات التطبيق - تُقرأ من ملف .env تلقائيًا.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    كل إعدادات المشروع في مكان واحد.
    Pydantic يقرأ القيم من .env ويتحقق من صحتها.
    """
    # App
    APP_NAME: str = "CarScan API"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str = "car-images"

    # Model
    MODEL_PATH: str = "models/best.pt"
    CONFIDENCE_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.45
    MAX_IMAGE_SIZE_MB: int = 10

    # إعدادات Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


# كائن واحد يُستخدم في كل مكان
settings = Settings()