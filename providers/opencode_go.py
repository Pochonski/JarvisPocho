import json
import sys
from pathlib import Path


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
BASE_URL = "https://opencode.ai/zen/go/v1"
MODEL = "deepseek-v4-pro"


def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("opencode_go_api_key", "")


def generate(prompt: str, system_prompt: str | None = None) -> str:
    from openai import OpenAI

    client = OpenAI(base_url=BASE_URL, api_key=_get_api_key())
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content


def generate_with_retry(prompt: str, system_prompt: str | None = None, max_retries: int = 3) -> str:
    import time

    last_error = None
    for attempt in range(max_retries):
        try:
            return generate(prompt, system_prompt)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"[OpencodeGo] Retry {attempt + 1} in {wait}s: {e}")
                time.sleep(wait)

    raise RuntimeError(f"OpenCode Go failed after {max_retries} attempts: {last_error}")
