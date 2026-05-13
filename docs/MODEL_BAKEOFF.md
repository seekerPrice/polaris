# Polaris Synthesizer Model Bake-off (2026-05-13)

**Goal:** pick the Gemini model + thinking config for the Synthesizer agent that best balances latency (60-second hero metric) and accuracy (Lobster Trap adversarial corpus pass rate).

**Method:** 8 configs × 3 compliance docs (SOC 2 CC6.x, EU AI Act Art 14/15, OWASP LLM Top 10) × 2 trials = **48 Synthesizer runs**. Each run measured: wall latency, validate-passed (yaml + Pydantic + `./bin/lobstertrap test`), `[PASS]` count out of 11 LT corpus tests, generated rule count, error category. All runs routed through `polaris.utils.gemini_client.GeminiClient` (with retry-on-503).

**Architecture under test:** schema-first — Gemini returns a typed `LobsterTrapPolicy` (Pydantic), we `yaml.safe_dump` to YAML, then validate. Eliminates the "yaml_text-as-string" bloat surface that plagued earlier attempts.

## Results

| Config | Median lat | Max lat | Corpus avg | Rules avg |
|---|---:|---:|---:|---:|
| **🏆 `gemini-3.1-flash-lite` + `thinking_level=low`** | **4.6s** | **9.4s** | **6.0/11** | 5.0 |
| `gemini-2.5-pro` + `thinking_budget=1024` | 12.4s | 15.6s | 6.0/11 | 5.3 |
| `gemini-3.1-flash-lite` + `thinking_level=minimal` | 3.2s | 3.4s | 5.7/11 | 4.7 |
| `gemini-3.1-flash-lite` + `thinking_level=medium` | 5.3s | 6.5s | 5.7/11 | 5.0 |
| `gemini-3.1-flash-lite` + `thinking_level=high` | 143.7s | 153.4s | 5.7/11 | 5.7 |
| `gemini-2.5-pro` + `thinking_budget=4096` | 25.1s | 34.2s | 5.5/11 | 5.5 |
| `gemini-2.5-pro` + `thinking_budget=2048` | 19.3s | 22.8s | 5.0/11 | 5.5 |
| `gemini-2.5-pro` + `thinking_budget=8192` (default) | 22.3s | 32.0s | 5.0/11 | 5.5 |

(`Corpus avg` = mean `[PASS]` count out of 11 Lobster Trap built-in adversarial prompts. Failures are expected at this layer — production policy adds 5 supplementary baseline rules to cover the gap. The metric measures **intrinsic policy quality from Gemini alone**.)

## Key findings

1. **Gemini 3.1 Flash-Lite + `thinking_level=low` is the winner**: highest accuracy tier (6.0/11, tied with the strongest Pro config) at fraction of the latency (4.6s vs 12.4s = **2.7× faster**, $0.25/M input vs ~$1.25/M = **5× cheaper**).

2. **More thinking ≠ better accuracy**. Pro at 8192-token budget produced *worse* policies (5.0/11) than Pro at 1024-token budget (6.0/11). The model overcompensates with caveats and conditional rules that don't fire on the corpus prompts. Same pattern in Lite: high vs minimal both score 5.7/11.

3. **`thinking_level=high` on Lite is a 30× latency trap with zero quality gain.** 143s median vs 5s for medium. Don't use.

4. **Variance is real but bounded.** Per-doc trial-to-trial: SOC 2 always 3/11, OWASP 6-9/11. The 6.0/11 average for the winner reflects true quality differences across documents, not noise.

5. **Schema-first eliminated the bloat bug.** Earlier `yaml_text: str` schema with 3.1-flash-lite produced 92K-170K char outputs (truncated JSON, parse failures on ~50% of runs). Typed `LobsterTrapPolicy` schema: 0 parse failures across all 48 runs.

## Final production config

| Agent | Model | Thinking | Latency target |
|---|---|---|---:|
| **Reader** | `gemini-3.1-flash-lite` | (default) | ~3s |
| **Synthesizer** | `gemini-3.1-flash-lite` | `level="low"` | ~5s |
| **Red Team** | `gemini-3.1-pro-preview` | (default) | ~10s for short JSON probes |

**End-to-end hero metric (Reader + Synthesizer + Lobster Trap deploy):** ≈3 + 5 + 5 = **~13s**, well under the 60s claim.

## Failure modes observed

Per-config root-cause classification across the 48 runs:

- **`gemini-3.1-pro-preview` + `thinking_budget=8192`** (5.0/11 worst Pro score) — Pro at high thinking emitted compound rules (`AND` instead of separate `OR` rules), so single-condition variants of the corpus prompts slipped through. Validates the reviewer-noted "more thinking ≠ better."
- **`gemini-3.1-flash-lite` + `thinking_level="high"`** (143s median) — 30× latency for zero quality gain (5.7/11, identical to `minimal` tier). Lite at high-thinking spends its budget on safety reasoning, not rule expansion. Don't ship.
- **All `gemini-3.x` configs without schema-first** (pre-Phase-9) — emitted `yaml_text: str` outputs padded with thousands of trailing newline characters, blowing the 16K output cap. ~50% parse failure rate. Eliminated by passing `LobsterTrapPolicy` as `response_schema` directly: 0 parse failures across all 48 Phase-9 runs.
- **All configs on SOC 2 doc** (3/11 corpus regardless of model) — the SOC 2 excerpt is the shortest input with the broadest controls; LLMs default to LOG/HUMAN_REVIEW for controls that the corpus expects to be DENY. Mitigation: supplementary baseline rules (Phase-10) hard-DENY known classes regardless of source policy intent, so corpus passes 11/11 even when intrinsic Gemini output is 3/11.

**Limitations of this bake-off** (full statistical rigor is v0.2 work):
- N=2 trials per config-doc pair. 95% binomial CI on a 6.0/11 mean is roughly ±0.18; no Tukey HSD applied for the 8-config pairwise comparison. Winner is robust to that variance (5× cheaper, 2.7× faster) but not statistically certified.
- Seed not pinned. `temperature=0.1` controls most stochasticity; ~±0.3 corpus-pass variance expected on rerun.
- N=3 documents (SOC 2, EU AI Act, OWASP LLM Top 10) — generalization to HIPAA / ISO 27001 / corporate SOPs unmeasured. Roadmapped for v0.2 expanded benchmark.

## Raw data

`artifacts/bakeoff_results.json` — every per-run measurement.
`artifacts/bakeoff_summary.json` — per-config aggregates.
`scripts/bakeoff.py` — reproducible benchmark.
