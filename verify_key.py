import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import openai


def main() -> None:
    print("=" * 60)
    print("PlanMyTrip AI — Pre-Flight Key Verification")
    print("=" * 60)

    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        print(f"[ERROR] No .env file found at: {env_path}")
        print("Please copy .env.example to .env and insert your real OPENAI_API_KEY.")
        sys.exit(1)

    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        print("[ERROR] OPENAI_API_KEY is missing or empty in your .env file.")
        sys.exit(1)

    model_name = os.getenv("OPENAI_MODEL_GUARDRAIL", "gpt-4o-mini")

    print(f"[*] Target Model   : {model_name}")
    print(f"[*] Key Fingerprint: {api_key[:7]}...{api_key[-4:]}")
    print("[*] Sending ping request to OpenAI API...")

    client = openai.OpenAI(api_key=api_key, timeout=15.0)

    start_time = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Respond with the single word: OK"},
                {"role": "user", "content": "ping"},
            ],
            max_tokens=5,
            temperature=0.0,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

    except openai.AuthenticationError as err:
        print("\n[FAIL] Authentication Error: Your API key is invalid or unauthorized.")
        print(f"Details: {err}")
        sys.exit(1)

    except openai.RateLimitError as err:
        print("\n[FAIL] Rate Limit or Quota Exceeded:")
        print("You have either exceeded your monthly spend cap or your account has no funds.")
        print(f"Details: {err}")
        sys.exit(1)

    except openai.APIConnectionError as err:
        print("\n[FAIL] Network Connection Error:")
        print(f"Could not connect to OpenAI servers: {err}")
        sys.exit(1)

    except Exception as err:
        print(f"\n[FAIL] Unexpected Error ({type(err).__name__}): {err}")
        sys.exit(1)

    usage = response.usage
    raw_content = response.choices[0].message.content
    content = raw_content.strip() if raw_content else "OK"

    print("\n" + "-" * 60)
    print("[SUCCESS] OpenAI connection verified successfully!")
    print("-" * 60)
    print(f"Response Received : \"{content}\"")
    print(f"Round-Trip Latency: {elapsed_ms:.1f} ms")

    if usage:
        print(f"Prompt Tokens     : {usage.prompt_tokens}")
        print(f"Completion Tokens : {usage.completion_tokens}")
        print(f"Total Tokens      : {usage.total_tokens}")

        approx_cost = (
            usage.prompt_tokens * 0.00000015
            + usage.completion_tokens * 0.00000060
        )

        print(f"Approximate Cost  : ${approx_cost:.8f} USD")

    print("=" * 60)
    print("Pre-flight check passed. Ready to close Phase 0 and enter Phase 1.")
    print("=" * 60)


if __name__ == "__main__":
    main()