# OWASP Top 10 for LLM Applications (2025)

> Source: OWASP LLM Top 10 project (https://owasp.org/www-project-top-10-for-large-language-model-applications/). Public-domain summary used as Polaris demo input.

## LLM01 — Prompt Injection

A prompt injection vulnerability occurs when an attacker manipulates a large language model (LLM) through crafted inputs, causing the LLM to unknowingly execute the attacker's intentions. This can be done directly by adversarially prompting the system prompt (jailbreak), or indirectly through manipulated external inputs the model later consumes (e.g., contents of a tool-fetched document). Defences include input validation, output filtering, sandboxing tool use, and rate limiting suspicious activity.

## LLM02 — Insecure Output Handling

This vulnerability occurs when an LLM output is accepted without scrutiny, exposing backend systems to risks such as XSS, CSRF, SSRF, privilege escalation, or remote code execution. Output should be validated and encoded before being passed downstream.

## LLM03 — Training Data Poisoning

Training data poisoning refers to manipulation of pretraining data or data involved in fine-tuning to introduce vulnerabilities, backdoors or biases that compromise the model's security, effectiveness or ethical behaviour.

## LLM04 — Model Denial of Service

An attacker interacts with an LLM in a way that consumes an exceptionally high amount of resources, resulting in a decline in service quality and potentially incurring high costs. Includes recursive context expansion, very long inputs, and pathological tool-call chains.

## LLM05 — Supply Chain Vulnerabilities

LLM application supply chain may be vulnerable, impacting the integrity of training data, ML models, and deployment platforms. Includes vulnerabilities in third-party plugins, base models, and pretrained weights.

## LLM06 — Sensitive Information Disclosure

LLM applications can inadvertently disclose sensitive information through their output, leading to unauthorised data access, privacy violations and security breaches. Examples: leaking API keys, customer PII, database contents, or proprietary source code.

## LLM07 — Insecure Plugin Design

LLM plugins can have insecure inputs and insufficient access control. This lack of validation makes them easier to exploit and can result in consequences like remote code execution.

## LLM08 — Excessive Agency

LLM-based systems are often granted a degree of agency by their developer — the ability to interface with other systems and undertake actions in response to a prompt. Excessive agency emerges when the LLM is granted too much autonomy or excessive permissions, allowing it to take unintended actions.

## LLM09 — Overreliance

Overreliance can occur when an LLM produces erroneous information and provides it in an authoritative manner. Overreliance can lead to misinformation, miscommunication, legal issues, and security vulnerabilities.

## LLM10 — Model Theft

Model theft refers to the unauthorised access and exfiltration of LLM models, whether through extraction APIs, parameter theft via repeated queries, or direct theft of stored model artifacts.
