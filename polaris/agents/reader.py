from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# Source: docs/LOBSTER_TRAP_REFERENCE.md §6
ALLOWED_LOBSTER_TRAP_FIELDS: frozenset[str] = frozenset({
    "intent_category", "intent_confidence", "risk_score",
    "contains_code", "contains_credentials", "contains_pii",
    "contains_pii_request", "contains_system_commands",
    "contains_injection_patterns", "contains_file_paths",
    "contains_sensitive_paths", "contains_urls",
    "contains_malware_request", "contains_phishing_patterns",
    "contains_role_impersonation", "contains_exfiltration",
    "contains_harm_patterns", "contains_obfuscation",
    "target_paths", "target_domains", "target_commands", "token_count",
})


def _extract_prompt_body(text: str) -> str:
    """Strip top-of-file meta-commentary (everything before the first '## System prompt'
    or '## System Prompt') so build-process notes don't leak into the model's system
    instruction. Reused by Synthesizer and the spike."""
    for marker in ("## System prompt", "## System Prompt"):
        if marker in text:
            return text.split(marker, 1)[1].strip()
    return text


class Requirement(BaseModel):
    id: str
    section: str
    control_type: Literal[
        "prompt_injection", "data_exfiltration", "credential_exposure",
        "pii_handling", "file_access", "network_egress", "code_execution",
        "role_impersonation", "system_command_execution", "malware_request",
        "obfuscation_detection", "rate_limiting", "human_oversight",
    ]
    human_text: str = Field(min_length=1)
    rationale: str
    severity: Literal["high", "medium", "low"]
    lobster_trap_fields: list[str]
    suggested_action: Literal["DENY", "LOG", "HUMAN_REVIEW", "RATE_LIMIT"]

    @field_validator("lobster_trap_fields")
    @classmethod
    def _all_known(cls, v: list[str]) -> list[str]:
        bad = [f for f in v if f not in ALLOWED_LOBSTER_TRAP_FIELDS]
        if bad:
            raise ValueError(f"unknown lobster_trap_fields: {bad}")
        return v


class PolicyTree(BaseModel):
    policy_name: str
    source_document: str
    requirements: list[Requirement]


class Reader:
    """Reader Agent: parses compliance docs into PolicyTree using gemini-3-flash-preview.

    System prompt body is extracted from prompts/reader_agent.md (CLAUDE.md §6).
    """

    PROMPT_PATH = Path(__file__).parents[2] / "prompts" / "reader_agent.md"

    def __init__(self, client=None) -> None:
        from polaris.utils.gemini_client import GeminiClient
        self._client = client or GeminiClient(default_model="gemini-3-flash-preview")
        self._system_prompt = _extract_prompt_body(self.PROMPT_PATH.read_text(encoding="utf-8"))

    async def process(self, document_text: str, *, max_attempts: int = 3) -> PolicyTree:
        from pydantic import ValidationError
        from polaris.utils.gemini_client import GeminiCallError

        last_err: Exception | None = None
        prompt = f"DOCUMENT TEXT:\n\n{document_text}\n\nReturn the JSON object."
        for _ in range(1, max_attempts + 1):
            try:
                tree: PolicyTree = await self._client.generate(
                    prompt=prompt,
                    system_instruction=self._system_prompt,
                    response_schema=PolicyTree,
                    model="gemini-3-flash-preview",
                    temperature=0.1,
                )
                return tree
            except ValidationError as e:
                last_err = e
                prompt = (
                    f"DOCUMENT TEXT:\n\n{document_text}\n\n"
                    f"PREVIOUS ATTEMPT FAILED VALIDATION:\n{e}\n"
                    "Return a corrected JSON object that conforms exactly to the schema."
                )
            except GeminiCallError:
                # Already retried inside GeminiClient; do not double-retry.
                raise
        raise RuntimeError(f"Reader failed after {max_attempts} validation attempts: {last_err}")
