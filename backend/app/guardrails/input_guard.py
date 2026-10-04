import re
from decimal import Decimal
from ..core.config import get_openai_client, get_settings
from ..core.state import GuardrailVerdict

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(an|the)\s+unrestricted", re.IGNORECASE),
    re.compile(r"system\s*:\s*role", re.IGNORECASE),
]


async def evaluate_input_guardrail(user_message: str) -> GuardrailVerdict:
    for pattern in INJECTION_PATTERNS:
        if pattern.search(user_message):
            return GuardrailVerdict(
                allowed=False,
                category="injection",
                confidence=Decimal("0.99"),
                reason="Input contains disallowed prompt-injection or override phrasing.",
                is_retryable=False,
            )

    client = get_openai_client()
    settings = get_settings()

    system_prompt = (
        "You are an input safety and topical guardrail for a travel planning system. "
        "Determine if the user query is a legitimate travel, vacation, or trip planning request. "
        "Reject requests that are completely off-topic (e.g. general programming, homework, political debates) "
        "or obviously unviable."
    )

    try:
        response = await client.beta.chat.completions.parse(
            model=settings.OPENAI_MODEL_GUARDRAIL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format=GuardrailVerdict,
            max_tokens=settings.OPENAI_MAX_TOKENS_GUARDRAIL,
            temperature=0.0,
        )
        verdict = response.choices[0].message.parsed
        if verdict:
            return verdict
    except Exception:
        pass

    return GuardrailVerdict(
        allowed=True,
        category="clean",
        confidence=Decimal("0.80"),
        reason="Deterministic fallback allowed standard travel query.",
        is_retryable=True,
    )
