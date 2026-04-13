from __future__ import annotations

import json
import os
from urllib import request, error
from pathlib import Path


def _load_env_file() -> None:
    """
    最小 .env 读取器：
    - 默认读取项目根目录下的 .env
    - 只处理 KEY=VALUE 这种简单格式
    - 不覆盖已经存在的环境变量
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    env_path = project_root / ".env"

    if not env_path.exists() or not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value

_load_env_file()


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")


def generate_with_ollama(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0,
    timeout: int = 300,
    show_thinking: bool = False,
    think: bool | None = False,
    max_thinking_chars: int = 4000,
) -> str:
    payload = {
        "model": model,
        "prompt": user_prompt,
        "system": system_prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
        },
    }

    if think is not None:
        payload["think"] = think

    req = request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    final_response_parts: list[str] = []
    thinking_parts: list[str] = []
    thinking_char_count = 0

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue

                chunk = json.loads(line)

                if "thinking" in chunk and chunk["thinking"]:
                    thinking_text = chunk["thinking"]
                    thinking_parts.append(thinking_text)
                    thinking_char_count += len(thinking_text)
                    if show_thinking and thinking_char_count <= max_thinking_chars:
                        print(thinking_text, end="", flush=True)

                if "response" in chunk and chunk["response"]:
                    final_response_parts.append(chunk["response"])

                if chunk.get("done", False):
                    break

    except error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            error_body = ""
        raise RuntimeError(
            f"Ollama HTTP error: {e.code} {e.reason}. Response body: {error_body}"
        ) from e
    except error.URLError as e:
        raise RuntimeError(
            f"Ollama connection error: {e.reason}. "
            f"请确认 ollama serve 已启动，且 127.0.0.1:11434 可访问。"
        ) from e

    if show_thinking and thinking_parts:
        if thinking_char_count > max_thinking_chars:
            print("\n\n=== THINKING TRUNCATED ===\n")
        else:
            print("\n\n=== END THINKING ===\n")

    return "".join(final_response_parts)


def generate_with_deepseek(
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = 0,
    timeout: int = 300,
) -> str:
    final_api_key = api_key or DEEPSEEK_API_KEY
    final_base_url = (base_url or DEEPSEEK_BASE_URL).rstrip("/")

    if not final_api_key:
        raise RuntimeError(
            "DeepSeek API key is missing. 请先设置环境变量 DEEPSEEK_API_KEY，"
            "或在调用 generate_with_deepseek 时显式传入 api_key。"
        )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "stream": False,
    }

    req = request.Request(
        f"{final_base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {final_api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            return data["choices"][0]["message"]["content"]
    except error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            error_body = ""
        raise RuntimeError(
            f"DeepSeek HTTP error: {e.code} {e.reason}. Response body: {error_body}"
        ) from e
    except error.URLError as e:
        raise RuntimeError(f"DeepSeek connection error: {e.reason}") from e
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        raise RuntimeError("DeepSeek response format error: 无法从返回结果中解析 message.content") from e