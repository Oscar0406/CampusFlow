"""
services/llm_service.py
Wraps any OpenAI-compatible provider with tool-calling support.
Config-driven: model, base_url, and api_key_env all come from university YAML.
"""
import json
import os
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from zai import ZaiClient

load_dotenv()

_PROVIDERS = {
    "groq": lambda key, **kw: Groq(api_key=key),
    "openai": lambda key, **kw: OpenAI(api_key=key),
    "hf": lambda key, **kw: OpenAI(api_key=key, base_url=kw.get("base_url")),
    "zai": lambda key, **kw: ZaiClient(api_key=key, base_url=kw.get("base_url")),
}

class LLMService:
    def __init__(self, model, api_key_env, provider="groq", base_url=None, **kwargs):
        self.model = model
        key = os.environ[api_key_env]
        factory = _PROVIDERS.get(provider, _PROVIDERS["groq"])
        self._client = factory(key, base_url=base_url)

    @classmethod
    def from_config(cls, llm_cfg):
        return cls(
            model       = llm_cfg["model"],
            api_key_env = llm_cfg["api_key_env"],
            provider    = llm_cfg.get("provider", "groq"),
            base_url    = llm_cfg.get("base_url"),
        )

    def complete(self, messages: list[dict], temperature: float = 0.3) -> str:
        """Plain completion — no tools. Returns raw string."""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        temperature: float = 0.3,
    ) -> dict:
        """
        Completion with tool schemas. Returns either:
          {"type": "text",     "content": str}
          {"type": "tool_use", "raw": <assistant msg>, "tool_calls": [{id, name, arguments}]}
        """
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
        )
        message = response.choices[0].message

        if message.tool_calls:
            parsed = [
                {
                    "id":        tc.id,
                    "name":      tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                }
                for tc in message.tool_calls
            ]
            raw_assistant = {
                "role":       "assistant",
                "content":    message.content or "",
                "tool_calls": [
                    {
                        "id":   tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in message.tool_calls
                ],
            }
            return {"type": "tool_use", "raw": raw_assistant, "tool_calls": parsed}

        return {"type": "text", "content": message.content or ""}
