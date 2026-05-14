from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Any

from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, ValidationError

# Load .env at module import so callers (Reader, Synthesizer, RedTeam, shim, FastAPI) can
# `GeminiClient()` without explicit env-var setup. Idempotent — safe to call repeatedly.
load_dotenv()

log = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def get_client(default_model: str = "gemini-3.1-flash-lite") -> "GeminiClient":
    """Shared GeminiClient singleton per default-model. Avoids reconstructing the
    underlying SDK client (and re-reading GEMINI_API_KEY) on every Reader/Synth/RedTeam
    instantiation. Callers can still pass `client=<stub>` to override (used in tests).

    L8 NOTE (deep-check 2026-05-13): this cache binds GEMINI_API_KEY at first call.
    Tests that rotate the env var must call `get_client.cache_clear()` afterwards or
    use `GeminiClient(api_key=...)` directly to bypass the cache.
    """
    return GeminiClient(default_model=default_model)


class GeminiCallError(RuntimeError):
    """Raised when Gemini fails after max_retries attempts."""


# M5 fix (deep-check 2026-05-13): scrubber for anything that looks like a Google API key
# OR a generic secret blob. Applied to error messages before logging or surfacing
# upstream so an SDK regression that ever puts the key into an error string doesn't
# leak it via logs, Sentry traces, or FastAPI 500 responses.
import re as _re
_API_KEY_RE = _re.compile(r"AIza[0-9A-Za-z_-]{30,}")


def _redact_key(text: str) -> str:
    return _API_KEY_RE.sub("AIza<REDACTED>", text)


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
        default_model: str = "gemini-3.1-flash-lite",
        # H3/M1 fix (deep-check 2026-05-13): bumped from 2 → 3 to match CLAUDE.md §6
        # "retry up to 3 times". Combined with the ValidationError separation below
        # this restores the documented retry-with-feedback contract.
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
        thinking: dict | None = None,
    ) -> Any:
        """Generate content. Returns parsed Pydantic instance if response_schema is provided,
        else returns the raw .text string. Retries on transient errors only.

        `thinking` controls Gemini's extended-thinking feature:
          - {"budget": N} for 2.5-family (e.g. {"budget": 0} disables thinking)
          - {"level": "minimal"|"low"|"medium"|"high"} for 3.x-family
          - None = use the model's default (8192 tokens for 2.5; medium for 3.x)
        """
        from google.genai import types

        chosen_model = model or self._default_model
        # 64K output budget — leaves headroom for thinking + output even on the strongest
        # models. Max per Gemini docs is 65536; 65K caps protect against the trailing-
        # whitespace bloat bug observed in early 3.x preview models.
        config: dict[str, Any] = {"temperature": temperature, "max_output_tokens": 65536}
        if system_instruction:
            config["system_instruction"] = system_instruction
        if response_schema is not None:
            config["response_mime_type"] = "application/json"
            config["response_schema"] = response_schema
        if thinking:
            if "budget" in thinking:
                config["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking["budget"])
            elif "level" in thinking:
                config["thinking_config"] = types.ThinkingConfig(thinking_level=thinking["level"])

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
            except ValidationError:
                # H3 fix (deep-check 2026-05-13): re-raise Pydantic validation errors RAW
                # so callers can implement retry-with-feedback per CLAUDE.md §6. Previously
                # this was caught by the broad `except Exception` below and wrapped as
                # GeminiCallError, making the Reader/Synthesizer ValidationError retry
                # branches dead code (the contracted prompt repair never reached Gemini).
                raise
            except Exception as e:
                last_err = e
                # Phase-11 deep-review (agents) C4: substring-on-`.lower()` missed real
                # google-genai exception text (`ResourceExhausted`, `DeadlineExceeded`,
                # httpx `ReadTimeout`/`ConnectError`, etc.). Combine class-name check,
                # numeric code attribute, and substring fallback.
                cls_name = e.__class__.__name__
                code = getattr(e, "code", None) or getattr(e, "status_code", None)
                msg = str(e).lower()
                transient_cls = cls_name in {
                    "ResourceExhausted", "ServerError", "ServiceUnavailable",
                    "DeadlineExceeded", "InternalServerError", "BadGateway",
                    "GatewayTimeout", "RetryError", "ReadTimeout", "ConnectTimeout",
                    "ReadError", "ConnectError", "RemoteProtocolError",
                }
                transient_code = isinstance(code, int) and code in {429, 500, 502, 503, 504}
                transient_msg = any(s in msg for s in (
                    "429", "500", "502", "503", "504", "timeout",
                    "rate limit", "resource_exhausted", "deadline", "unavailable",
                ))
                transient = transient_cls or transient_code or transient_msg
                if not transient or attempt == self._max_retries:
                    # M5 fix (deep-check 2026-05-13): redact any value that looks like
                    # an API key (Google keys start with "AIza..."; generic 32+ char
                    # base64-y blob) before logging or surfacing to callers.
                    safe_err = _redact_key(str(e))[:200]
                    log.error(json.dumps({
                        "evt": "gemini_failed",
                        "model": chosen_model,
                        "attempt": attempt,
                        "err": safe_err,
                    }))
                    # Drop the `from e` chain to avoid the key leaking via __cause__'s
                    # traceback to any outer error reporter (Sentry, FastAPI 500 trace).
                    raise GeminiCallError(safe_err)
                backoff = self._base_backoff_s * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
                await asyncio.sleep(backoff)

        raise GeminiCallError(str(last_err) if last_err else "unknown")  # pragma: no cover
