# Security Policy

## Status

Polaris v0.1 is a **hackathon prototype** built in 6 days for the TechEx Veea Trust Track (May 19, 2026). It is functional and live-verified but has not undergone third-party security review. Do not deploy to production without an independent audit.

## Reporting a vulnerability

If you find a security issue, please email **lucaslootan@gmail.com** with a description and reproduction steps. Please do **not** open a public GitHub issue for security reports.

## Threat model

Polaris's Red Team Agent operates under a **white-box adaptive attacker** model: the attacker can read `policy.yaml`, audit logs, and previous probes, and may re-probe after the Synthesizer regenerates the policy. Probe horizon is **single-stage** (no multi-turn jailbreak chains) in v0.1. Out of scope: multi-turn adaptive adversaries, side-channel attacks against the Gemini API, compromise of the host running Lobster Trap, and DoS against the Polaris control plane (the synthesized policy rate-limits LLM traffic, not the dashboard).

## Threats addressed

Polaris-generated policies defend against the **OWASP LLM Top 10 (2025)** classes covered in `docs/POLARIS_SPEC.md` §4.1 — prompt injection (direct + indirect), data exfiltration, sensitive-path access, system-command injection, role impersonation, and obfuscated payloads (base64/ROT13/homoglyph). The closed-loop Red Team agent verifies coverage and surfaces gaps; verified gaps trigger Synthesizer regeneration with an obfuscation-class fallback (deterministic `_inject_obfuscation_closure` for regex-DPI blind spots).

## Known limitations (v0.1)

- **Single-document input**: cross-document fusion (SOC 2 + HIPAA + EU AI Act merged into one policy) is roadmapped for v0.2. v0.1 ships one policy per upload.
- **No PII redaction before Gemini**: prompts are sent to Google Gemini verbatim. For regulated workloads, pair with on-premises redaction (e.g., Microsoft Presidio) or wait for v0.2's BAA-mode shim.
- **No authentication / RBAC**: the Polaris API has no auth — single-operator deployment posture. v0.2 will add OAuth2 + 4-eyes policy approval.
- **Audit log not tamper-evident**: JSONL + SQLite, no HMAC chain. Acceptable for development; v0.2 will add append-only signing for SOC 2 Type II / HIPAA §164.312(b) compatibility.
- **No outage fallback (partial)**: if Gemini or LT goes down mid-pipeline, the in-flight job fails. Phase-11 ships `policies/default_baseline.yaml` (deny-all) so the next deploy attempt has a known-safe target; v0.2 will add automatic baseline reversion on Synth failure.
- **Lobster Trap binary not signature-verified**: `scripts/download_lobstertrap.sh` pins to commit SHA but doesn't verify GPG signature. Recommended for production: verify Veea's release signature out-of-band.
- **CORS is permissive** (`allow_origins=["*"]`) for the demo. Tighten before any non-localhost deployment.
- **Gemini API key**: read from environment / `.env` only. The centralized client masks the key in logs (`polaris/utils/gemini_client.py`). Operators must rotate the key post-incident.

## Out of scope

- Side-channel attacks against the Gemini API.
- Compromise of the host running Lobster Trap.
- DoS against the Polaris control plane (synthesized policy rate-limits LLM traffic, not the dashboard).
