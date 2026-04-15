"""Generate the course notebooks with explicit pedagogical metadata."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ntt_learning.course import FOUNDATION_BUNDLE_DIR, NOTEBOOK_SEQUENCE


def block(text: str) -> str:
    return dedent(text).strip() + "\n"


def normalized_body(text: str) -> str:
    return dedent(text).strip()


def markdown(role: str, difficulty: int, kind: str, title: str, body: str) -> dict[str, object]:
    label = role.upper()
    return {
        "cell_type": "markdown",
        "metadata": {
            "pedagogy": {
                "role": role,
                "difficulty": difficulty,
                "kind": kind,
                "title": title,
            }
        },
        "source": f"## {label} | difficulty {difficulty} | {title}\n\n{normalized_body(body)}\n",
    }


def code(role: str, difficulty: int, kind: str, title: str, body: str) -> dict[str, object]:
    label = role.upper()
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {
            "pedagogy": {
                "role": role,
                "difficulty": difficulty,
                "kind": kind,
                "title": title,
            }
        },
        "outputs": [],
        "source": f"# {label} | difficulty {difficulty} | {title}\n\n{normalized_body(body)}\n",
    }


def notebook(title: str, cells: list[dict[str, object]]) -> dict[str, object]:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
            "ntt_learning": {
                "title": title,
                "contract_version": "0.1",
                "sequence": [str(path) for path in NOTEBOOK_SEQUENCE],
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebook(relative_path: str, payload: dict[str, object]) -> None:
    destination = REPO_ROOT / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_notebooks() -> None:
    foundation_link = FOUNDATION_BUNDLE_DIR.as_posix()

    write_notebook(
        "notebooks/START_HERE.ipynb",
        notebook(
            "Start Here",
            [
                markdown(
                    "meta",
                    1,
                    "orientation",
                    "Welcome",
                    """
                    This course is local-first and notebook-first. Every visible cell is labeled so the learner always knows
                    whether a cell is route guidance, required walkthrough material, or an optional detour.

                    Contract:

                    - `META` = route, pacing, and handoff guidance
                    - `MANDATORY` = the official walkthrough
                    - `FACULTATIVE` = optional extension
                    """,
                ),
                markdown(
                    "mandatory",
                    1,
                    "route",
                    "Official Route",
                    """
                    Follow exactly one supported path:

                    1. `START_HERE.ipynb`
                    2. `COURSE_BLUEPRINT.ipynb`
                    3. `{foundation_link}/lecture.ipynb`
                    4. `{foundation_link}/lab.ipynb`
                    5. `{foundation_link}/problems.ipynb`
                    6. `{foundation_link}/studio.ipynb`

                    The course starts with concrete arrays and small examples before any Kyber-specific implementation details.
                    """.format(foundation_link=foundation_link),
                ),
                markdown(
                    "meta",
                    1,
                    "operations",
                    "Local Operations",
                    """
                    Repo-local commands:

                    - `scripts/bootstrap.sh` creates `.venv` and installs dependencies
                    - `scripts/validate.sh` runs structural and execution checks
                    - `scripts/start.sh` launches JupyterLab when it is installed
                    """,
                ),
                markdown(
                    "meta",
                    1,
                    "handoff",
                    "Next Notebook",
                    """
                    Next notebook: `COURSE_BLUEPRINT.ipynb`
                    """,
                ),
            ],
        ),
    )

    write_notebook(
        "notebooks/COURSE_BLUEPRINT.ipynb",
        notebook(
            "Course Blueprint",
            [
                markdown(
                    "meta",
                    1,
                    "orientation",
                    "Why This Order Exists",
                    """
                    The course separates three ideas that are often blurred together:

                    - the algebraic purpose of the NTT
                    - the in-place butterfly dataflow
                    - Kyber-specific implementation conventions
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "route",
                    "Learning Staircase",
                    """
                    The supported staircase is:

                    1. ordinary polynomial multiplication and convolution
                    2. negacyclic multiplication
                    3. a tiny toy NTT
                    4. butterfly mechanics in isolation
                    5. forward and inverse flow side by side
                    6. Kyber-specific parameters and indexing
                    7. real implementation patterns
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "structure",
                    "Bundle Rhythm",
                    """
                    Technical bundles follow a consistent rhythm:

                    - `lecture.ipynb` explains the idea carefully
                    - `lab.ipynb` asks for predictions before execution
                    - `problems.ipynb` checks retrieval and reflection
                    - `studio.ipynb` compares implementation choices and debugging cues
                    """,
                ),
                markdown(
                    "meta",
                    1,
                    "constraints",
                    "Route Constraints",
                    """
                    Route notebooks stay pure route notebooks.

                    - no facultative detours here
                    - no hidden competing learner route
                    - every notebook ends with a visible handoff
                    """,
                ),
                markdown(
                    "meta",
                    1,
                    "handoff",
                    "Next Notebook",
                    """
                    Next notebook: `foundations/01_convolution_to_toy_ntt/lecture.ipynb`
                    """,
                ),
            ],
        ),
    )

    write_notebook(
        "notebooks/foundations/01_convolution_to_toy_ntt/lecture.ipynb",
        notebook(
            "Lecture: Convolution To Toy NTT",
            [
                markdown(
                    "meta",
                    1,
                    "orientation",
                    "Objectives",
                    """
                    This notebook introduces the first technical bundle.

                    Focus:

                    - why polynomial multiplication matters
                    - what negacyclic folding changes
                    - how a tiny toy NTT gives a matrix-level view
                    - what a butterfly does locally
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "explanation",
                    "Convolution Before Transforms",
                    """
                    Start with the concrete problem. Two coefficient arrays multiply by accumulating all pairwise products.
                    That schoolbook view is the baseline the learner should be able to inspect by hand before a transform is introduced.
                    """,
                ),
                code(
                    "mandatory",
                    2,
                    "demo",
                    "Inspect Convolution And Negacyclic Folding",
                    """
                    from ntt_learning.toy_ntt import negacyclic_multiply, schoolbook_convolution

                    left = [2, 1, 3, 0]
                    right = [1, 4, 0, 2]

                    print("convolution:", schoolbook_convolution(left, right))
                    print("negacyclic in x^4 + 1:", negacyclic_multiply(left, right, n=4))
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "explanation",
                    "Toy NTT As A Round Trip",
                    """
                    A tiny transform is useful because it keeps every entry inspectable. The first goal is not Kyber fidelity.
                    The first goal is to see that the transform maps one coefficient view to another and can be inverted.
                    """,
                ),
                code(
                    "mandatory",
                    2,
                    "demo",
                    "Run A Tiny Forward And Inverse NTT",
                    """
                    from ntt_learning.toy_ntt import find_primitive_root, forward_ntt, inverse_ntt

                    modulus = 17
                    omega = find_primitive_root(order=4, modulus=modulus)
                    signal = [3, 1, 4, 1]
                    spectrum = forward_ntt(signal, modulus=modulus, omega=omega)

                    print("primitive 4th root:", omega)
                    print("forward spectrum:", spectrum)
                    print("inverse recovery:", inverse_ntt(spectrum, modulus=modulus, omega=omega))
                    """,
                ),
                markdown(
                    "mandatory",
                    3,
                    "explanation",
                    "Butterflies Are Local Dataflow",
                    """
                    A butterfly is a local rewrite of a pair. The pair changes because one branch is twiddled by a zeta value.
                    This is separate from the global story about polynomial multiplication.

                    Forward Cooley-Tukey and inverse Gentleman-Sande have the same shape intuition: pair values, combine them, and move layer by layer.
                    """,
                ),
                code(
                    "mandatory",
                    3,
                    "demo",
                    "Compare Pairwise And Stage-Level Butterfly Views",
                    """
                    from ntt_learning.toy_ntt import action_rows, apply_ct_stage, ct_butterfly_pair, gs_butterfly_pair

                    print("single CT pair:", ct_butterfly_pair(top=7, bottom=5, zeta=3, modulus=17))
                    print("single GS pair:", gs_butterfly_pair(top=7, bottom=5, zeta=3, modulus=17))

                    values = [3, 1, 4, 1]
                    stage_output, stage_actions = apply_ct_stage(values, block_size=2, zetas=1, modulus=17)

                    print("stage output:", stage_output)
                    print("stage trace:", action_rows(stage_actions))
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "quiz",
                    "Retrieval Check",
                    """
                    Quiz:

                    1. What changes when schoolbook multiplication is folded negacyclically?
                    2. Why is the toy NTT introduced before Kyber indexing details?
                    3. In a butterfly, which part of the computation is local and directly inspectable?
                    """,
                ),
                markdown(
                    "facultative",
                    4,
                    "exploration",
                    "Optional Extension",
                    """
                    If the local pairings already feel comfortable, inspect a bit-reversed ordering next. That prepares the learner
                    for later discussions of array ordering without mixing it into the mandatory route too early.
                    """,
                ),
                code(
                    "facultative",
                    4,
                    "exploration",
                    "Bit-Reversed Ordering",
                    """
                    from ntt_learning.toy_ntt import bit_reversed_order

                    print(bit_reversed_order([0, 1, 2, 3, 4, 5, 6, 7]))
                    """,
                ),
                markdown(
                    "meta",
                    1,
                    "handoff",
                    "Next Notebook",
                    """
                    Next notebook: `lab.ipynb`
                    """,
                ),
            ],
        ),
    )

    write_notebook(
        "notebooks/foundations/01_convolution_to_toy_ntt/lab.ipynb",
        notebook(
            "Lab: Convolution To Toy NTT",
            [
                markdown(
                    "meta",
                    1,
                    "orientation",
                    "Lab Goals",
                    """
                    This lab asks for prediction before execution.

                    The learner should pause and name the expected pairings and sign changes before reading the output.
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "exercise",
                    "Exercise 1",
                    """
                    Before running the next cell, predict which coefficients will collide when the raw convolution is folded into `x^4 + 1`.
                    """,
                ),
                code(
                    "mandatory",
                    2,
                    "exercise",
                    "Work Two Multiplication Examples",
                    """
                    from ntt_learning.toy_ntt import negacyclic_multiply, schoolbook_convolution

                    samples = [
                        ([1, 2, 0, 0], [3, 4, 0, 0]),
                        ([5, 0, 1, 2], [2, 1, 0, 1]),
                    ]

                    for left, right in samples:
                        print("left:", left, "right:", right)
                        print("  convolution:", schoolbook_convolution(left, right))
                        print("  negacyclic:", negacyclic_multiply(left, right, n=4))
                    """,
                ),
                markdown(
                    "mandatory",
                    3,
                    "exercise",
                    "Exercise 2",
                    """
                    Predict the pairings for a single Cooley-Tukey stage on eight values with block size four.
                    Name the index pairs before running the cell.
                    """,
                ),
                code(
                    "mandatory",
                    3,
                    "exercise",
                    "Trace One Butterfly Layer",
                    """
                    from ntt_learning.toy_ntt import action_rows, apply_ct_stage

                    values = [0, 1, 2, 3, 4, 5, 6, 7]
                    stage_output, stage_actions = apply_ct_stage(
                        values,
                        block_size=4,
                        zetas=[1, 4, 1, 4],
                        modulus=17,
                    )

                    print("stage output:", stage_output)
                    for row in action_rows(stage_actions):
                        print(row)
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "reflection",
                    "Reflection",
                    """
                    Reflection prompt:

                    - Which part of the stage felt mechanical and local?
                    - Which part still feels global or mysterious?
                    - If one zeta is wrong, what kind of output difference would you expect to see?
                    """,
                ),
                code(
                    "facultative",
                    4,
                    "exploration",
                    "Optional Inverse-Style Stage",
                    """
                    from ntt_learning.toy_ntt import action_rows, apply_gs_stage

                    values = [5, 1, 9, 3, 7, 2, 6, 4]
                    stage_output, stage_actions = apply_gs_stage(
                        values,
                        block_size=4,
                        zetas=[1, 4, 1, 4],
                        modulus=17,
                    )

                    print("stage output:", stage_output)
                    for row in action_rows(stage_actions):
                        print(row)
                    """,
                ),
                markdown(
                    "meta",
                    1,
                    "handoff",
                    "Next Notebook",
                    """
                    Next notebook: `problems.ipynb`
                    """,
                ),
            ],
        ),
    )

    write_notebook(
        "notebooks/foundations/01_convolution_to_toy_ntt/problems.ipynb",
        notebook(
            "Problems: Convolution To Toy NTT",
            [
                markdown(
                    "meta",
                    1,
                    "orientation",
                    "Problem Set Goals",
                    """
                    Use this notebook to check retrieval, not to discover the topic for the first time.
                    If the questions feel opaque, return to the lecture and lab first.
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "quiz",
                    "Multiple-Choice Retrieval",
                    """
                    Choose one answer for each:

                    1. Negacyclic reduction mainly changes:
                       A. coefficient labels only
                       B. wraparound terms by folding them back with sign changes
                       C. the modulus but not the polynomial ring

                    2. The toy NTT is introduced early because it:
                       A. already matches Kyber implementation details exactly
                       B. removes the need to inspect arrays
                       C. gives a small, reversible transform that can be inspected directly

                    3. A butterfly stage is best thought of as:
                       A. a local rewrite over paired entries
                       B. a proof that convolution is impossible
                       C. a random permutation with no arithmetic structure
                    """,
                ),
                code(
                    "mandatory",
                    2,
                    "quiz",
                    "Answer Key",
                    """
                    answers = {
                        1: "B",
                        2: "C",
                        3: "A",
                    }

                    print(answers)
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "reflection",
                    "Written Reflection",
                    """
                    Reflection prompt:

                    - In one paragraph, separate the algebraic purpose of the NTT from the local butterfly dataflow.
                    - In one sentence, explain why the course postpones Kyber-specific indexing.
                    """,
                ),
                code(
                    "mandatory",
                    2,
                    "exercise",
                    "Verify A Round Trip",
                    """
                    from ntt_learning.toy_ntt import find_primitive_root, forward_ntt, inverse_ntt

                    signal = [3, 1, 4, 1]
                    modulus = 17
                    omega = find_primitive_root(order=4, modulus=modulus)
                    recovered = inverse_ntt(forward_ntt(signal, modulus=modulus, omega=omega), modulus=modulus, omega=omega)

                    assert recovered == signal
                    print("round-trip verified:", recovered)
                    """,
                ),
                markdown(
                    "facultative",
                    4,
                    "exploration",
                    "Optional Challenge",
                    """
                    Try replacing the signal with your own four coefficients and predict the forward spectrum before running the next cell.
                    """,
                ),
                code(
                    "facultative",
                    4,
                    "exploration",
                    "Explore Another Signal",
                    """
                    from ntt_learning.toy_ntt import find_primitive_root, forward_ntt

                    signal = [6, 0, 5, 2]
                    modulus = 17
                    omega = find_primitive_root(order=4, modulus=modulus)

                    print("spectrum:", forward_ntt(signal, modulus=modulus, omega=omega))
                    """,
                ),
                markdown(
                    "meta",
                    1,
                    "handoff",
                    "Next Notebook",
                    """
                    Next notebook: `studio.ipynb`
                    """,
                ),
            ],
        ),
    )

    write_notebook(
        "notebooks/foundations/01_convolution_to_toy_ntt/studio.ipynb",
        notebook(
            "Studio: Convolution To Toy NTT",
            [
                markdown(
                    "meta",
                    1,
                    "orientation",
                    "Studio Goals",
                    """
                    This studio frames implementation reading.

                    Keep three lenses separate:

                    - algebraic purpose
                    - array dataflow
                    - protocol-specific conventions
                    """,
                ),
                markdown(
                    "mandatory",
                    3,
                    "explanation",
                    "Forward And Inverse Flow Side By Side",
                    """
                    The goal here is not to claim the same cell-by-cell formula for both directions.
                    The goal is to compare the same pairing structure while noticing that forward and inverse flows push arithmetic in opposite directions.
                    """,
                ),
                code(
                    "mandatory",
                    3,
                    "demo",
                    "Compare Cooley-Tukey And Gentleman-Sande Views",
                    """
                    from ntt_learning.toy_ntt import action_rows, apply_ct_stage, apply_gs_stage

                    values = [2, 5, 7, 1, 3, 6, 4, 0]
                    ct_output, ct_actions = apply_ct_stage(values, block_size=4, zetas=[1, 4, 1, 4], modulus=17)
                    gs_output, gs_actions = apply_gs_stage(values, block_size=4, zetas=[1, 4, 1, 4], modulus=17)

                    print("input:", values)
                    print("ct output:", ct_output)
                    print("gs output:", gs_output)
                    print("ct trace:", action_rows(ct_actions))
                    print("gs trace:", action_rows(gs_actions))
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "exercise",
                    "Debug Checklist",
                    """
                    When a stage looks wrong, inspect these in order:

                    1. wrong pairings
                    2. wrong zeta value
                    3. wrong sign in the subtraction branch
                    4. wrong direction choice between forward-style and inverse-style flow
                    """,
                ),
                code(
                    "mandatory",
                    2,
                    "exercise",
                    "Compare Baseline And Wrong-Zeta Output",
                    """
                    from ntt_learning.toy_ntt import apply_ct_stage

                    values = [3, 1, 4, 1]
                    baseline, _ = apply_ct_stage(values, block_size=2, zetas=1, modulus=17)
                    wrong_zeta, _ = apply_ct_stage(values, block_size=2, zetas=3, modulus=17)

                    print("baseline:", baseline)
                    print("wrong zeta:", wrong_zeta)
                    """,
                ),
                markdown(
                    "facultative",
                    4,
                    "exploration",
                    "Optional Ordering Preview",
                    """
                    Bit-reversal is important later, but it is deliberately optional here so the main route can stay focused on pair mechanics first.
                    """,
                ),
                code(
                    "facultative",
                    4,
                    "exploration",
                    "Inspect Bit-Reversed Order",
                    """
                    from ntt_learning.toy_ntt import bit_reversed_order

                    print(bit_reversed_order([0, 1, 2, 3, 4, 5, 6, 7]))
                    """,
                ),
                markdown(
                    "meta",
                    1,
                    "handoff",
                    "Next Notebook",
                    """
                    Next notebook: return to `../../COURSE_BLUEPRINT.ipynb` and extend the course into Kyber-specific notebooks.
                    """,
                ),
            ],
        ),
    )


if __name__ == "__main__":
    build_notebooks()
