import json
import pytest
from pydantic import BaseModel
from polaris.utils.gemini_client import GeminiClient, GeminiCallError


class _SmokeSchema(BaseModel):
    greeting: str


@pytest.mark.asyncio
async def test_generate_returns_pydantic_instance(monkeypatch) -> None:
    captured: dict = {}

    class _FakeModels:
        def generate_content(self, *, model, contents, config):
            captured["model"] = model
            captured["config"] = config

            class _Resp:
                text = json.dumps({"greeting": "hi"})
                parsed = _SmokeSchema(greeting="hi")
                usage_metadata = type(
                    "U", (), {"prompt_token_count": 7, "candidates_token_count": 3}
                )()

            return _Resp()

    class _FakeClient:
        def __init__(self, *_, **__):
            self.models = _FakeModels()

    # IMPORTANT: patch BEFORE constructing GeminiClient — constructor calls genai.Client(...)
    monkeypatch.setattr("polaris.utils.gemini_client.genai.Client", _FakeClient)
    client = GeminiClient(api_key="dummy", default_model="gemini-2.5-flash")

    out = await client.generate(prompt="hi", response_schema=_SmokeSchema)
    assert isinstance(out, _SmokeSchema)
    assert out.greeting == "hi"
    assert captured["model"] == "gemini-2.5-flash"
    assert captured["config"]["response_schema"] is _SmokeSchema
    assert captured["config"]["response_mime_type"] == "application/json"


@pytest.mark.asyncio
async def test_generate_retries_on_5xx(monkeypatch) -> None:
    calls = {"n": 0}

    class _Models:
        def generate_content(self, **_):
            calls["n"] += 1
            if calls["n"] < 3:
                raise RuntimeError("503 service unavailable")

            class _Resp:
                text = "{}"
                parsed = None
                usage_metadata = type(
                    "U", (), {"prompt_token_count": 0, "candidates_token_count": 0}
                )()

            return _Resp()

    class _FakeClient:
        def __init__(self, *_, **__):
            self.models = _Models()

    monkeypatch.setattr("polaris.utils.gemini_client.genai.Client", _FakeClient)
    client = GeminiClient(
        api_key="dummy",
        default_model="gemini-2.5-flash",
        max_retries=3,
        base_backoff_s=0.0,
    )
    await client.generate(prompt="x")
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_generate_raises_after_max_retries(monkeypatch) -> None:
    class _Models:
        def generate_content(self, **_):
            raise RuntimeError("500")

    class _FakeClient:
        def __init__(self, *_, **__):
            self.models = _Models()

    monkeypatch.setattr("polaris.utils.gemini_client.genai.Client", _FakeClient)
    client = GeminiClient(
        api_key="dummy",
        default_model="gemini-2.5-flash",
        max_retries=2,
        base_backoff_s=0.0,
    )
    with pytest.raises(GeminiCallError):
        await client.generate(prompt="x")
