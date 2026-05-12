# Polaris — Claude Code Kickoff

## How to use this file

1. Open your terminal in an empty directory.
2. Drop all the files from this handoff package into that directory (preserving the folder structure).
3. Run `claude` to start Claude Code.
4. Paste the prompt below as your first message. Then follow the daily prompts in `docs/BUILD_PLAYBOOK.md`.

---

## The first prompt (paste this exactly)

```
We are building Polaris, an enterprise AI security tool, for the TechEx Transforming
Enterprise Through AI hackathon. Demo is May 19, submission deadline May 18. Seven days
including today.

Before doing anything else:

1. Read CLAUDE.md in full. It is the single source of truth for this project.
2. Read docs/POLARIS_SPEC.md.
3. Read docs/LOBSTER_TRAP_REFERENCE.md.
4. Read docs/BUILD_PLAYBOOK.md.
5. Read all three files in prompts/.

Once you have read everything, do NOT start coding yet. Instead:

a) Confirm in two or three sentences what Polaris is and how the four agents fit together.
b) List the exact files you will create today (Day 1 — Foundation). Do not include any
   files outside the Day 1 scope from docs/BUILD_PLAYBOOK.md.
c) Tell me what you need from me before we can run the foundation scaffolding (likely
   a Gemini API key, a Go installation, and an example PDF — but ask, do not assume).
d) Propose the exact bash commands you will run to set up the Python project with uv,
   download the Lobster Trap binary, and verify it runs.

Then wait for my approval before executing anything. We move in approved increments.
```

---

## Why this prompt is shaped this way

- **It forces reading first.** Claude Code's default is to dive into code. We don't want that here. The project's complexity is in the integration between Gemini, Lobster Trap, and the demo beats — all of which are documented. Reading saves a day.
- **It demands a confirmation back.** If the model misunderstands Polaris in its summary, we catch it before any code is written.
- **It blocks Day-2-and-beyond work.** The model is explicitly told to scope to Day 1.
- **It demands the bash plan before execution.** This is your last chance to spot a flag mistake or a wrong URL before it runs.

---

## After the first prompt

Once Day 1's scaffolding is approved and running, move to the daily prompts in
`docs/BUILD_PLAYBOOK.md`. There is one canonical prompt per day. Use it. Do not
freestyle prompts unless something is blocked.

When Claude Code finishes a task, end every session with:

```
Update CLAUDE.md section 7 to reflect today's completion. Commit the changes with a
clear message. Then summarize in three bullets what works, what doesn't, and what is
the single most important thing to fix tomorrow.
```

This keeps the project memory alive across sessions. Future Claude Code sessions will
pick up where you left off without you re-explaining the state.

---

## Recovery prompts (when something goes wrong)

**If Claude Code drifts off-scope:**

```
Stop. Re-read section 8 of CLAUDE.md (the demo beats). Does what you are building
appear in those 12 beats? If not, stop building it and confirm.
```

**If a Gemini output keeps failing schema validation:**

```
Show me the last three raw outputs from Gemini, the schema you expect, and the
validation errors. Do NOT change the prompt yet. I want to see the actual mismatch
before we modify anything.
```

**If Lobster Trap won't load a generated policy:**

```
Run ./lobstertrap inspect with one of the test prompts against the failing policy.
Capture the full output. Compare what is being matched against what we expected to
be matched. Then show me — do not fix anything yet.
```

**If the demo agent has flaky behavior:**

```
The demo must be deterministic. Identify every source of nondeterminism: temperature,
random seeds, timing, network. Make a list. Then propose the minimum changes to make
the demo path 100% repeatable. Do not change other code.
```

---

## What to NEVER let Claude Code do

- Add a dependency not on the allowlist in CLAUDE.md section 4.
- Create a feature not appearing in the 12 demo beats (CLAUDE.md section 8).
- Modify the Lobster Trap binary or fork its source. We integrate; we do not patch.
- Skip the `./lobstertrap test` validation gate on generated YAML.
- Bypass the centralized `gemini_client.py` or `lobster/client.py` modules.
- Touch the demo recording until Day 5. Recording earlier means re-recording later, and
  re-recording is where projects die.

If you see any of the above happening, stop the session and reset with:

```
You have violated <specific rule from CLAUDE.md>. Roll back the change. Re-read
CLAUDE.md section <X>. Confirm understanding before continuing.
```
