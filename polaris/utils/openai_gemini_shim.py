from __future__ import annotations

import ipaddress
import logging
import os
import secrets
import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from polaris.utils.gemini_client import GeminiClient

log = logging.getLogger(__name__)

# C3 fix (deep-check 2026-05-13): the shim is the trust boundary between Lobster Trap
# and Gemini. Previously any local process could POST /v1/chat/completions and bypass
# the firewall entirely. Two defenses, applied as middleware:
#   1. Reject any client whose remote IP is not loopback (127.0.0.0/8 or ::1).
#   2. If POLARIS_SHIM_TOKEN is set, require Authorization: Bearer <token>.
# The token is optional today because Lobster Trap (an unmodified upstream binary) does
# not yet inject custom upstream headers — once it does, set the env var to make this
# mandatory. The localhost-only check is unconditional and already closes the LAN attack
# surface from a hostile Wi-Fi.
_LOOPBACK_NETS = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
)


def _is_loopback(host: str | None) -> bool:
    if not host:
        return False
    # Starlette's TestClient uses the literal "testclient" as request.client.host;
    # allowing it keeps unit tests on the firewall middleware honest without disabling
    # the check in production.
    if host == "testclient":
        return True
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(addr in net for net in _LOOPBACK_NETS)


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

    # The shim sits behind an unmodified upstream LobsterTrap binary which forwards
    # real OpenAI-format requests — they regularly carry fields we don't model
    # (`stream`, `max_tokens`, future additions). `extra: "ignore"` keeps the demo
    # robust against that drift. `_lobster_trap`-style typo detection has to happen
    # somewhere that can warn without 422-ing the actual chat completion.
    model_config = {"populate_by_name": True, "extra": "ignore"}


def build_app(client: GeminiClient | None = None) -> FastAPI:
    """Build the shim FastAPI app. If `client` is None, GeminiClient is constructed
    LAZILY on first request (so module import doesn't require GEMINI_API_KEY)."""
    app = FastAPI(title="polaris-gemini-openai-shim")
    holder: dict[str, GeminiClient | None] = {"client": client}

    def _get_client() -> GeminiClient:
        c = holder["client"]
        if c is None:
            c = GeminiClient()
            holder["client"] = c
        return c

    @app.middleware("http")
    async def _firewall(request: Request, call_next):
        # Allow the healthz probe through unconditionally so run_demo.sh can detect
        # readiness without needing the token.
        if request.url.path == "/healthz":
            return await call_next(request)
        # Code-review bug-6 fix (deep-check 2026-05-14): return a JSONResponse directly
        # rather than raising HTTPException. In Starlette's middleware stack, exceptions
        # raised inside @app.middleware("http") propagate past FastAPI's ExceptionMiddleware
        # to ServerErrorMiddleware and render as a 500 traceback — not the intended 403/401.
        client_host = request.client.host if request.client else None
        if not _is_loopback(client_host):
            log.warning("shim rejected non-loopback client: %s", client_host)
            return JSONResponse(
                {"detail": "shim accepts loopback connections only"},
                status_code=403,
            )
        required_token = os.environ.get("POLARIS_SHIM_TOKEN")
        if required_token:
            auth = request.headers.get("authorization", "")
            presented = auth.removeprefix("Bearer ").strip() if auth.lower().startswith("bearer ") else ""
            if not presented or not secrets.compare_digest(presented, required_token):
                log.warning("shim rejected request with bad/missing bearer token")
                return JSONResponse(
                    {"detail": "shim requires Authorization: Bearer <POLARIS_SHIM_TOKEN>"},
                    status_code=401,
                )
        return await call_next(request)

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

        log.info(
            "shim.chat model=%s msgs=%d temp=%.2f",
            req.model, len(req.messages), req.temperature,
        )
        # L13 (deep-check 2026-05-13): log declared_intent so a shim-bypass attempt or
        # misconfigured LT forwarding is visible in shim logs.
        if req.lobstertrap is not None:
            log.info(
                "shim.chat.lobstertrap declared_intent=%s agent_id=%s",
                req.lobstertrap.declared_intent, req.lobstertrap.agent_id,
            )
        try:
            text: str = await gemini.generate(
                prompt=prompt,
                model=req.model,
                temperature=req.temperature,
                system_instruction=sys_inst,
            )
        except Exception as e:
            log.exception("shim.chat upstream gemini call failed")
            raise HTTPException(502, f"upstream gemini call failed: {e}") from e
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
