from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Action(str, Enum):
    """Lobster Trap actions Polaris emits. MODIFY and REDIRECT are RESERVED per
    LOBSTER_TRAP_REFERENCE.md §4 — REMOVED from the enum so Gemini's structured-output
    schema doesn't include them and the model never tries to emit them."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    LOG = "LOG"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    QUARANTINE = "QUARANTINE"
    RATE_LIMIT = "RATE_LIMIT"


class MatchType(str, Enum):
    exact = "exact"
    prefix = "prefix"
    glob = "glob"
    regex = "regex"
    contains = "contains"
    boolean = "boolean"
    threshold = "threshold"
    range = "range"


METADATA_FIELDS: frozenset[str] = frozenset({
    "intent_category", "intent_confidence", "risk_score",
    "contains_code", "contains_credentials", "contains_pii", "contains_pii_request",
    "contains_system_commands", "contains_injection_patterns", "contains_file_paths",
    "contains_sensitive_paths", "contains_urls", "contains_malware_request",
    "contains_phishing_patterns", "contains_role_impersonation", "contains_exfiltration",
    "contains_harm_patterns", "contains_obfuscation",
    "target_paths", "target_domains", "target_commands", "token_count",
})

INTENT_CATEGORIES = frozenset({
    "code_execution", "file_io", "network", "system",
    "communication", "credential_access", "data_access", "general",
})


class Condition(BaseModel):
    field: str
    match_type: MatchType
    # Gemini structured-output rejects `Any` (no `type` key in JSON schema). Use a union
    # of all the concrete value types LT match_types accept. Bool MUST come before str/int
    # in the union so Pydantic v2's smart-union picks bool for JSON `true`/`false` instead
    # of coercing to int (true→1). Strings like "true" still validate as str.
    value: bool | int | float | str | None = None
    negate: bool = False

    @field_validator("field")
    @classmethod
    def _known(cls, v: str) -> str:
        if v not in METADATA_FIELDS:
            raise ValueError(f"unknown metadata field: {v}")
        return v

    @model_validator(mode="after")
    def _value_type_matches_match_type(self):
        # L16/L17 fix (deep-check 2026-05-13): enforce match_type ↔ value-type pairing in
        # Layer 2 so the Synthesizer's retry loop sees a clear Pydantic error instead of
        # the binary's opaque rejection. boolean→bool, threshold→numeric, everything else
        # →str. None remains allowed only on non-boolean/threshold types where LT treats
        # missing as "any value".
        if self.value is None:
            return self
        if self.match_type == MatchType.boolean and not isinstance(self.value, bool):
            raise ValueError(f"match_type=boolean requires bool value, got {type(self.value).__name__}")
        if self.match_type == MatchType.threshold:
            # `isinstance(True, int)` is True in Python — exclude bool explicitly so
            # `match_type=threshold, value=True` doesn't sneak through as a "numeric".
            if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
                raise ValueError(f"match_type=threshold requires numeric value, got {type(self.value).__name__}")
        return self


# MODIFY/REDIRECT removed from Action enum entirely — Gemini sees the schema's
# enum constants and would otherwise emit them, blowing up our validator. Removing
# from the enum is cleaner than rejecting them post-hoc.


class Rule(BaseModel):
    name: str
    description: str
    priority: int = Field(ge=1, le=1000)
    action: Action
    deny_message: str | None = None
    conditions: list[Condition] = Field(min_length=1)

    @model_validator(mode="after")
    def _deny_needs_message(self):
        if self.action == Action.DENY and not self.deny_message:
            raise ValueError("DENY action requires deny_message")
        return self


class RateLimits(BaseModel):
    requests_per_minute: int = 120
    requests_per_hour: int = 2000
    burst_threshold: int = 30


class NetworkPolicy(BaseModel):
    egress_policy: Literal["allowlist", "denylist"] = "denylist"
    allowed_domains: list[str] = Field(default_factory=list)
    denied_domains: list[str] = Field(default_factory=list)


class FilesystemPolicy(BaseModel):
    denied_paths: list[str] = Field(default_factory=list)
    allowed_read_paths: list[str] = Field(default_factory=list)
    allowed_write_paths: list[str] = Field(default_factory=list)


class LobsterTrapPolicy(BaseModel):
    version: str = "1.0"
    policy_name: str
    default_action: Action = Action.ALLOW
    ingress_rules: list[Rule] = Field(default_factory=list)
    egress_rules: list[Rule] = Field(default_factory=list)
    rate_limits: RateLimits = Field(default_factory=RateLimits)
    network: NetworkPolicy = Field(default_factory=NetworkPolicy)
    filesystem: FilesystemPolicy = Field(default_factory=FilesystemPolicy)

    @model_validator(mode="after")
    def _unique_rule_names(self):
        # L18 fix (deep-check 2026-05-13): LT keys rule names by (direction, name) per the
        # reference doc — so `block_pii` can legitimately exist in both ingress AND egress.
        # Check uniqueness within each list separately.
        for kind, rules in (("ingress", self.ingress_rules), ("egress", self.egress_rules)):
            names = [r.name for r in rules]
            if len(names) != len(set(names)):
                raise ValueError(f"{kind}_rules names must be unique within {kind}")
        return self
