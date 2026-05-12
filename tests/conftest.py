"""Test bootstrap — load .env so GEMINI_API_KEY is visible to skipif() before tests run."""
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure repo root is on sys.path even if tests run from elsewhere.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()
