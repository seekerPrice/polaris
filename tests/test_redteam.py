import asyncio
from polaris.agents.redteam import RedTeam


def test_demo_sequence_has_three_probes() -> None:
    rt = RedTeam.__new__(RedTeam)
    rt._client = None  # noqa: SLF001
    rt._system_prompt = None  # noqa: SLF001
    rt._target_url = ""  # noqa: SLF001
    seq = asyncio.run(rt.demo_sequence())
    assert len(seq) == 3
    assert seq[0].attack_category.startswith("prompt_injection")
    assert "base64" in seq[1].attack_subtype
    assert seq[2].expected_rule == "block_obfuscated_exfiltration"
