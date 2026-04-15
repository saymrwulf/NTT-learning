# NTT-learning

`NTT-learning` is a local-first, notebook-first course repo for understanding the Number Theoretic Transform in the context of Kyber.

The project is built around one supported learner route:

1. `notebooks/START_HERE.ipynb`
2. `notebooks/COURSE_BLUEPRINT.ipynb`
3. `notebooks/foundations/01_convolution_to_toy_ntt/lecture.ipynb`
4. `notebooks/foundations/01_convolution_to_toy_ntt/lab.ipynb`
5. `notebooks/foundations/01_convolution_to_toy_ntt/problems.ipynb`
6. `notebooks/foundations/01_convolution_to_toy_ntt/studio.ipynb`

The current build intentionally starts with convolution, negacyclic folding, a tiny toy NTT, and butterfly mechanics before any Kyber-specific implementation details.

## Notebook Contract

Visible notebook cells follow an explicit contract:

- `META` cells provide route, objective, pacing, and handoff guidance.
- `MANDATORY` cells are the official walkthrough.
- `FACULTATIVE` cells are optional extensions only.

Difficulty is reserved as follows:

- `1-3` for mandatory cells
- `4-10` for facultative cells

Route notebooks stay pure route notebooks. They contain `META` and `MANDATORY` cells only.

## Local Operations

All repo-local operations live in `scripts/`:

- `scripts/bootstrap.sh`
- `scripts/start.sh`
- `scripts/stop.sh`
- `scripts/restart.sh`
- `scripts/status.sh`
- `scripts/reset-state.sh`
- `scripts/validate.sh`

Typical first run:

```bash
scripts/bootstrap.sh
scripts/validate.sh
scripts/start.sh
```

## Notes

- The repo uses a local `.venv`.
- Validation is designed to work with the standard library first, so structure and notebook execution checks can run before richer notebook tooling is installed.
- JupyterLab is declared in `pyproject.toml` and installed by `scripts/bootstrap.sh`.

