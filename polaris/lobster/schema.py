from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Action(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    LOG = "LOG"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    MODIFY = "MODIFY"
    QUARANTINE = "QUARANTINE"
    RATE_LIMIT = "RATE_LIMIT"
    REDIRECT = "REDIRECT"


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
    value: Any
    negate: bool = False

    @field_validator("field")
    @classmethod
    def _known(cls, v: str) -> str:
        if v not in METADATA_FIELDS:
            raise ValueError(f"unknown metadata field: {v}")
        return v


_RESERVED_ACTIONS = {Action.MODIFY, Action.REDIRECT}


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

    @model_validator(mode="after")
    def _no_reserved_actions(self):
        if self.action in _RESERVED_ACTIONS:
            raise ValueError(f"action {self.action.value} is reserved, do not emit")
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
        names = [r.name for r in self.ingress_rules + self.egress_rules]
        if len(names) != len(set(names)):
            raise ValueError("rule names must be unique across ingress and egress")
        return self
