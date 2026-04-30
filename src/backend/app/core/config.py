import os


class Settings:
    APP_NAME = os.getenv("APP_NAME", "Scider Backend")
    API_PREFIX = os.getenv("API_PREFIX", "/api")

    REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
    REDIS_RESULT_BACKEND = os.getenv("REDIS_RESULT_BACKEND", "redis://localhost:6379/1")

    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
    # ──────────────────────────────────────────────
    # LLM Provider: "deepseek" | "qwen"
    # Both expose an OpenAI-compatible REST API,
    # so the same openai SDK can drive either one.
    # ──────────────────────────────────────────────
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")

    # DeepSeek
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # Qwen (通义千问 DashScope compatible-mode)
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")

    # Shared LLM call settings
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))   # seconds
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))


settings = Settings()
