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
        self._client = client or GeminiClient(default_model="gemini-2.5-pro")
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

    # Supplementary rules ALWAYS injected into the synthesised policy so the demo is
    # robust against Lobster Trap's DPI signal dilution on long prompts. We use
    # field-level signals (target_domains) and per-paste-site rules — more reliable than
    # the contains_exfiltration boolean which gets diluted on >100-token prompts.
    # Each rule is a separate ingress entry (Lobster Trap conditions are AND-ed within
    # a rule, so each paste-site domain needs its own rule to OR them).
    _SUPPLEMENTARY_INGRESS_YAML = """
  - name: block_paste_site_pastebin
    description: "Block ingress prompts referencing pastebin.com (data exfiltration vector)"
    priority: 999
    action: DENY
    deny_message: "[POLARIS-SUPP] Blocked: prompt targets pastebin.com (exfiltration vector)."
    conditions:
      - field: target_domains
        match_type: contains
        value: "pastebin.com"
  - name: block_paste_site_transfer_sh
    description: "Block ingress prompts referencing transfer.sh"
    priority: 999
    action: DENY
    deny_message: "[POLARIS-SUPP] Blocked: prompt targets transfer.sh (exfiltration vector)."
    conditions:
      - field: target_domains
        match_type: contains
        value: "transfer.sh"
  - name: block_paste_site_requestbin
    description: "Block ingress prompts referencing requestbin"
    priority: 999
    action: DENY
    deny_message: "[POLARIS-SUPP] Blocked: prompt targets requestbin (exfiltration vector)."
    conditions:
      - field: target_domains
        match_type: contains
        value: "requestbin"
"""

    @classmethod
    def _inject_supplementary_rules(cls, yaml_text: str) -> str:
        """Append our hardcoded supplementary rules under ingress_rules: if not already present.
        Handles three forms of `ingress_rules:`:
          1. `ingress_rules:\\n  - name: ...`     (normal, items follow)
          2. `ingress_rules: []`                  (inline empty list — convert to block)
          3. `ingress_rules:\\n  []`              (block empty list — replace)
        """
        if "block_paste_site_pastebin" in yaml_text:
            return yaml_text
        marker = "ingress_rules:"
        idx = yaml_text.find(marker)
        if idx == -1:
            return yaml_text
        # Detect form 2: `ingress_rules: []`
        line_end = yaml_text.find("\n", idx)
        if line_end == -1:
            line_end = len(yaml_text)
        line = yaml_text[idx:line_end]
        if "[]" in line:
            # convert `ingress_rules: []` → `ingress_rules:\n` + supplementary
            return yaml_text[:idx] + "ingress_rules:\n" + cls._SUPPLEMENTARY_INGRESS_YAML.lstrip("\n") + yaml_text[line_end + 1 :]
        # Forms 1+3: splice after the marker line
        return yaml_text[: line_end + 1] + cls._SUPPLEMENTARY_INGRESS_YAML + yaml_text[line_end + 1 :]

    async def process(self, tree: PolicyTree, *, max_attempts: int = 2) -> SynthesizerResult:
        from polaris.utils.gemini_client import GeminiCallError

        prompt = self._initial_prompt(tree)
        last: TestResults | None = None
        last_llm_out: LLMSynthesizerOutput | None = None
        last_err_msg = ""
        for attempt in range(1, max_attempts + 1):
            try:
                llm_out: LLMSynthesizerOutput = await self._client.generate(
                    prompt=prompt,
                    system_instruction=self._initial_system_prompt,
                    response_schema=LLMSynthesizerOutput,
                    model="gemini-2.5-pro",
                    temperature=0.1,
                )
            except GeminiCallError as e:
                # JSON-parse / output-truncation failures land here. Retry with a hint
                # to keep the YAML brief and well-formed, NOT pad with whitespace.
                last_err_msg = str(e)[:300]
                prompt = (
                    self._initial_prompt(tree)
                    + f"\n\nPREVIOUS ATTEMPT RAW-OUTPUT FAILED: {last_err_msg}\n"
                    + "IMPORTANT: emit a COMPACT YAML — no trailing whitespace, no padding lines, "
                      "no comments. Aim for under 4000 characters total."
                )
                if attempt == max_attempts:
                    raise
                continue
            last_llm_out = llm_out
            # Inject hardcoded supplementary rules BEFORE validation so they're tested too.
            patched_yaml = self._inject_supplementary_rules(llm_out.yaml_text)
            res = await validate(patched_yaml)
            last = res
            if res.passed:
                output = SynthesizerOutput(
                    yaml_text=patched_yaml,
                    declared_intents=_default_declared_intents(),
                )
                return SynthesizerResult(output=output, test_results_summary=res.summary, passed=True)
            prompt = self._retry_prompt(tree, patched_yaml, res)
        assert last_llm_out is not None and last is not None
        return SynthesizerResult(
            output=SynthesizerOutput(
                yaml_text=self._inject_supplementary_rules(last_llm_out.yaml_text),
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
            model="gemini-2.5-pro",
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
