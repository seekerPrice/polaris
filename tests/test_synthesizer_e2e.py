import json
import os
from pathlib import Path

import pytest

from polaris.agents.reader import PolicyTree, Reader
from polaris.agents.synthesizer import Synthesizer

pytestmark = pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="requires GEMINI_API_KEY",
)


@pytest.mark.asyncio
@pytest.mark.parametrize("doc", ["soc2_excerpt.md", "eu_ai_act_excerpt.md", "owasp_llm_top10.md"])
async def test_synthesizer_passes_validation_on_real_tree(doc: str) -> None:
    text = (Path("examples") / doc).read_text(encoding="utf-8")
    tree: PolicyTree = await Reader().process(text)
    result = await Synthesizer().process(tree)

    out_dir = Path("artifacts/synthesizer_outputs") / doc.replace(".md", "")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "policy.yaml").write_text(result.output.yaml_text)
    (out_dir / "declared_intents.json").write_text(
        json.dumps({k: v.model_dump() for k, v in result.output.declared_intents.items()}, indent=2)
    )
    (out_dir / "test_results.txt").write_text(result.test_results_summary)
    assert result.passed, f"{doc}: {result.test_results_summary}"
