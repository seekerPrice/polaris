from pathlib import Path
import yaml
import pytest
from polaris.lobster.schema import LobsterTrapPolicy


def test_default_policy_round_trips():
    # Prefer the upstream-fetched copy if present (download_lobstertrap.sh fetches it).
    # Falls back to an in-repo minimal known-good baseline so the test isn't coupled
    # to upstream file movement.
    p = Path("examples/lobstertrap_default_policy.yaml")
    if not p.exists():
        p = Path("examples/lobstertrap_baseline_min.yaml")
    raw = yaml.safe_load(p.read_text())
    pol = LobsterTrapPolicy.model_validate(raw)
    assert pol.policy_name


def test_unknown_field_rejected():
    bad = {
        "policy_name": "x",
        "ingress_rules": [{
            "name": "r", "description": "x", "priority": 100, "action": "DENY",
            "deny_message": "no",
            "conditions": [{"field": "contains_foo", "match_type": "boolean", "value": True}],
        }],
    }
    with pytest.raises(Exception):
        LobsterTrapPolicy.model_validate(bad)


def test_deny_requires_message():
    bad = {
        "policy_name": "x",
        "ingress_rules": [{
            "name": "r", "description": "x", "priority": 100, "action": "DENY",
            "conditions": [{"field": "contains_credentials", "match_type": "boolean", "value": True}],
        }],
    }
    with pytest.raises(Exception):
        LobsterTrapPolicy.model_validate(bad)


def test_modify_action_rejected():
    """MODIFY removed from Action enum entirely (so Gemini's structured-output schema
    doesn't include it). Validation now fails at the enum level instead of the model_validator."""
    bad = {
        "policy_name": "x",
        "ingress_rules": [{
            "name": "r", "description": "x", "priority": 100, "action": "MODIFY",
            "conditions": [{"field": "contains_credentials", "match_type": "boolean", "value": True}],
        }],
    }
    with pytest.raises(Exception):
        LobsterTrapPolicy.model_validate(bad)
