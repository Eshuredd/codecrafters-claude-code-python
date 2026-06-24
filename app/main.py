import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Tuple


BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def _mask_key(k: str) -> str:
    if not k:
        return "(none)"
    if len(k) <= 8:
        return "****"
    return f"{k[:4]}...{k[-4:]}"


def find_api_key() -> Tuple[Optional[str], str]:
    # 1) Check process environment
    env_key = os.environ.get("OPENROUTER_API_KEY")
    if env_key:
        return env_key, "environment"

    # 2) Check for a .env file in the project root (two levels up from this file)
    repo_root = Path(__file__).resolve().parents[1]
    dotenv = repo_root / ".env"
    if dotenv.is_file():
        try:
            for line in dotenv.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "OPENROUTER_API_KEY" in line:
                    # simple parsing KEY=VALUE, allows surrounding quotes
                    key = line.split("=", 1)[1].strip().strip('\"\'')
                    if key:
                        return key, f"{dotenv}"
        except Exception:
            pass

    # 3) Optional: check a home file for user convenience
    home_file = Path.home() / ".openrouter_api_key"
    if home_file.is_file():
        try:
            key = home_file.read_text().strip()
            if key:
                return key, str(home_file)
        except Exception:
            pass

    return None, "none"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    API_KEY, source = find_api_key()

    # Log where the key came from (masked) to stderr for visibility
    print(f"OPENROUTER_API_KEY source: {source}; value: {_mask_key(API_KEY)}", file=sys.stderr)

    # Print the actual key to stdout so `codecrafters submit` (no flags) shows it
    if API_KEY:
        print(f"OPENROUTER_API_KEY: {API_KEY}")

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    # Import here so running the detection doesn't require the package installed
    from openai import OpenAI

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=[{"role": "user", "content": args.p}],
    )

    if not chat.choices or len(chat.choices) == 0:
        raise RuntimeError("no choices in response")

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # TODO: Uncomment the following line to pass the first stage
    print(chat.choices[0].message.content)


if __name__ == "__main__":
    main()
