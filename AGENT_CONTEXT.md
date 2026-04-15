# Agent Context

  This file exists so a restarted coding agent can get up to speed quickly in `NTT-learning` without relying on vanished session memory.

  ## Project Identity

  - Project: `NTT-learning`
  - Directory: `/Users/oho/GitClone/CodexProjects/NTT-learning`
  - Goal: build a local-first, notebook-first learning platform for understanding the Number Theoretic Transform in the context of Kyber, with special focus on:
    - forward NTT
    - inverse NTT
    - butterfly structure
    - Cooley-Tukey vs Gentleman-Sande / Sande-style inverse flow
    - layer-by-layer data movement
    - how the algorithm actually plays out in arrays
  - The project should follow the same high standard as `QuantumLearning` in pedagogy, guardrails, notebook design, testing, and local operations.

  ## Core Teaching Judgement

  This topic is confusing because most explanations blur together three different things:

  1. the algebraic purpose of NTT
  2. the in-place butterfly dataflow
  3. the Kyber-specific implementation conventions

  The course must separate those cleanly.

  A learner should not be forced to jump straight into Kyber’s real implementation. The correct staircase is:

  1. ordinary polynomial multiplication / convolution
  2. negacyclic multiplication
  3. tiny toy NTT with very small `n`
  4. butterfly mechanics in isolation
  5. forward vs inverse flow side by side
  6. only then Kyber-specific parameters and indexing
  7. only then the real implementation patterns

  ## Official Course Contract

  The project must have one supported end-to-end walkthrough only.

  Inside notebooks, the visible cell contract must be explicit:

  - `META` cells are route/objective/pacing guidance
  - `MANDATORY` cells are the official walkthrough
  - `FACULTATIVE` cells are optional extensions only

  Difficulty scheme:

  - difficulty `1-3` is reserved for mandatory cells
  - difficulty `4-10` is reserved for facultative cells

  Route notebooks must remain pure route notebooks:
  - they must not contain facultative detours
  - they must not confuse meta-level guidance with technical payload

  Hide plumbing where possible:
  - if widgets are used, learners should see the pedagogical surface, not raw helper code unless that code is itself the lesson

  ## Pedagogical Style

  The strongest style is notebook-first, small-step, highly visual, and highly inspectable.

  Every major concept should be taught through:
  - careful lecture-style explanation
  - array-state snapshots
  - editable examples
  - multiple-choice retrieval checks
  - written reflection prompts
  - “predict the next layer before running it” moments

  The learner must be able to watch:
  - inputs
  - current layer
  - twiddle factor / zeta use
  - pairings
  - outputs after one butterfly stage

  This topic especially needs:
  - explicit diagrams of pairings
  - side-by-side tables of array values after each stage
  - bit-reversal explained visually, not only verbally
  - forward and inverse diagrams compared directly
  - “same structure, opposite direction” intuition for inverse flow

  ## Topic-Specific Judgement

  The course should make clear that Kyber is not just “a generic FFT story with modular arithmetic”.

  The learner must understand:
  - why polynomial multiplication matters
  - why negacyclic structure matters
  - what the transform is buying
  - why Kyber’s parameter choices shape the exact construction
  - what butterflies do locally
  - how local butterfly operations produce the global transform
  - why inverse butterflies undo the forward structure
  - where scaling enters
  - how base multiplication fits between NTT and inverse NTT

  The course must distinguish carefully between:
  - mathematical NTT definition
  - implementation-oriented in-place iterative NTT
  - Kyber’s specific indexing / ordering / twiddle schedule

  ## Proposed Curriculum Spine

  The likely notebook architecture should look like this:

  1. `START_HERE.ipynb`
  2. `COURSE_BLUEPRINT.ipynb`

  Then technical bundles such as:

  ### Foundations
  - polynomial multiplication and convolution
  - negacyclic rings and why Kyber uses them
  - modular arithmetic and roots of unity
  - toy NTT with tiny examples

  ### Butterfly Mechanics
  - what one butterfly does
  - forward Cooley-Tukey butterfly
  - inverse Gentleman-Sande butterfly
  - layer-by-layer traces
  - bit-reversal and ordering

  ### Kyber Mapping
  - Kyber parameters
  - Kyber forward NTT
  - Kyber base multiplication
  - Kyber inverse NTT
  - implementation reading studio

  ### Professional / Debugging
  - common misconceptions
  - debugging wrong twiddle/sign/index mistakes
  - hand-tracing selected stages
  - implementation critique and validation

  Each serious module should follow the same bundle style used successfully elsewhere:

  - `lecture.ipynb`
  - `lab.ipynb`
  - `problems.ipynb`
  - `studio.ipynb`

  ## Operational Expectations

  The repo should be self-service for a normal user.

  Provide repo-local operations such as:
  - bootstrap
  - start
  - stop
  - restart
  - status
  - reset-state
  - validate

  Use a repo-local `.venv`.

  Prefer:
  - local Jupyter
  - bash-first commands
  - repo-local config and runtime files
  - no Docker
  - no cloud dependency
  - no IDE-specific assumptions

  ## Validation Expectations

  The project should include:

  - curriculum / route tests
  - pedagogy tests
  - notebook execution tests
  - browser UX tests where practical
  - repo-local operational docs

  The notebooks should be tested not only for existence, but also for:
  - route consistency
  - required labels
  - mandatory/facultative separation
  - presence of quizzes / exercises / reflections where appropriate
  - visible next-notebook handoff

  ## Immediate Build Priorities

  When starting from an empty repo, do this first:

  1. inspect repo state
  2. create `.venv`
  3. create package / notebook / test / config skeleton
  4. create consumer-facing operational scripts
  5. create the course backbone and route guardrails
  6. build the first serious module around toy convolution and toy butterflies
  7. only then expand to Kyber-specific notebooks

  Do not start by dumping advanced Kyber code into notebooks.

  ## What To Avoid

  Do not:
  - create multiple competing learner routes
  - mix meta guidance with technical payload without clear labels
  - introduce facultative cells into route notebooks
  - overuse abstraction before a learner has seen concrete arrays move
  - assume the learner can infer butterfly flow from equations alone
  - rely on “trust me, this is just FFT-like” explanations

  ## Recommended First Reads For A Restarted Agent

  If a coding agent restarts in this repo, it should:

  1. read this file first
  2. inspect `git status --short --branch`
  3. inspect `git log --oneline -5`
  4. inspect the repo tree
  5. summarize current state and immediate build plan
  6. then execute

  ## One-Line Restart Prompt

  Use this after restarting an agent in this repo:

  `Read AGENT_CONTEXT.md first. Then inspect git status and the repo tree, summarize the current state and constraints, and only then continue the build.`
