# Security Policy

## Status

Polaris v0.1 is a **hackathon prototype** built in 6 days for the TechEx Veea Trust Track (May 19, 2026). It is functional and live-verified but has not undergone third-party security review. Do not deploy to production without an independent audit.

## Reporting a vulnerability

If you find a security issue, please email **lucaslootan@gmail.com** with a description and reproduction steps. Please do **not** open a public GitHub issue for security reports.

## Known limitations

- Single-user demo posture: no auth, no rate limiting on the Polaris API itself (rate limits are within the synthesized Lobster Trap policy, not the management surface).
- CORS is permissive (`allow_origins=["*"]`) for the demo. Tighten before any non-localhost deployment.
- Gemini API key is read from environment / `.env` only. The centralized client masks the key in logs (`polaris/utils/gemini_client.py`).
- Lobster Trap binary is downloaded at install time from upstream; pin a known-good SHA in `scripts/download_lobstertrap.sh` for reproducible builds.

## Threat model addressed

Polaris-generated policies defend against the **OWASP LLM Top 10 (2025)** classes covered in `docs/POLARIS_SPEC.md` §4.1 — prompt injection (direct + indirect), data exfiltration, sensitive-path access, system-command injection, role impersonation, and obfuscated payloads. The closed-loop Red Team agent verifies coverage and surfaces gaps.

## Out of scope

- Side-channel attacks against the Gemini API.
- Compromise of the host running Lobster Trap.
- DoS against the Polaris control plane (synthesized policy rate-limits LLM traffic, not the dashboard).
