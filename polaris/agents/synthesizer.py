from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from polaris.agents.reader import PolicyTree, _extract_prompt_body
from polaris.lobster.validator import TestResults, validate
from polaris.utils.gemini_client import GeminiClient


class IntentSchemaTool(BaseModel):
    intent: str
    expected_paths: list[str] = Field(default_factory=list)
    expected_domains: list[str] = Field(default_factory=list)


class IntentSchema(BaseModel):
    default_intent: str
    tool_intents: dict[str, IntentSchemaTool] = Field(default_factory=dict)


# IMPORTANT: Gemini's structured output rejects open dict fields (`additionalProperties`).
# `LLMSynthesizerOutput` is the schema sent to Gemini — yaml_text only.
# `SynthesizerOutput` is the public type (yaml + declared_intents synthesised in Python from
# a per-agent template, since declared_intents is deterministic per agent_id).
class LLMSynthesizerOutput(BaseModel):
    yaml_text: str


class SynthesizerOutput(BaseModel):
    yaml_text: str
    declared_intents: dict[str, IntentSchema] = Field(default_factory=dict)


class SynthesizerResult(BaseModel):
    output: SynthesizerOutput
    test_results_summary: str
    passed: bool


# Per-agent declared_intent template. See prompts/synthesizer_agent.md "Declared intents schema".
def _default_declared_intents() -> dict[str, IntentSchema]:
    return {
        "sales-ops-copilot-v1": IntentSchema(
            default_intent="communication",
            tool_intents={
                "read_customer_feedback": IntentSchemaTool(
                    intent="file_io",
                    expected_paths=["/home/*/customer_feedback*.txt", "/tmp/*", "examples/customer_feedback*.txt"],
                    expected_domains=[],
                ),
                "post_summary_to_slack": IntentSchemaTool(
                    intent="communication",
                    expected_paths=[],
                    expected_domains=["hooks.slack.com", "*.slack.com"],
                ),
            },
        ),
    }


class Synthesizer:
    PROMPT_PATH = Path(__file__).parents[2] / "prompts" / "synthesizer_agent.md"

    # Marker headers in prompts/synthesizer_agent.md. Initial generation must NOT see
    # Example 5 (block_obfuscated_exfiltration), or Gemini will preemptively include
    # that rule and there will be no Day-5 Red Team gap to demonstrate.
    _EXAMPLE_5_HEADER = "### Example 5 — Block obfuscated payloads (Red Team-discovered class)"

    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client or GeminiClient(default_model="gemini-3.1-pro-preview")
        full = _extract_prompt_body(self.PROMPT_PATH.read_text(encoding="utf-8"))
        self._initial_system_prompt = self._strip_example_5(full)
        self._regen_system_prompt = full

    @classmethod
    def _strip_example_5(cls, prompt: str) -> str:
        """Remove ONLY the Example 5 block (between its header and the next ### or ## header)."""
        if cls._EXAMPLE_5_HEADER not in prompt:
            return prompt
        head, _, tail = prompt.partition(cls._EXAMPLE_5_HEADER)
        next_h_idx = min(
            (tail.find(marker) for marker in ("\n### Example 6", "\n---\n", "\n## ") if tail.find(marker) != -1),
            default=len(tail),
        )
        return head + tail[next_h_idx:]

    async def process(self, tree: PolicyTree, *, max_attempts: int = 3) -> SynthesizerResult:
        prompt = self._initial_prompt(tree)
        last: TestResults | None = None
        last_llm_out: LLMSynthesizerOutput | None = None
        for _ in range(1, max_attempts + 1):
            llm_out: LLMSynthesizerOutput = await self._client.generate(
                prompt=prompt,
                system_instruction=self._initial_system_prompt,
                response_schema=LLMSynthesizerOutput,
                model="gemini-3.1-pro-preview",
                temperature=0.1,
            )
            last_llm_out = llm_out
            res = await validate(llm_out.yaml_text)
            last = res
            if res.passed:
                output = SynthesizerOutput(
                    yaml_text=llm_out.yaml_text,
                    declared_intents=_default_declared_intents(),
                )
                return SynthesizerResult(output=output, test_results_summary=res.summary, passed=True)
            prompt = self._retry_prompt(tree, llm_out.yaml_text, res)
        assert last_llm_out is not None and last is not None
        return SynthesizerResult(
            output=SynthesizerOutput(
                yaml_text=last_llm_out.yaml_text,
                declared_intents=_default_declared_intents(),
            ),
            test_results_summary=last.summary,
            passed=False,
        )

    async def regenerate(
        self, tree: PolicyTree, gap_evidence: dict[str, Any], previous_yaml: str
    ) -> SynthesizerResult:
        prompt = (
            f"REGENERATION MODE.\n\nPrevious policy:\n{previous_yaml}\n\n"
            f"Red Team Agent gap:\n{gap_evidence}\n\n"
            "Generate an updated yaml_text that closes this gap WITHOUT removing existing rules. "
            "Add the minimal set of new rules.\n\n"
            f"Original tree:\n{tree.model_dump_json(indent=2)}"
        )
        llm_out: LLMSynthesizerOutput = await self._client.generate(
            prompt=prompt,
            system_instruction=self._regen_system_prompt,
            response_schema=LLMSynthesizerOutput,
            model="gemini-3.1-pro-preview",
            temperature=0.1,
        )
        res = await validate(llm_out.yaml_text)
        return SynthesizerResult(
            output=SynthesizerOutput(
                yaml_text=llm_out.yaml_text,
                declared_intents=_default_declared_intents(),
            ),
            test_results_summary=res.summary,
            passed=res.passed,
        )

    @staticmethod
    def _initial_prompt(tree: PolicyTree) -> str:
        return (
            "PolicyTree input:\n\n"
            + tree.model_dump_json(indent=2)
            + "\n\nReturn a JSON object with one key: yaml_text — the COMPLETE deployable Lobster Trap YAML policy."
        )

    @staticmethod
    def _retry_prompt(tree: PolicyTree, prev_yaml: str, res: TestResults) -> str:
        # Validation feedback with concrete remediation hints.
        hints: list[str] = []
        if res.parse_error:
            hints.append("- YAML must be 2-space-indented, no tabs, lowercase booleans (true/false).")
        for err in (res.schema_errors or []):
            el = err.lower()
            if "boolean" in el or "bool" in el:
                hints.append("- Boolean signal fields must use match_type: boolean with value: true/false.")
            if "unknown metadata field" in el:
                hints.append("- Use ONLY the 22 fields listed in the system prompt; no inventions.")
            if "deny_message" in el:
                hints.append("- Every action: DENY rule needs a deny_message string.")
            if "rule names must be unique" in el:
                hints.append("- Rule names must be unique across ingress_rules + egress_rules.")
            if "reserved" in el:
                hints.append("- Do NOT emit MODIFY or REDIRECT actions; they are reserved.")
        if res.lt_stderr:
            hints.append(f"- Lobster Trap test stderr: {res.lt_stderr[:300]}")
        return (
            "Previous attempt:\n" + prev_yaml +
            f"\n\nValidation FAILED: {res.summary}\n"
            "Concrete fixes to apply:\n" + "\n".join(hints) + "\n\n"
            "Return a corrected SynthesizerOutput JSON.\n\n"
            "PolicyTree:\n" + tree.model_dump_json(indent=2)
        )
