from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from polaris.api import routes as _routes
from polaris.api.routes import DB_PATH, LT, _DEFAULT_BASELINE_POLICY, _redeploy, router
from polaris.utils.db import init_db

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Path("./artifacts").mkdir(parents=True, exist_ok=True)
        Path("./artifacts/audit_logs").mkdir(parents=True, exist_ok=True)
        await init_db(DB_PATH)
        # H1 fix (deep-check 2026-05-13): spawn Lobster Trap with the default baseline
        # at lifespan startup so the firewall is live BEFORE any compliance doc is
        # uploaded. Previously LT only spawned during _pipeline, meaning the demo agent
        # got ECONNREFUSED until the first upload landed. Wrapped in try/except so a
        # startup failure logs loudly + dashboard sees the API up but LT down via
        # /healthz (next time we add one), instead of crashing the whole API.
        if _DEFAULT_BASELINE_POLICY.exists():
            try:
                await _redeploy("startup", _DEFAULT_BASELINE_POLICY)
                log.info("LT spawned with default baseline at startup")
            except Exception:
                log.exception("LT startup spawn failed — API will run but firewall is offline until first upload")
        else:
            log.warning("default baseline policy missing at %s — LT will spawn on first upload", _DEFAULT_BASELINE_POLICY)
    except Exception:
        log.exception("lifespan startup failed")
        raise
    yield
    if _routes._AUDIT_TASK and not _routes._AUDIT_TASK.done():
        _routes._AUDIT_TASK.cancel()
    await LT.stop()


app = FastAPI(title="polaris-api", lifespan=lifespan)
# Demo posture: allow any origin so judges can pull the dashboard from any device on the
# demo network. Revert to ["http://localhost:3000"] for any post-hackathon shipping work.
# Note: when allow_origins=["*"], allow_credentials must be False (CORS spec).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


def main() -> None:
    import uvicorn
    # M9 fix (deep-check 2026-05-13): default to 127.0.0.1 so the API isn't reachable
    # from conference Wi-Fi. The dashboard runs locally and proxies via NEXT_PUBLIC_API_BASE,
    # so loopback-only is fine for the single-user demo posture. Override with
    # POLARIS_API_HOST=0.0.0.0 if a judge needs to hit the API from their device.
    port = int(os.environ.get("POLARIS_API_PORT", 8000))
    host = os.environ.get("POLARIS_API_HOST", "127.0.0.1")
    uvicorn.run("polaris.api.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
