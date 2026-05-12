from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from polaris.utils.gemini_client import GeminiClient


class _Msg(BaseModel):
    role: str
    content: str


class _LobsterMeta(BaseModel):
    declared_intent: str | None = None
    declared_paths: list[str] = Field(default_factory=list)
    declared_domains: list[str] = Field(default_factory=list)
    agent_id: str | None = None


class _ChatReq(BaseModel):
    model: str = "gemini-3.1-flash-lite"
    messages: list[_Msg]
    temperature: float = 0.2
    # Lobster Trap reads `_lobstertrap` from the original wire request before forwarding
    # to this shim. The shim itself just ignores it (Pydantic alias keeps validation lenient).
    lobstertrap: _LobsterMeta | None = Field(default=None, alias="_lobstertrap")

    model_config = {"populate_by_name": True, "extra": "ignore"}


def build_app(client: GeminiClient | None = None) -> FastAPI:
    """Build the shim FastAPI app. If `client` is None, GeminiClient is constructed
    LAZILY on first request (so module import doesn't require GEMINI_API_KEY)."""
    app = FastAPI(title="polaris-gemini-openai-shim")
    holder: dict[str, GeminiClient | None] = {"client": client}

    def _get_client() -> GeminiClient:
        if holder["client"] is None:
            holder["client"] = GeminiClient()
        assert holder["client"] is not None
        return holder["client"]

    @app.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/chat/completions")
    async def chat(req: _ChatReq) -> dict[str, Any]:
        gemini = _get_client()
        system_msgs = [m.content for m in req.messages if m.role == "system"]
        user_msgs = [m.content for m in req.messages if m.role != "system"]
        prompt = "\n\n".join(user_msgs) or "(empty)"
        sys_inst = "\n\n".join(system_msgs) if system_msgs else None

        text: str = await gemini.generate(
            prompt=prompt,
            model=req.model,
            temperature=req.temperature,
            system_instruction=sys_inst,
        )
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    return app


# Module-level app for `uvicorn polaris.utils.openai_gemini_shim:app`.
app = build_app()
