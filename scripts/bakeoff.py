"""Phase 9 bake-off — measure latency × accuracy across model+thinking configs.

Architecture (Block B): use LobsterTrapPolicy as response_schema directly. Gemini returns
typed JSON, we parse to a Policy object, then yaml.safe_dump → ./bin/lobstertrap test.
NO yaml_text string field, NO whitespace bloat surface.

Routes through polaris.utils.gemini_client.GeminiClient (CLAUDE.md §6) so transient
503s get retried — single network blip won't contaminate a config's pass rate.

Persists results to artifacts/bakeoff_results.json AFTER EACH CONFIG so a hang
mid-run doesn't lose all evidence.

Run with: PYTHONUNBUFFERED=1 PYTHONPATH=. uv run python scripts/bakeoff.py 2>&1 | tee /tmp/bakeoff.log
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

from polaris.agents.reader import Reader, PolicyTree
from polaris.lobster.schema import LobsterTrapPolicy
from polaris.utils.gemini_client import GeminiClient

SYSTEM_PROMPT = Path("prompts/synthesizer_agent.md").read_text()
DOCS = ["soc2_excerpt.md", "eu_ai_act_excerpt.md", "owasp_llm_top10.md"]

# (label, model, thinking_dict). Pro models REQUIRE budget>=1024 (verified empirically:
# budget=0 → 400 INVALID_ARGUMENT "only works in thinking mode").
CONFIGS: list[tuple[str, str, dict]] = [
    ("3.1-flash-lite_minimal", "gemini-3.1-flash-lite", {"level": "minimal"}),
    ("3.1-flash-lite_low",     "gemini-3.1-flash-lite", {"level": "low"}),
    ("3.1-flash-lite_medium",  "gemini-3.1-flash-lite", {"level": "medium"}),
    ("3.1-flash-lite_high",    "gemini-3.1-flash-lite", {"level": "high"}),
    ("2.5-pro_1024",           "gemini-2.5-pro",        {"budget": 1024}),
    ("2.5-pro_2048",           "gemini-2.5-pro",        {"budget": 2048}),
    ("2.5-pro_4096",           "gemini-2.5-pro",        {"budget": 4096}),
    ("2.5-pro_8192",           "gemini-2.5-pro",        {"budget": 8192}),
]

TRIALS_PER_DOC = 2
RESULTS_PATH = Path("artifacts/bakeoff_results.json")


def log(msg: str) -> None:
    print(msg, flush=True)


def run_lobstertrap_corpus(yaml_text: str) -> tuple[bool, int]:
    """Returns (all_passed, n_passed_out_of_11)."""
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(yaml_text)
        tmp = Path(f.name)
    try:
        proc = subprocess.run(
            ["./bin/lobstertrap", "test", "--policy", str(tmp)],
            capture_output=True, text=True, timeout=60,
        )
        out = (proc.stderr or "") + (proc.stdout or "")
        n_pass = len(re.findall(r"\[PASS\]", out))
        return proc.returncode == 0, n_pass
    finally:
        tmp.unlink(missing_ok=True)


async def run_one(config_name: str, model: str, thinking: dict, tree: PolicyTree, client: GeminiClient) -> dict:
    """Single Synthesizer run via centralised GeminiClient (gets retry-on-503 for free)."""
    user_prompt = (
        "PolicyTree input:\n\n" + tree.model_dump_json(indent=2) +
        "\n\nReturn a LobsterTrapPolicy. Cover the policy_tree's requirements; produce "
        "as many ingress_rules as the requirements imply. Use unique rule names."
    )
    t0 = time.monotonic()
    fail_kind = None
    err_msg = ""
    try:
        policy: LobsterTrapPolicy = await client.generate(
            prompt=user_prompt,
            system_instruction=SYSTEM_PROMPT,
            response_schema=LobsterTrapPolicy,
            model=model,
            temperature=0.1,
            thinking=thinking,
        )
    except Exception as e:
        return {
            "config": config_name, "elapsed_s": round(time.monotonic() - t0, 1),
            "passed": False, "n_rules": 0, "yaml_size": 0, "lt_corpus_pass": 0,
            "fail_kind": "api_or_parse", "err": str(e)[:200],
        }
    elapsed = round(time.monotonic() - t0, 1)
    try:
        yaml_text = yaml.safe_dump(
            policy.model_dump(mode="json", exclude_none=False),
            sort_keys=False, indent=2,
        )
    except Exception as e:
        return {
            "config": config_name, "elapsed_s": elapsed, "passed": False,
            "n_rules": 0, "yaml_size": 0, "lt_corpus_pass": 0,
            "fail_kind": "yaml_dump", "err": str(e)[:200],
        }
    passed, n_corpus = run_lobstertrap_corpus(yaml_text)
    return {
        "config": config_name, "elapsed_s": elapsed,
        "passed": passed,
        "n_rules": len(policy.ingress_rules) + len(policy.egress_rules),
        "yaml_size": len(yaml_text),
        "lt_corpus_pass": n_corpus,
        "fail_kind": None if passed else "lt_corpus",
    }


async def main():
    log("Building PolicyTrees from 3 docs (Reader)…")
    reader = Reader()
    trees: dict[str, PolicyTree] = {}
    for doc in DOCS:
        text = (Path("examples") / doc).read_text()
        trees[doc] = await reader.process(text)
        log(f"  {doc}: {len(trees[doc].requirements)} reqs")

    results: list[dict] = []
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    last_model: str | None = None
    total = len(CONFIGS) * len(DOCS) * TRIALS_PER_DOC
    log(f"\nRunning {len(CONFIGS)} configs × {len(DOCS)} docs × {TRIALS_PER_DOC} trials = {total} runs")
    for cfg_name, model, thinking in CONFIGS:
        # Cooldown when switching model families (avoid Pro RPM spike right after Lite burst)
        if last_model and last_model != model:
            log(f"[cooldown] switching {last_model} → {model}, sleeping 5s")
            await asyncio.sleep(5)
        client = GeminiClient(default_model=model)
        for doc in DOCS:
            for trial in range(1, TRIALS_PER_DOC + 1):
                r = await run_one(cfg_name, model, thinking, trees[doc], client)
                r["doc"] = doc
                r["trial"] = trial
                r["thinking"] = thinking
                results.append(r)
                tag = "PASS" if r["passed"] else f"FAIL({r.get('fail_kind','?')})"
                err = f" err={r.get('err','')[:80]}" if not r["passed"] else ""
                log(f"  {cfg_name:30s} {doc:25s} t{trial} {r['elapsed_s']:5.1f}s {tag} corpus={r['lt_corpus_pass']}/11 rules={r['n_rules']}{err}")
                await asyncio.sleep(0.5)
        # Persist after each config
        RESULTS_PATH.write_text(json.dumps(results, indent=2))
        log(f"[persist] saved {len(results)} runs to {RESULTS_PATH}")
        last_model = model

    # Aggregate per-config
    log("\n=== PER-CONFIG SUMMARY ===")
    log(f"{'config':30s} pass    lat_med lat_max corpus_avg rules_avg")
    summary: list[dict] = []
    for cfg_name, _, _ in CONFIGS:
        runs = [r for r in results if r["config"] == cfg_name]
        n_pass = sum(1 for r in runs if r["passed"])
        n_total = len(runs)
        lats = sorted(r["elapsed_s"] for r in runs)
        lat_med = lats[len(lats) // 2] if lats else 0
        lat_max = lats[-1] if lats else 0
        corpus_avg = sum(r["lt_corpus_pass"] for r in runs) / max(n_total, 1)
        rules_avg = sum(r["n_rules"] for r in runs) / max(n_total, 1)
        n_api_fail = sum(1 for r in runs if r.get("fail_kind") == "api_or_parse")
        n_corpus_fail = sum(1 for r in runs if r.get("fail_kind") == "lt_corpus")
        s = {
            "config": cfg_name,
            "pass_rate": f"{n_pass}/{n_total}",
            "lat_median_s": lat_med,
            "lat_max_s": lat_max,
            "corpus_avg": round(corpus_avg, 1),
            "rules_avg": round(rules_avg, 1),
            "n_api_fail": n_api_fail,
            "n_corpus_fail": n_corpus_fail,
        }
        summary.append(s)
        log(f"{cfg_name:30s} {n_pass}/{n_total:4} {lat_med:6.1f}  {lat_max:6.1f}  {corpus_avg:8.1f}/11 {rules_avg:8.1f}  api_fail={n_api_fail} corpus_fail={n_corpus_fail}")

    Path("artifacts/bakeoff_summary.json").write_text(json.dumps(summary, indent=2))

    # Pick winner — relaxed gates per reviewer feedback I2:
    # pass_rate >= TRIALS*2 (i.e., 2/3 of total trials), lat_max_s <= 50 (Synthesizer slot)
    min_pass = TRIALS_PER_DOC * len(DOCS) * 2 // 3  # 2/3 of all runs
    survivors = [s for s in summary if int(s["pass_rate"].split("/")[0]) >= min_pass and s["lat_max_s"] <= 50]
    log(f"\nSurvivors (pass≥{min_pass}/{TRIALS_PER_DOC*len(DOCS)} AND lat_max≤50s): {[s['config'] for s in survivors]}")
    if survivors:
        winner = max(survivors, key=lambda s: (s["corpus_avg"], s["rules_avg"], -s["lat_median_s"]))
        log(f"\n[WINNER] {winner['config']}  median={winner['lat_median_s']}s max={winner['lat_max_s']}s "
            f"corpus={winner['corpus_avg']}/11 rules={winner['rules_avg']}")
    else:
        log("\n[NO survivors] sorting all by (corpus_avg DESC, lat_median ASC):")
        for s in sorted(summary, key=lambda x: (-x["corpus_avg"], x["lat_median_s"])):
            log(f"  {s}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
