import json
import os

import httpx

API_KEY = os.environ.get("DEEPSEEK_API_KEY")


def call_llm(
    messages,
    tools=None,
    model="deepseek-chat",
    temperature=0.6,
    max_tokens=4000,
    api_base_url="https://api.deepseek.com/v1",
):
    if not API_KEY:
        return {
            "response_type": "error",
            "content": "DEEPSEEK_API_KEY environment variable is not set.",
        }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if tools:
        body["tools"] = tools

    try:
        response = httpx.post(
            f"{api_base_url}/chat/completions",
            headers=headers,
            json=body,
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]

        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            return {
                "response_type": "tool_call",
                "content": {
                    "id": tool_call["id"],
                    "name": tool_call["function"]["name"],
                    "arguments": json.loads(tool_call["function"]["arguments"]),
                },
            }

        return {
            "response_type": "message",
            "content": message.get("content", ""),
        }

    except httpx.HTTPStatusError as e:
        return {
            "response_type": "error",
            "content": (
                f"API error ({e.response.status_code}): "
                f"{e.response.text[:500]}"
            ),
        }
    except httpx.TimeoutException:
        return {
            "response_type": "error",
            "content": "Request timed out after 120 seconds.",
        }
    except Exception as e:
        return {
            "response_type": "error",
            "content": f"Unexpected error: {str(e)}",
        }
