import pytest
from pydantic import ValidationError
from polaris.agents.reader import PolicyTree, Requirement


def test_requirement_accepts_valid_lobster_fields():
    r = Requirement(
        id="REQ-001",
        section="SOC 2 CC6.1",
        control_type="credential_exposure",
        human_text="The entity restricts access to information assets to authorized users.",
        rationale="Block credential leakage.",
        severity="high",
        lobster_trap_fields=["contains_credentials", "intent_category"],
        suggested_action="DENY",
    )
    assert r.lobster_trap_fields == ["contains_credentials", "intent_category"]


def test_requirement_rejects_invented_fields():
    with pytest.raises(ValidationError):
        Requirement(
            id="REQ-002",
            section="SOC 2 CC6.1",
            control_type="credential_exposure",
            human_text="x",
            rationale="y",
            severity="high",
            lobster_trap_fields=["contains_dangerous_thoughts"],   # not real
            suggested_action="DENY",
        )


def test_policy_tree_round_trips_json():
    tree = PolicyTree(
        policy_name="t", source_document="t",
        requirements=[Requirement(
            id="REQ-001", section="x", control_type="prompt_injection",
            human_text="x", rationale="y", severity="medium",
            lobster_trap_fields=["contains_injection_patterns"],
            suggested_action="DENY",
        )],
    )
    assert PolicyTree.model_validate_json(tree.model_dump_json()) == tree
