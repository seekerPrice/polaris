import os
from pathlib import Path

import pytest

from polaris.agents.reader import PolicyTree, Reader

pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="requires GEMINI_API_KEY",
)


@pytest.mark.asyncio
@pytest.mark.parametrize("doc", ["soc2_excerpt.md", "eu_ai_act_excerpt.md", "owasp_llm_top10.md"])
async def test_reader_extracts_at_least_three_requirements(doc: str):
    text = (Path("examples") / doc).read_text(encoding="utf-8")
    tree: PolicyTree = await Reader().process(text)
    assert len(tree.requirements) >= 3, f"{doc}: only {len(tree.requirements)} reqs"
    assert any(r.severity == "high" for r in tree.requirements), f"{doc}: no high-severity reqs"
    out = Path("artifacts/reader_outputs") / (doc.replace(".md", ".json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tree.model_dump_json(indent=2))
