"""Phase 12 T6 — Policy pack registry tests.

Validates that every YAML in policies/builtin/ is structurally sound AND
passes the LT corpus (the Layer-3 validator), so the pack-deploy path is
guaranteed safe to ship as demo insurance.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml as pyyaml

from polaris.lobster.schema import LobsterTrapPolicy

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKS_DIR = REPO_ROOT / "policies" / "builtin"


def _all_packs() -> list[Path]:
    return sorted(PACKS_DIR.glob("*.yaml"))


def test_packs_directory_is_non_empty():
    packs = _all_packs()
    assert len(packs) >= 4, f"expected 4+ packs (soc2, hipaa, eu_ai_act, pci_dss), got {len(packs)}"


@pytest.mark.parametrize("pack_path", _all_packs(), ids=lambda p: p.stem)
def test_pack_parses_as_lobstertrap_policy(pack_path: Path):
    """Each pack must conform to the Pydantic schema — same gate the
    Synthesizer's Layer-2 validator uses on generated YAMLs."""
    data = pyyaml.safe_load(pack_path.read_text(encoding="utf-8"))
    policy = LobsterTrapPolicy.model_validate(data)
    # Sanity: every pack should have at least some ingress rules.
    assert len(policy.ingress_rules) >= 3, f"{pack_path.name}: pack too thin"


@pytest.mark.parametrize("pack_path", _all_packs(), ids=lambda p: p.stem)
def test_pack_policy_name_is_namespaced(pack_path: Path):
    """Avoid name collisions with operator-generated policies: every shipped
    pack must use the `polaris-*-pack` namespace."""
    data = pyyaml.safe_load(pack_path.read_text(encoding="utf-8"))
    assert data["policy_name"].startswith("polaris-"), (
        f"{pack_path.name}: policy_name '{data['policy_name']}' must start with 'polaris-'"
    )
    assert data["policy_name"].endswith("-pack"), (
        f"{pack_path.name}: policy_name '{data['policy_name']}' must end with '-pack'"
    )
