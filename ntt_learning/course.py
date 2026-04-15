"""Course-level constants shared by tooling and tests."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ROUTE_NOTEBOOKS = [
    Path("notebooks/START_HERE.ipynb"),
    Path("notebooks/COURSE_BLUEPRINT.ipynb"),
]

FOUNDATION_BUNDLE_DIR = Path("notebooks/foundations/01_convolution_to_toy_ntt")

TECHNICAL_NOTEBOOKS = [
    FOUNDATION_BUNDLE_DIR / "lecture.ipynb",
    FOUNDATION_BUNDLE_DIR / "lab.ipynb",
    FOUNDATION_BUNDLE_DIR / "problems.ipynb",
    FOUNDATION_BUNDLE_DIR / "studio.ipynb",
]

ALL_NOTEBOOKS = ROUTE_NOTEBOOKS + TECHNICAL_NOTEBOOKS

NOTEBOOK_SEQUENCE = [
    ROUTE_NOTEBOOKS[0],
    ROUTE_NOTEBOOKS[1],
    *TECHNICAL_NOTEBOOKS,
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

