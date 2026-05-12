from fastapi.testclient import TestClient
from polaris.utils.openai_gemini_shim import build_app


class _StubClient:
    async def generate(self, **_):
        return "stub-response"


def test_chat_completion_round_trip():
    app = build_app(client=_StubClient())  # type: ignore[arg-type]
    c = TestClient(app)
    r = c.post("/v1/chat/completions", json={
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": "ping"}],
        "_lobstertrap": {"declared_intent": "general", "agent_id": "test"},
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["choices"][0]["message"]["content"] == "stub-response"
    assert body["object"] == "chat.completion"


def test_health():
    app = build_app(client=_StubClient())  # type: ignore[arg-type]
    c = TestClient(app)
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_extra_fields_ignored():
    app = build_app(client=_StubClient())  # type: ignore[arg-type]
    c = TestClient(app)
    r = c.post("/v1/chat/completions", json={
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": "ping"}],
        "stream": False,         # OpenAI extras the shim should silently accept
        "max_tokens": 100,
    })
    assert r.status_code == 200
