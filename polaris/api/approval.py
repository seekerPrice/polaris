"""Pre-deploy consent gate (Phase 12 T1).

Pauses _pipeline_inner between Synth-validated and _redeploy() so an operator
approves the policy version before it goes live. Maps to SOC 2 CC8.1 (change
management) — distinct from runtime HUMAN_REVIEW (synthesizer.py:148-154), which
is per-request access control (CC6.1).

Single-shot async gate per (job_id, policy_sha). The pipeline awaits
wait_for_decision(); the HTTP /approve and /reject endpoints call approve() or
reject() on the gate to resolve it. auto_approve_after fires the demo-mode
default if neither endpoint is hit within the timeout, so live recording isn't
held hostage to a click.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)


class ApprovalState(str, Enum):
    AWAITING = "AWAITING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    approver: str
    decided_at: float
    reason: str | None = None


class ApprovalGate:
    """One-shot async gate. wait_for_decision() resolves when approve()/reject()
    is called OR after auto_approve_after seconds (demo-mode default 3.0).
    auto_approve_after is intended for demo continuity; production callers
    should pass a large timeout (or sys.maxsize) to require explicit operator
    action."""

    def __init__(self, job_id: str, policy_sha: str, *, auto_approve_after: float = 3.0) -> None:
        self.job_id = job_id
        self.policy_sha = policy_sha
        self.auto_approve_after = auto_approve_after
        self.state = ApprovalState.AWAITING
        self._event = asyncio.Event()
        self._decision: ApprovalDecision | None = None

    def approve(self, approver: str) -> None:
        if self.state is not ApprovalState.AWAITING:
            log.info(
                "approval.approve ignored — already %s for job %s sha %s",
                self.state.value, self.job_id, self.policy_sha,
            )
            return
        self._decision = ApprovalDecision(
            approved=True, approver=approver, decided_at=time.time(),
        )
        self.state = ApprovalState.APPROVED
        self._event.set()

    def reject(self, approver: str, reason: str) -> None:
        if self.state is not ApprovalState.AWAITING:
            log.info(
                "approval.reject ignored — already %s for job %s sha %s",
                self.state.value, self.job_id, self.policy_sha,
            )
            return
        self._decision = ApprovalDecision(
            approved=False, approver=approver, decided_at=time.time(), reason=reason,
        )
        self.state = ApprovalState.REJECTED
        self._event.set()

    async def wait_for_decision(self) -> ApprovalDecision:
        try:
            await asyncio.wait_for(self._event.wait(), timeout=self.auto_approve_after)
        except asyncio.TimeoutError:
            # Demo-mode safety: auto-approve so the pipeline doesn't deadlock if
            # nobody clicks. The approver string is distinctive so audit logs
            # show which deploys went out unattended.
            self.approve(approver="auto-approve-demo-mode")
        assert self._decision is not None, "approve()/reject() must set _decision before _event"
        return self._decision
