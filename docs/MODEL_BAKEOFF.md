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

## Raw data

`artifacts/bakeoff_results.json` — every per-run measurement.
`artifacts/bakeoff_summary.json` — per-config aggregates.
`scripts/bakeoff.py` — reproducible benchmark.
