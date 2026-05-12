from __future__ import annotations

import asyncio
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError

from polaris.lobster.schema import LobsterTrapPolicy


@dataclass
class TestResults:
    passed: bool
    parse_error: str | None = None
    schema_errors: list[str] = field(default_factory=list)
    lt_exit_code: int | None = None
    lt_stdout: str = ""
    lt_stderr: str = ""

    @property
    def summary(self) -> str:
        if self.passed:
            return "PASS"
        if self.parse_error:
            return f"PARSE_FAIL: {self.parse_error}"
        if self.schema_errors:
            return "SCHEMA_FAIL: " + " | ".join(self.schema_errors[:5])
        return f"LOBSTER_TEST_FAIL (exit={self.lt_exit_code}): {self.lt_stderr[:500]}"


async def validate(yaml_text: str, lobstertrap_binary: Path = Path("./bin/lobstertrap")) -> TestResults:
    # Layer 1 — parse
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        return TestResults(passed=False, parse_error=str(e))

    # Layer 2 — Pydantic
    try:
        LobsterTrapPolicy.model_validate(data)
    except ValidationError as e:
        return TestResults(passed=False, schema_errors=[str(err) for err in e.errors()])

    # Layer 3 — lobstertrap test
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
        tmp.write(yaml_text)
        tmp_path = Path(tmp.name)
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            [str(lobstertrap_binary), "test", "--policy", str(tmp_path)],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired as e:
        return TestResults(
            passed=False,
            lt_exit_code=None,
            lt_stdout=(e.stdout or b"").decode(errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or ""),
            lt_stderr=f"timeout after 60s: {e}",
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    return TestResults(
        passed=(proc.returncode == 0),
        lt_exit_code=proc.returncode,
        lt_stdout=proc.stdout,
        lt_stderr=proc.stderr,
    )
