from __future__ import annotations

import asyncio
import json
import os
import signal
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

import aiofiles


@dataclass
class AuditEntry:
    raw: dict

    @property
    def verdict(self) -> str:
        return self.raw.get("verdict", "")

    @property
    def matched_rule(self) -> str | None:
        return self.raw.get("matched_rule")


class LobsterTrap:
    def __init__(
        self,
        binary: Path = Path("./bin/lobstertrap"),
        listen: str = ":8080",
        backend_url: str = "http://localhost:11434",
        audit_log_path: Path = Path("./artifacts/audit_logs/current.jsonl"),
    ) -> None:
        self._binary = binary
        self._listen = listen
        self._backend = backend_url
        self._audit_log = audit_log_path
        self._proc: asyncio.subprocess.Process | None = None
        self._generation = 0
        self._lock = asyncio.Lock()

    async def spawn(self, policy_path: Path) -> int:
        async with self._lock:
            self._audit_log.parent.mkdir(parents=True, exist_ok=True)
            self._audit_log.touch(exist_ok=True)
            cmd = [
                str(self._binary), "serve",
                "--policy", str(policy_path),
                "--listen", self._listen,
                "--backend", self._backend,
                "--audit-log", str(self._audit_log),
                "--no-dashboard",
            ]
            self._proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            assert self._proc.stderr is not None
            try:
                while True:
                    raw = await asyncio.wait_for(self._proc.stderr.readline(), timeout=15)
                    if not raw:
                        raise RuntimeError("lobstertrap exited before becoming ready")
                    line = raw.decode(errors="ignore")
                    if "listening" in line.lower() or "8080" in line:
                        break
            except asyncio.TimeoutError as e:
                await self._stop_locked()
                raise RuntimeError("lobstertrap did not become ready in 15s") from e
            self._generation += 1
            return self._generation

    @property
    def generation(self) -> int:
        return self._generation

    async def stop(self) -> None:
        async with self._lock:
            await self._stop_locked()

    async def _stop_locked(self) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._proc.kill()
                await self._proc.wait()
        self._proc = None

    async def reload(self, policy_path: Path) -> int:
        await self.stop()
        return await self.spawn(policy_path)

    async def tail_audit_log(self, *, generation: int) -> AsyncIterator[AuditEntry]:
        """Tail the JSONL until LobsterTrap reloads to a new generation. Re-opens the file
        on EOF if the inode changes (handles file rotation)."""
        await asyncio.sleep(0.05)
        f = await aiofiles.open(self._audit_log, "r")
        try:
            await f.seek(0, os.SEEK_END)
            while True:
                if self._generation != generation:
                    return
                line = await f.readline()
                if not line:
                    await asyncio.sleep(0.2)
                    try:
                        if (
                            self._audit_log.exists()
                            and self._audit_log.stat().st_ino != os.fstat(f.fileno()).st_ino
                        ):
                            await f.close()
                            f = await aiofiles.open(self._audit_log, "r")
                    except OSError:
                        pass
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    yield AuditEntry(raw=json.loads(line))
                except json.JSONDecodeError:
                    continue
        finally:
            await f.close()
