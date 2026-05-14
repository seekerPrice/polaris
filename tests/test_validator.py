from pathlib import Path

import pytest
from polaris.lobster.validator import validate


# The upstream default policy is verified by `lobstertrap test` to handle all 11 corpus
# prompts. Use it as the "known-good" fixture; the validator's Layer 3 calls the same
# `lobstertrap test` binary, so anything less comprehensive will FAIL not because the
# YAML is invalid but because the policy doesn't cover the corpus.
_UPSTREAM_GOOD = Path("examples/lobstertrap_default_policy.yaml")
GOOD = _UPSTREAM_GOOD.read_text() if _UPSTREAM_GOOD.exists() else Path("examples/lobstertrap_baseline_min.yaml").read_text()


@pytest.mark.asyncio
@pytest.mark.skipif(not _UPSTREAM_GOOD.exists(), reason="needs upstream default policy (run scripts/download_lobstertrap.sh first)")
async def test_valid_yaml_passes() -> None:
    res = await validate(GOOD)
    assert res.passed, res.summary


@pytest.mark.asyncio
async def test_unparseable_yaml_fails_layer_1() -> None:
    res = await validate("::not yaml::\n  - [")
    assert not res.passed
    assert res.parse_error


@pytest.mark.asyncio
async def test_schema_violation_fails_layer_2() -> None:
    bad = GOOD.replace("contains_injection_patterns", "contains_unicorns")
    res = await validate(bad)
    assert not res.passed
    assert res.schema_errors


@pytest.mark.asyncio
@pytest.mark.skipif(not Path("./bin/lobstertrap").exists(), reason="needs lobstertrap binary")
async def test_layer_3_runs_subprocess() -> None:
    """Sanity that layer 3 actually runs the binary even if the policy fails the corpus."""
    minimal = Path("examples/lobstertrap_baseline_min.yaml").read_text()
    res = await validate(minimal)
    # Minimal policy fails the corpus (expected), but exit code should be set, not None
    assert res.lt_exit_code is not None
