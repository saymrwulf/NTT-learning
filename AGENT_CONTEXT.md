# Agent Context

This file exists so a restarted coding agent can recover quickly in `NTT-learning` without relying on vanished session memory.

## Identity

- Project: `NTT-learning`
- Directory: `/Users/oho/GitClone/CodexProjects/NTT-learning`
- GitHub: `https://github.com/saymrwulf/NTT-learning`
- Branch: `master` only. Do not assume `main`.
- Goal: build the best notebook-first tutorial for understanding NTT / iNTT, especially in the Kyber context, with the real emphasis on:
  - convolution and negacyclic structure
  - direct transform definitions
  - butterfly mechanics
  - CT vs GS flow
  - ordering / bit-reversal / scaling
  - Kyber-specific mapping only after the learner sees the mechanics

Current course shape:

- `27` canonical notebooks total
- `3` route notebooks:
  - `notebooks/START_HERE.ipynb`
  - `notebooks/COURSE_BLUEPRINT.ipynb`
  - `notebooks/COURSE_COMPLETE.ipynb`
- `24` technical notebooks across `6` bundles:
  - `foundations/01_convolution_to_toy_ntt`
  - `foundations/02_negative_wrapped_ntt`
  - `butterfly_mechanics/03_fast_forward_ct`
  - `butterfly_mechanics/04_fast_inverse_gs`
  - `kyber_mapping/05_kyber_ntt_and_base_multiplication`
  - `professional/06_debugging_ntt_failures`

## Non-Negotiable User Rules

These are not optional style preferences. Future agents should assume these are hard requirements.

- Read this file first on restart.
- Inspect `git status --short --branch`, `git log --oneline -8`, and the repo tree before acting.
- Work autonomously after that. Do not ask the user to re-explain the project state.
- Always commit and push before returning a final answer.
- Never return with a dirty worktree. Final `git status --short` should be empty.
- UX is first-order priority. If the learner can get lost, the UX is wrong.
- The user is strongly visual and struggles when asked to imagine array motion abstractly.
- Abstractions are bad for this teaching goal unless they come after concrete motion and visuals.
- The course should be blunt, graphical, dynamic, and foolproof.
- If one animation or notebook interaction breaks, assume the bug may be systemic across other players and test broadly.

## Core Teaching Judgement

The course must keep these stories separate:

1. the algebraic purpose of the transform
2. the local in-place butterfly dataflow
3. the Kyber-specific implementation conventions

The learner staircase should remain:

1. ordinary polynomial multiplication / convolution
2. cyclic vs negacyclic folding
3. tiny direct NTT / INTT examples
4. butterfly mechanics in isolation
5. forward vs inverse flow side by side
6. ordering / bit-reversal / scaling
7. Kyber parameter reality and base multiplication
8. only then implementation-reading / debugging studios

Do not dump advanced Kyber implementation detail before the learner has seen small arrays move.

## Current Notebook Contract

There is one official learner route only.

The internal cell-role contract still exists:

- `meta`
- `mandatory`
- `facultative`

Difficulty still means:

- `1-3` reserved for mandatory cells
- `4-10` reserved for facultative cells

Important UX rule:

- Raw `META`, `MANDATORY`, and `FACULTATIVE` labels must **not** appear as notebook headlines.
- Content headings must be about the content itself.
- Role and pacing information may appear only through subtle chrome such as colored cards / chips / level badges.

Route notebooks stay pure:

- markdown only
- no facultative detours
- clear route guidance
- clickable navigation only

Every canonical notebook must have:

- a top route-guardrails cell
- a bottom next-notebook handoff cell
- clickable `Previous`, `Next`, and `Restart route` recovery links

Never make the learner choose the next notebook manually from the file tree.

## Current Architecture

Source-of-truth files:

- `tools/render_notebooks.py`
  - notebook generator
  - route guardrails / handoff cells
  - notebook chrome
  - learner-facing header styling
- `ntt_learning/course.py`
  - course constants
  - route sequence
  - bundle definitions
- `ntt_learning/toy_ntt.py`
  - inspectable math helpers
  - toy NTT / INTT
  - CT / GS traces
  - pairings and stage helpers
- `ntt_learning/visuals.py`
  - interactive players
  - plots
  - rendering behavior
- `scripts/app.sh`
  - Jupyter lifecycle source of truth
- `tests/`
  - contract
  - execution
  - repo ops
  - visual UX

Do not hand-edit notebook structure when the change belongs in the generator. Change `tools/render_notebooks.py`, then regenerate canonical notebooks.

## Current Rendering / Animation Rules

This section matters because several UX regressions already happened here.

### Stable rules

- `schoolbook_diagonal_player(...)` is HTML-board based, not SVG.
- `wraparound_comparison_player(...)` is HTML-board based, not SVG.
- The wraparound player was explicitly rewritten because the SVG version jittered and collided.
- `direct_ntt_player(...)` and `butterfly_story_player(...)` still use SVG, but:
  - they must render inside horizontal-scroll frames
  - their SVG canvases must not shrink to fit the viewport
  - they must use fixed canvas widths with `max-width:none` / `min-width`
