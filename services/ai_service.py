"""
AI provider wrapper (currently Groq).

Routes and services never import the Groq SDK directly — they call
get_reply(history). If you swap providers later, this is the only
file that changes.
"""

from groq import Groq

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_MAX_TOKENS,
    GROQ_TEMPERATURE,
    SYSTEM_PROMPT,
)

_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


class AiNotConfigured(RuntimeError):
    """Raised when GROQ_API_KEY is missing."""


class AiRequestError(RuntimeError):
    """Raised when the provider API call itself fails."""


def get_reply(history: list[dict]) -> str:
    """
    history: list of {"role": "user" | "ai", "content": str}
    Returns the assistant's reply text.
    """
    if _client is None:
        raise AiNotConfigured(
            "GROQ_API_KEY is not set. Add it to your .env file."
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history:
        role = "assistant" if turn["role"] == "ai" else "user"
        messages.append({"role": role, "content": turn["content"]})

    try:
        completion = _client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=GROQ_TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS,
        )
    except Exception as exc:  # groq.APIError and friends
        raise AiRequestError(str(exc)) from exc

    return completion.choices[0].message.content