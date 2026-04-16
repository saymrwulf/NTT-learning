# NTT-learning

`NTT-learning` is a local-first, notebook-first course repo for understanding the Number Theoretic Transform in the context of Kyber.

The project is built around one supported learner route:

1. `notebooks/START_HERE.ipynb`
2. `notebooks/COURSE_BLUEPRINT.ipynb`
3. Each bundle in `Lecture -> Lab -> Problems -> Studio` order:
   - `notebooks/foundations/01_convolution_to_toy_ntt/`
   - `notebooks/foundations/02_negative_wrapped_ntt/`
   - `notebooks/butterfly_mechanics/03_fast_forward_ct/`
   - `notebooks/butterfly_mechanics/04_fast_inverse_gs/`
   - `notebooks/kyber_mapping/05_kyber_ntt_and_base_multiplication/`
   - `notebooks/professional/06_debugging_ntt_failures/`
4. `notebooks/COURSE_COMPLETE.ipynb`

The current build covers convolution, negacyclic folding, direct `NTTψ` / `INTTψ`, fast CT/GS butterfly schedules, ordering and scaling, Kyber modulus reality, base multiplication, and debugging fingerprints.

## Notebook Contract

Notebook cells follow an explicit internal contract:

- `meta` cells provide route, objective, pacing, and handoff guidance.
- `mandatory` cells are the official walkthrough.
- `facultative` cells are optional extensions only.

For the learner, those roles are conveyed through notebook chrome and coloring. Raw `META` / `MANDATORY` / `FACULTATIVE` labels are not supposed to appear as the visible content headlines.

Difficulty is reserved as follows:

- `1-3` for mandatory cells
- `4-10` for facultative cells

Route notebooks stay pure route notebooks. They contain `META` and `MANDATORY` cells only.

## Local Operations

The lifecycle source of truth is `scripts/app.sh`:

- `scripts/app.sh bootstrap`
- `scripts/app.sh start`
- `scripts/app.sh start --foreground`
- `scripts/app.sh stop`
- `scripts/app.sh restart`
- `scripts/app.sh status`
- `scripts/app.sh logs -f`

Compatibility wrappers remain in `scripts/bootstrap.sh`, `scripts/start.sh`, `scripts/stop.sh`, `scripts/restart.sh`, `scripts/status.sh`, `scripts/reset-state.sh`, and `scripts/validate.sh`.

Typical first run:

```bash
bash scripts/app.sh bootstrap
bash scripts/app.sh validate
bash scripts/app.sh start --no-open
```

## Notes

- The repo uses a local `.venv`.
- Jupyter state is isolated inside the repo with `.jupyter_config`, `.jupyter_data`, `.jupyter_runtime`, `.ipython`, `.cache`, and `.logs`.
- The Jupyter kernel is installed into the venv with `--sys-prefix`, not `--user`.
- Validation is designed to work with the standard library first, so structure and notebook execution checks can run before richer notebook tooling is installed.
- JupyterLab and ipykernel are declared in `pyproject.toml` and installed by `scripts/app.sh bootstrap`.