- Player captions should have a fixed minimum height to reduce layout shift.

### Practical lesson

Dense explanatory text inside shrinking SVG is a bad idea here.

If a player shows:

- text collisions
- jitter between frames
- section labels jumping vertically
- numbers painting over other numbers

then first suspect:

- shrinking SVG layout
- variable-height captions
- too many text bands inside the same visual corridor

### Regression discipline

When fixing one player:

- test the other players too
- extend `tests/test_visuals.py`
- test the failure mode itself, not just “widget exists”

## Current Visual / UX Expectations

The user explicitly rejected “nice enough” visuals. Treat these as hard constraints:

- The course should feel plastic and inspectable.
- The learner should be able to watch values move, not infer motion from prose.
- Graphics are not decorative. They are the lesson.
- UX must be foolproof from `START_HERE` to `COURSE_COMPLETE`.
- The first notebooks matter disproportionately. Weak early visuals destroy trust quickly.

The user also explicitly said:

- abstractions suck for this purpose
- they need to see it
- they are disappointed by pretty-but-useless pictures

Design decisions must be judged against that standard.

## Jupyter / Ops State

The Jupyter lifecycle is aligned with the cross-project manager spec.

Use `scripts/app.sh` as the source of truth:

- `bootstrap`
- `start`
- `stop`
- `restart`
- `status`
- `logs`
- compatibility:
  - `validate`
  - `reset-state`

Important operational constraints:

- Jupyter dirs are isolated inside the repo:
  - `.jupyter_config`
  - `.jupyter_data`
  - `.jupyter_runtime`
  - `.ipython`
  - `.cache`
  - `.logs`
  - `.run`
- Kernel is installed with `--sys-prefix`
- Port allocation scans `8888-8899`
- PID file lives at `.logs/jupyter.pid` and mirrors to `.run/jupyter.pid`
- `start` supports background and foreground modes
- `stop` uses graceful termination before kill fallback

## Validation State

Current validation expectation:

- run `bash scripts/validate.sh` before finalizing meaningful work

Current suite count:

- `32` tests at the time this file was updated

Current test coverage includes:

- `tests/test_course_contract.py`
  - notebook existence
  - role / difficulty metadata
  - route purity
  - no raw role labels as notebook headlines
  - handoff / route-nav presence
- `tests/test_notebook_execution.py`
  - code cells execute as plain Python
- `tests/test_toy_ntt.py`
  - math helpers
  - trace examples
  - round trips
- `tests/test_repo_ops.py`
  - scripts / repo-local operations
- `tests/test_visuals.py`
  - schoolbook HTML player behavior
  - wraparound HTML stability
  - non-shrinking SVG player behavior
  - slider update behavior
  - fixed caption-height behavior

Important truth:

- there are still no real browser-level screenshot/playback tests
- if future visual regressions keep slipping through, raising the testing bar further is a real priority

## Repo Hygiene Gotchas

This repo has one recurring trap: Jupyter notebook noise.

Running or opening tracked notebooks in Jupyter can mutate:

- execution counts
- outputs
- metadata
- cell ids

Those diffs are often not intended course changes.

Before finalizing work:

1. inspect `git diff` on dirty notebooks
2. if the diffs are only autosave / execution noise, restore them
3. only commit notebook diffs that represent intentional canonical content changes

Do not return to the user with notebook autosave noise still dirty.

Ignored local-only file:

- `Complete Beginner Guide to the Number Theoretic Transform (NTT).pdf`

It is a local reference artifact and is intentionally ignored.

## Current Restart Checklist

On a fresh restart in this repo, do this in order:

1. read `AGENT_CONTEXT.md`
2. run `git status --short --branch`
3. run `git log --oneline -8`
4. inspect the repo tree
5. if the tree is dirty, inspect diffs immediately
6. classify notebook diffs as:
   - intentional canonical content changes
   - or autosave / execution noise
7. summarize current state and constraints
8. continue autonomously

Before final answer:

1. run relevant tests
2. run `bash scripts/validate.sh` if the change is substantial
3. commit
4. push to `origin master`
5. verify `git status --short` is empty

## Recent Important Commits

These are useful waypoints for recovery:

- `0955ede` Ignore local reference PDF
- `934586e` Replace jittery wraparound animation
- `5f41121` Fix wraparound animation label collisions
- `b3b1885` Harden notebook animation rendering
- `5d267ee` Fix notebook headings and schoolbook UX
- `5aad355` Improve notebook chrome and player responsiveness
- `f152567` Replace early notebook plots with teaching players
- `74700b8` Add foolproof notebook route navigation

## One-Line Restart Prompt

Use this after restarting an agent in this repo:

`Read AGENT_CONTEXT.md first. Then inspect git status, git log, dirty diffs, and the repo tree, summarize the current state and constraints, clean incidental notebook noise if needed, and continue autonomously.`
