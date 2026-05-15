"""Phase 12 T1 — Pre-deploy consent gate (SOC 2 CC8.1 change management).

Distinct from runtime HUMAN_REVIEW (synthesizer.py:148-154, per-request access
control / SOC 2 CC6.1). This gate operates at policy-version granularity:
pauses _pipeline_inner between Synth-validated and _redeploy() until operator
approves or auto-approve timer fires.
"""
from __future__ import annotations

import asyncio

import pytest

from polaris.api.approval import ApprovalDecision, ApprovalGate, ApprovalState


@pytest.mark.asyncio
async def test_gate_emits_awaiting_then_resolves_on_approve():
    gate = ApprovalGate(job_id="abc123def456", policy_sha="deadbeef", auto_approve_after=10.0)
    waiter = asyncio.create_task(gate.wait_for_decision())
    # Yield so wait_for_decision starts blocking before we approve.
    await asyncio.sleep(0)
    assert gate.state is ApprovalState.AWAITING
    gate.approve(approver="operator@polaris.demo")
    result = await waiter
    assert isinstance(result, ApprovalDecision)
    assert result.approved is True
    assert result.approver == "operator@polaris.demo"
    assert gate.state is ApprovalState.APPROVED


@pytest.mark.asyncio
async def test_gate_auto_approves_after_timeout_for_demo_flow():
    gate = ApprovalGate(job_id="abc123def456", policy_sha="deadbeef", auto_approve_after=0.05)
    result = await gate.wait_for_decision()
    assert result.approved is True
    assert result.approver == "auto-approve-demo-mode"
    assert gate.state is ApprovalState.APPROVED


@pytest.mark.asyncio
async def test_gate_blocks_redeploy_on_reject():
    gate = ApprovalGate(job_id="abc123def456", policy_sha="deadbeef", auto_approve_after=10.0)
    waiter = asyncio.create_task(gate.wait_for_decision())
    await asyncio.sleep(0)
    gate.reject(approver="operator@polaris.demo", reason="missing PCI-DSS coverage")
    result = await waiter
    assert result.approved is False
    assert result.reason == "missing PCI-DSS coverage"
    assert gate.state is ApprovalState.REJECTED


@pytest.mark.asyncio
async def test_gate_ignores_double_approve():
    """Defensive: two browser tabs both click 'Approve' — second is no-op."""
    gate = ApprovalGate(job_id="abc123def456", policy_sha="deadbeef", auto_approve_after=10.0)
    waiter = asyncio.create_task(gate.wait_for_decision())
    await asyncio.sleep(0)
    gate.approve(approver="operator-1@polaris.demo")
    gate.approve(approver="operator-2@polaris.demo")
    result = await waiter
    # First approver wins; second silently ignored.
    assert result.approver == "operator-1@polaris.demo"


@pytest.mark.asyncio
async def test_gate_ignores_approve_after_reject():
    gate = ApprovalGate(job_id="abc123def456", policy_sha="deadbeef", auto_approve_after=10.0)
    waiter = asyncio.create_task(gate.wait_for_decision())
    await asyncio.sleep(0)
    gate.reject(approver="op@polaris", reason="nope")
    gate.approve(approver="op@polaris")  # too late
    result = await waiter
    assert result.approved is False
    assert gate.state is ApprovalState.REJECTED
