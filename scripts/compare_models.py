"""CP (cost/performance) comparison: Gemini 2.5 vs 3.1 vs 3.x-flash on Polaris workloads.

Tests three roles:
  1. Synthesizer (PRO models)  — produce Lobster Trap YAML that passes ./bin/lobstertrap test
  2. Reader      (FLASH models) — parse a compliance doc into PolicyTree
  3. Red Team    (PRO models)   — generate adversarial probes

Reports per (model, role): pass/fail, wall latency, prompt+output tokens.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
import time
from pathlib import Path

from pydantic import BaseModel

from polaris.utils.gemini_client import GeminiClient


PRO_MODELS = ["gemini-2.5-pro", "gemini-3.1-pro-preview"]
FLASH_MODELS = ["gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]


HAND_TREE = {
    "policy_name": "cp-test-soc2",
    "source_document": "SOC 2 CC6.1",
    "requirements": [
        {"id": "REQ-001", "section": "OWASP LLM01", "control_type": "prompt_injection",
         "human_text": "Direct and indirect prompt injection attempts must be blocked.",
         "rationale": "contains_injection_patterns is the primary boolean signal.",
         "severity": "high", "lobster_trap_fields": ["contains_injection_patterns"],
         "suggested_action": "DENY"},
        {"id": "REQ-002", "section": "SOC 2 CC6.1", "control_type": "credential_exposure",
         "human_text": "The entity restricts access to information assets to authorized users.",
         "rationale": "Block any prompt or response containing API keys, tokens, or passwords.",
         "severity": "high", "lobster_trap_fields": ["contains_credentials"],
         "suggested_action": "DENY"},
        {"id": "REQ-003", "section": "SOC 2 CC6.1 / OWASP LLM02", "control_type": "file_access",
         "human_text": "Logical access to sensitive system paths must be restricted.",
         "rationale": "Block prompts that reference /etc/, ~/.ssh/, .env, /root/, .aws/credentials.",
         "severity": "high", "lobster_trap_fields": ["contains_sensitive_paths"],
         "suggested_action": "DENY"},
        {"id": "REQ-004", "section": "SOC 2 CC6.6 / OWASP LLM07", "control_type": "system_command_execution",
         "human_text": "Dangerous system commands (rm -rf, sudo, curl|bash) must not be executed.",
         "rationale": "contains_system_commands flag catches shell-injection-style attacks.",
         "severity": "high", "lobster_trap_fields": ["contains_system_commands"],
         "suggested_action": "DENY"},
        {"id": "REQ-005", "section": "OWASP LLM06", "control_type": "data_exfiltration",
         "human_text": "Prompts attempting to exfiltrate data to attacker-controlled domains must be blocked.",
         "rationale": "Combine intent_category=data_access with target_domains containing paste sites.",
         "severity": "high", "lobster_trap_fields": ["contains_exfiltration", "target_domains"],
         "suggested_action": "DENY"},
    ],
}


class _Yaml(BaseModel):
    yaml_text: str


def _strip_example_5(prompt: str) -> str:
    marker = "### Example 5 — Block obfuscated payloads (Red Team-discovered class)"
    if marker not in prompt:
        return prompt
    head, _, tail = prompt.partition(marker)
    next_h_idx = min(
        (tail.find(m) for m in ("\n### Example 6", "\n---\n", "\n## ") if tail.find(m) != -1),
        default=len(tail),
    )
    return head + tail[next_h_idx:]


def _extract_prompt_body(text: str) -> str:
    for marker in ("## System prompt", "## System Prompt"):
        if marker in text:
            return text.split(marker, 1)[1].strip()
    return text


def _lobstertrap_test(yaml_text: str) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(yaml_text)
        tmp = Path(f.name)
    try:
        proc = subprocess.run(
            ["./bin/lobstertrap", "test", "--policy", str(tmp)],
            capture_output=True, text=True, timeout=60,
        )
        return proc.returncode == 0, (proc.stderr or proc.stdout)[:300]
    finally:
        tmp.unlink(missing_ok=True)


async def _bench_synth(model: str) -> dict:
    """Run Synthesizer role: hand-tree → YAML → lobstertrap test."""
    client = GeminiClient(default_model=model)
    syn_prompt_path = Path("prompts/synthesizer_agent.md")
    sys_prompt = _strip_example_5(_extract_prompt_body(syn_prompt_path.read_text()))
    user_prompt = (
        "PolicyTree input:\n\n" + json.dumps(HAND_TREE, indent=2) +
        "\n\nReturn a JSON object with one key: yaml_text — the COMPLETE deployable Lobster Trap YAML policy."
    )
    t0 = time.monotonic()
    try:
        out: _Yaml = await client.generate(
            prompt=user_prompt, system_instruction=sys_prompt,
            response_schema=_Yaml, model=model, temperature=0.1,
        )
        latency = time.monotonic() - t0
        passed, msg = _lobstertrap_test(out.yaml_text)
        return {"model": model, "role": "synth", "passed": passed, "latency_s": round(latency, 2),
                "yaml_len": len(out.yaml_text), "msg": msg if not passed else "OK"}
    except Exception as e:
        return {"model": model, "role": "synth", "passed": False, "latency_s": round(time.monotonic() - t0, 2),
                "err": str(e)[:300]}


async def _bench_reader(model: str) -> dict:
    """Run Reader role: SOC 2 doc → PolicyTree."""
    from polaris.agents.reader import PolicyTree
    client = GeminiClient(default_model=model)
    sys_prompt = _extract_prompt_body(Path("prompts/reader_agent.md").read_text())
    doc_text = Path("examples/soc2_excerpt.md").read_text()
    user_prompt = f"DOCUMENT TEXT:\n\n{doc_text}\n\nReturn the JSON object."
    t0 = time.monotonic()
    try:
        tree: PolicyTree = await client.generate(
            prompt=user_prompt, system_instruction=sys_prompt,
            response_schema=PolicyTree, model=model, temperature=0.1,
        )
        latency = time.monotonic() - t0
        return {"model": model, "role": "reader", "passed": len(tree.requirements) >= 3,
                "latency_s": round(latency, 2), "n_reqs": len(tree.requirements),
                "n_high": sum(1 for r in tree.requirements if r.severity == "high")}
    except Exception as e:
        return {"model": model, "role": "reader", "passed": False, "latency_s": round(time.monotonic() - t0, 2),
                "err": str(e)[:300]}


async def main():
    print("\n=== SYNTHESIZER (PRO) — same hand-tree, run lobstertrap test ===")
    results = []
    for m in PRO_MODELS:
        r = await _bench_synth(m)
        results.append(r)
        print(f"  {m:32s} pass={r.get('passed')} t={r.get('latency_s')}s  {r.get('msg', r.get('err',''))[:80]}")

    print("\n=== READER (FLASH) — same SOC 2 doc, count requirements ===")
    for m in FLASH_MODELS:
        r = await _bench_reader(m)
        results.append(r)
        print(f"  {m:32s} pass={r.get('passed')} t={r.get('latency_s')}s reqs={r.get('n_reqs','?')}  {r.get('err','')[:80]}")

    Path("artifacts/model_comparison.json").write_text(json.dumps(results, indent=2))
    print("\nSaved → artifacts/model_comparison.json")


if __name__ == "__main__":
    asyncio.run(main())
