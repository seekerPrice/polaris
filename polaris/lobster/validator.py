from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError

from polaris.lobster.client import LobsterTrap
from polaris.lobster.schema import LobsterTrapPolicy

log = logging.getLogger(__name__)


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
    yaml_sha = hashlib.sha256(yaml_text.encode("utf-8")).hexdigest()[:12]
    log.info("validate.start sha=%s len=%d binary=%s", yaml_sha, len(yaml_text), lobstertrap_binary)

    # Layer 1 — parse
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        log.warning("validate.parse_fail sha=%s err=%s", yaml_sha, e)
        return TestResults(passed=False, parse_error=str(e))

    # Layer 2 — Pydantic
    try:
        LobsterTrapPolicy.model_validate(data)
    except ValidationError as e:
        log.warning("validate.schema_fail sha=%s n_errs=%d", yaml_sha, len(e.errors()))
        return TestResults(passed=False, schema_errors=[str(err) for err in e.errors()])

    # Layer 3 — lobstertrap test (delegated to LobsterTrap.test_policy so this module
    # never shells out directly; satisfies CLAUDE.md §6 "all LT interactions via client.py").
    trap = LobsterTrap(binary=lobstertrap_binary)
    exit_code, stdout, stderr = await trap.test_policy(yaml_text)
    if exit_code == -1:
        log.warning("validate.lt_timeout sha=%s", yaml_sha)
        return TestResults(passed=False, lt_exit_code=None, lt_stdout=stdout, lt_stderr=stderr)

    passed = exit_code == 0
    log.info("validate.lt_done sha=%s exit=%d passed=%s", yaml_sha, exit_code, passed)
    return TestResults(
        passed=passed,
        lt_exit_code=exit_code,
        lt_stdout=stdout,
        lt_stderr=stderr,
    )
