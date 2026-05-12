"""Test bootstrap — load .env so GEMINI_API_KEY is visible to skipif() before tests run."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Ensure repo root is on sys.path even if tests run from elsewhere.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()


@pytest.fixture(autouse=True)
def _kill_zombie_lobstertrap_before_live():
    """Live e2e tests share state via the LobsterTrap singleton — kill any leftover
    LT process before each test so a zombie from a prior run doesn't poison this one.
    Only runs when POLARIS_LIVE_E2E is set (skipped during unit-test runs)."""
    if os.environ.get("POLARIS_LIVE_E2E"):
        subprocess.run(["pkill", "-f", "bin/lobstertrap serve"], check=False, capture_output=True)
    yield
