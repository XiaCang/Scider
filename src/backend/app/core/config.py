import os


class Settings:
    APP_NAME = os.getenv("APP_NAME", "Scider Backend")
    API_PREFIX = os.getenv("API_PREFIX", "/api")

    REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
    REDIS_RESULT_BACKEND = os.getenv("REDIS_RESULT_BACKEND", "redis://localhost:6379/1")

    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")


settings = Settings()
