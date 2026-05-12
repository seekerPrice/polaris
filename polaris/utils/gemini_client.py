from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

# Load .env at module import so callers (Reader, Synthesizer, RedTeam, shim, FastAPI) can
# `GeminiClient()` without explicit env-var setup. Idempotent — safe to call repeatedly.
load_dotenv()

log = logging.getLogger(__name__)


class GeminiCallError(RuntimeError):
    """Raised when Gemini fails after max_retries attempts."""


@dataclass
class _Usage:
    prompt_tokens: int
    output_tokens: int

    @classmethod
    def from_response(cls, resp: Any) -> "_Usage":
        meta = getattr(resp, "usage_metadata", None)
        return cls(
            prompt_tokens=getattr(meta, "prompt_token_count", 0) if meta else 0,
            output_tokens=getattr(meta, "candidates_token_count", 0) if meta else 0,
        )


class GeminiClient:
    """Centralised async wrapper around google-genai with retries + JSON-mode + structured logs.

    Every Gemini call in Polaris MUST go through this client (CLAUDE.md §6).
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "gemini-3-flash-preview",
        max_retries: int = 3,
        base_backoff_s: float = 0.5,
    ) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        self._client = genai.Client(api_key=key)
        self._default_model = default_model
        self._max_retries = max_retries
        self._base_backoff_s = base_backoff_s

    async def generate(
        self,
        *,
        prompt: str,
        model: str | None = None,
        response_schema: type[BaseModel] | None = None,
        temperature: float = 0.1,
        system_instruction: str | None = None,
    ) -> Any:
        """Generate content. Returns parsed Pydantic instance if response_schema is provided,
        else returns the raw .text string. Retries on transient errors only.
        """
        chosen_model = model or self._default_model
        # Cap output tokens — without this, Gemini occasionally pads with thousands of
        # trailing whitespace lines, hits the SDK buffer, and returns truncated JSON.
        # 4096 is plenty for a Lobster Trap policy YAML or a Reader PolicyTree.
        config: dict[str, Any] = {"temperature": temperature, "max_output_tokens": 4096}
        if system_instruction:
            config["system_instruction"] = system_instruction
        if response_schema is not None:
            config["response_mime_type"] = "application/json"
            config["response_schema"] = response_schema

        last_err: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            t0 = time.monotonic()
            try:
                resp = await asyncio.to_thread(
                    self._client.models.generate_content,
                    model=chosen_model,
                    contents=prompt,
                    config=config,
                )
                usage = _Usage.from_response(resp)
                latency_ms = int((time.monotonic() - t0) * 1000)
                log.info(json.dumps({
                    "evt": "gemini_call",
                    "model": chosen_model,
                    "attempt": attempt,
                    "latency_ms": latency_ms,
                    "prompt_tokens": usage.prompt_tokens,
                    "output_tokens": usage.output_tokens,
                }))
                if response_schema is not None:
                    parsed = getattr(resp, "parsed", None)
                    if parsed is not None:
                        return parsed
                    return response_schema.model_validate_json(resp.text)
                return resp.text
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                transient = any(s in msg for s in ("429", "500", "502", "503", "504", "timeout"))
                if not transient or attempt == self._max_retries:
                    log.error(json.dumps({
                        "evt": "gemini_failed",
                        "model": chosen_model,
                        "attempt": attempt,
                        "err": str(e)[:200],
                    }))
                    raise GeminiCallError(str(e)) from e
                backoff = self._base_backoff_s * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
                await asyncio.sleep(backoff)

        raise GeminiCallError(str(last_err) if last_err else "unknown")  # pragma: no cover
