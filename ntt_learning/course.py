"""Course-level constants shared by tooling and tests."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ROUTE_NOTEBOOKS = [
    Path("notebooks/START_HERE.ipynb"),
    Path("notebooks/COURSE_BLUEPRINT.ipynb"),
    Path("notebooks/COURSE_COMPLETE.ipynb"),
]

BUNDLE_DIRS = [
    Path("notebooks/foundations/01_convolution_to_toy_ntt"),
    Path("notebooks/foundations/02_negative_wrapped_ntt"),
    Path("notebooks/butterfly_mechanics/03_fast_forward_ct"),
    Path("notebooks/butterfly_mechanics/04_fast_inverse_gs"),
    Path("notebooks/kyber_mapping/05_kyber_ntt_and_base_multiplication"),
    Path("notebooks/professional/06_debugging_ntt_failures"),
]


def bundle_notebooks(bundle_dir: Path) -> list[Path]:
    return [
        bundle_dir / "lecture.ipynb",
        bundle_dir / "lab.ipynb",
        bundle_dir / "problems.ipynb",
        bundle_dir / "studio.ipynb",
    ]


TECHNICAL_NOTEBOOKS = [notebook for bundle_dir in BUNDLE_DIRS for notebook in bundle_notebooks(bundle_dir)]

ALL_NOTEBOOKS = ROUTE_NOTEBOOKS[:2] + TECHNICAL_NOTEBOOKS + ROUTE_NOTEBOOKS[2:]

NOTEBOOK_SEQUENCE = [
    ROUTE_NOTEBOOKS[0],
    ROUTE_NOTEBOOKS[1],
    *TECHNICAL_NOTEBOOKS,
    ROUTE_NOTEBOOKS[2],
]

REQUIRED_SCRIPT_NAMES = [
    "bootstrap.sh",
    "start.sh",
    "stop.sh",
    "restart.sh",
    "status.sh",
    "reset-state.sh",
    "validate.sh",
]

CELL_ROLES = {"meta", "mandatory", "facultative"}
ROUTE_ONLY_ROLES = {"meta", "mandatory"}
MANDATORY_DIFFICULTIES = {1, 2, 3}
FACULTATIVE_DIFFICULTIES = {4, 5, 6, 7, 8, 9, 10}
