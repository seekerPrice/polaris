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
        # Phase-11 deep-review C4: keep drain tasks so they're cancellable on stop().
        self._drain_tasks: list[asyncio.Task] = []

    @staticmethod
    async def _drain_stream(stream: asyncio.StreamReader | None, label: str) -> None:
        """Continuously read+discard so LT's stdout/stderr pipe buffers never fill.
        Cancelled by `stop()` before the next spawn."""
        if stream is None:
            return
        try:
            while True:
                line = await stream.readline()
                if not line:
                    return
        except asyncio.CancelledError:
            raise
        except Exception:
            return

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
            assert self._proc.stdout is not None

            # Race stdout + stderr for the ready signal — upstream LT may log to either.
            async def _wait_for_ready_line(stream) -> bool:
                while True:
                    raw = await stream.readline()
                    if not raw:
                        return False
                    line = raw.decode(errors="ignore").lower()
                    if "listening on" in line or ":8080" in line:
                        return True

            tasks = [
                asyncio.create_task(_wait_for_ready_line(self._proc.stderr)),
                asyncio.create_task(_wait_for_ready_line(self._proc.stdout)),
            ]
            # Phase-11 deep-review (agents) C1: `asyncio.wait(timeout=N)` does NOT raise
            # TimeoutError — it returns (done, pending) with `done` empty on timeout.
            # The previous `except TimeoutError` branch was dead code, so on timeout
            # we raised but left `self._proc` alive (zombie subprocess). Now we
            # explicitly clean up the subprocess on ANY non-ready exit path.
            ready = False
            try:
                done, pending = await asyncio.wait(
                    tasks, timeout=15, return_when=asyncio.FIRST_COMPLETED
                )
                for t in pending:
                    t.cancel()
                # Drain cancelled tasks so asyncio doesn't emit "task was destroyed
                # but is pending" warnings on next loop iteration.
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
                ready = bool(done) and any(t.result() for t in done if not t.cancelled())
            finally:
                if not ready:
                    await self._stop_locked()
            if not ready:
                raise RuntimeError("lobstertrap did not signal ready in 15s")
            # Phase-11 deep-review (api) C4: drain stdout + stderr after readiness so
            # LT's slog doesn't block on a full pipe buffer over a long session.
            self._drain_tasks = [
                asyncio.create_task(self._drain_stream(self._proc.stdout, "lt.stdout")),
                asyncio.create_task(self._drain_stream(self._proc.stderr, "lt.stderr")),
            ]
            self._generation += 1
            return self._generation

    @property
    def generation(self) -> int:
        return self._generation

    async def stop(self) -> None:
        async with self._lock:
            await self._stop_locked()

    async def _stop_locked(self) -> None:
        # Cancel drain tasks BEFORE killing the process so cancellation doesn't race
        # with a closing pipe.
        for t in self._drain_tasks:
            t.cancel()
        if self._drain_tasks:
            await asyncio.gather(*self._drain_tasks, return_exceptions=True)
        self._drain_tasks = []
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
        on EOF if the path's inode changes (handles file rotation/truncation across reload)."""
        await asyncio.sleep(0.05)
        f = await aiofiles.open(self._audit_log, "r")
        # Track inode of the path we opened (NOT the fd — aiofiles fd is opaque/async).
        try:
            opened_ino = self._audit_log.stat().st_ino
        except OSError:
            opened_ino = None
        try:
            await f.seek(0, os.SEEK_END)
            while True:
                if self._generation != generation:
                    return
                line = await f.readline()
                if not line:
                    await asyncio.sleep(0.2)
                    # Re-open if the path now points to a different inode.
                    try:
                        cur_ino = self._audit_log.stat().st_ino
                        if opened_ino is not None and cur_ino != opened_ino:
                            await f.close()
                            f = await aiofiles.open(self._audit_log, "r")
                            opened_ino = cur_ino
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
