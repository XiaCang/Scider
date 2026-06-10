"""
LLM Client — 统一封装 DeepSeek 和 Qwen 大模型 API 调用。

两者都暴露 OpenAI 兼容的 REST 接口，因此用同一个 openai SDK 驱动。
通过环境变量 LLM_PROVIDER 选择提供商（"deepseek" 或 "qwen"）。
"""

from openai import OpenAI

from app.core.config import settings


def _build_client() -> OpenAI:
    """根据配置构造对应提供商的 OpenAI 客户端实例。"""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "qwen":
        return OpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            timeout=settings.LLM_TIMEOUT,
        )

    # 默认 deepseek
    return OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        timeout=settings.LLM_TIMEOUT,
    )


def _active_model() -> str:
    """返回当前提供商对应的模型名称。"""
    provider = settings.LLM_PROVIDER.lower()
    return settings.QWEN_MODEL if provider == "qwen" else settings.DEEPSEEK_MODEL


def chat_completion(system_prompt: str, user_prompt: str) -> str:
    """
    发起一次 chat completion 请求，返回模型的文本回复。

    Args:
        system_prompt: System 角色指令。
        user_prompt:   User 角色输入内容（如论文正文摘录）。

    Returns:
        模型回复的纯文本字符串。

    Raises:
        openai.OpenAIError: API 调用失败时原样抛出，由上层任务决定重试策略。
    """
    client = _build_client()
    response = client.chat.completions.create(
        model=_active_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
    )
    return response.choices[0].message.content or ""
