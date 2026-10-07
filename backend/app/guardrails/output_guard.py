import re
from ..core.state import GuardrailVerdict

PII_PATTERNS = [
    re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
]


def evaluate_output_guardrail(itinerary_text: str) -> GuardrailVerdict:
    for pattern in PII_PATTERNS:
        if pattern.search(itinerary_text):
            return GuardrailVerdict(
                allowed=False,
                category="pii",
                confidence=0.98,
                reason="Generated output contained potential personal identifier or payment credential pattern.",
                is_retryable=False,
            )

    return GuardrailVerdict(
        allowed=True,
        category="clean",
        confidence=0.99,
        reason="Output verified free of sensitive data.",
        is_retryable=True,
    )
