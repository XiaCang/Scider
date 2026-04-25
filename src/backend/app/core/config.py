import os


class Settings:
    APP_NAME = os.getenv("APP_NAME", "Scider Backend")
    API_PREFIX = os.getenv("API_PREFIX", "/api")

    # Redis is used by Celery as broker and result backend.
    REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
    REDIS_RESULT_BACKEND = os.getenv("REDIS_RESULT_BACKEND", "redis://localhost:6379/1")


settings = Settings()
