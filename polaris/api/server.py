from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from polaris.api import routes as _routes
from polaris.api.routes import DB_PATH, LT, router
from polaris.utils.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("./artifacts").mkdir(parents=True, exist_ok=True)
    Path("./artifacts/audit_logs").mkdir(parents=True, exist_ok=True)
    await init_db(DB_PATH)
    yield
    if _routes._AUDIT_TASK and not _routes._AUDIT_TASK.done():
        _routes._AUDIT_TASK.cancel()
    await LT.stop()


app = FastAPI(title="polaris-api", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


def main() -> None:
    import uvicorn
    port = int(os.environ.get("POLARIS_API_PORT", 8000))
    uvicorn.run("polaris.api.server:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
