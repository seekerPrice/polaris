"""Guard the stub-injection path against future singleton refactors.

If anyone ever changes Reader/Synthesizer/RedTeam to bypass the `client=...` parameter
in favour of the singleton, these tests catch the regression — otherwise unit tests that
mock the Gemini client would silently call the real API and burn quota.
"""

from polaris.agents.reader import Reader
from polaris.agents.redteam import RedTeam
from polaris.agents.synthesizer import Synthesizer


class _Stub:
    async def generate(self, **_):
        return "stub"


def test_reader_injection_wins_over_singleton():
    stub = _Stub()
    r = Reader(client=stub)  # type: ignore[arg-type]
    assert r._client is stub  # noqa: SLF001


def test_synth_injection_wins_over_singleton():
    stub = _Stub()
    s = Synthesizer(client=stub)  # type: ignore[arg-type]
    assert s._client is stub  # noqa: SLF001


def test_redteam_injection_wins_over_singleton():
    stub = _Stub()
    rt = RedTeam(client=stub)  # type: ignore[arg-type]
    assert rt._client is stub  # noqa: SLF001


def test_get_client_returns_same_instance_for_same_model():
    from polaris.utils.gemini_client import get_client
    a = get_client("gemini-3.1-flash-lite")
    b = get_client("gemini-3.1-flash-lite")
    assert a is b


def test_get_client_returns_different_instances_per_model():
    from polaris.utils.gemini_client import get_client
    a = get_client("gemini-3.1-flash-lite")
    b = get_client("gemini-2.5-pro")
    assert a is not b
