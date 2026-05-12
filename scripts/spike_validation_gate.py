"""Day-1 spike: hand-write a tiny PolicyTree, ask Gemini using THE REAL Synthesizer system prompt
(prompts/synthesizer_agent.md) to translate it to Lobster Trap YAML, then run ./bin/lobstertrap test.

CRITICAL: this script must use the same prompt-loading path as Phase 3.3.1's Synthesizer.__init__.
Otherwise a passing spike does not predict Phase 3 will pass, and the spike's purpose evaporates.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
from pathlib import Path

from pydantic import BaseModel
from polaris.utils.gemini_client import GeminiClient


SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "synthesizer_agent.md"


HAND_TREE = {
    "policy_name": "spike-soc2-cc6.1",
    "source_document": "SOC 2 CC6.1",
    "requirements": [
        {
            "id": "REQ-001",
            "section": "OWASP LLM01",
            "control_type": "prompt_injection",
            "human_text": "Direct and indirect prompt injection attempts must be blocked.",
            "rationale": "contains_injection_patterns is the primary boolean signal.",
            "severity": "high",
            "lobster_trap_fields": ["contains_injection_patterns"],
            "suggested_action": "DENY",
        },
        {
            "id": "REQ-002",
            "section": "SOC 2 CC6.1",
            "control_type": "credential_exposure",
            "human_text": "The entity restricts access to information assets to authorized users.",
            "rationale": "Block any prompt or response containing API keys, tokens, or passwords.",
            "severity": "high",
            "lobster_trap_fields": ["contains_credentials"],
            "suggested_action": "DENY",
        },
        {
            "id": "REQ-003",
            "section": "SOC 2 CC6.1 / OWASP LLM02",
            "control_type": "file_access",
            "human_text": "Logical access to sensitive system paths must be restricted.",
            "rationale": "Block prompts that reference /etc/, ~/.ssh/, .env, /root/, .aws/credentials, etc.",
            "severity": "high",
            "lobster_trap_fields": ["contains_sensitive_paths"],
            "suggested_action": "DENY",
        },
        {
            "id": "REQ-004",
            "section": "SOC 2 CC6.6 / OWASP LLM07",
            "control_type": "system_command_execution",
            "human_text": "Dangerous system commands (rm -rf, sudo, curl|bash) must not be executed by AI agents.",
            "rationale": "contains_system_commands flag catches shell-injection-style attacks.",
            "severity": "high",
            "lobster_trap_fields": ["contains_system_commands"],
            "suggested_action": "DENY",
        },
        {
            "id": "REQ-005",
            "section": "OWASP LLM06",
            "control_type": "data_exfiltration",
            "human_text": "Prompts attempting to exfiltrate data to attacker-controlled domains must be blocked.",
            "rationale": "Combine intent_category=data_access with target_domains containing paste sites.",
            "severity": "high",
            "lobster_trap_fields": ["contains_exfiltration", "target_domains"],
            "suggested_action": "DENY",
        },
    ],
}


class SpikeOutput(BaseModel):
    # NOTE: Gemini's structured output rejects open dict fields (additionalProperties).
    # Keep this schema flat — yaml_text is the only thing the spike validates.
    yaml_text: str


def _strip_example_5(prompt: str) -> str:
    """Mirror Synthesizer._strip_example_5 — the spike must match Phase 3 behaviour."""
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


async def main() -> int:
    client = GeminiClient(default_model="gemini-3.1-pro-preview")
    raw_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    system_prompt = _strip_example_5(_extract_prompt_body(raw_prompt))

    out: SpikeOutput = await client.generate(
        prompt=(
            "PolicyTree input:\n\n"
            + json.dumps(HAND_TREE, indent=2)
            + "\n\nReturn a SynthesizerOutput JSON with yaml_text and declared_intents."
        ),
        system_instruction=system_prompt,
        response_schema=SpikeOutput,
        model="gemini-3.1-pro-preview",
        temperature=0.1,
    )
    yaml_text = out.yaml_text
    print("---generated yaml---")
    print(yaml_text)

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(yaml_text)
        tmp = Path(f.name)

    try:
        proc = subprocess.run(
            ["./bin/lobstertrap", "test", "--policy", str(tmp)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired as e:
        print("---lobstertrap test TIMED OUT---", e)
        return 2

    print("---lobstertrap test---")
    print("exit:", proc.returncode)
    print("stdout:", proc.stdout)
    print("stderr:", proc.stderr)
    if proc.returncode != 0:
        print("\n[X] SPIKE FAILED — Phase 3 prompt needs work before continuing")
        return 1
    print("\n[OK] SPIKE PASSED — validation gate is reachable from Gemini output via the real prompt")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
