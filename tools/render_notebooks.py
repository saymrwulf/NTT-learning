"""Generate the course notebooks with explicit pedagogical metadata."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from textwrap import dedent

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ntt_learning.course import BUNDLE_DIRS, NOTEBOOK_SEQUENCE


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
                "contract_version": "0.2",
                "sequence": [str(path) for path in NOTEBOOK_SEQUENCE],
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def humanize_path_part(text: str) -> str:
    label = text.replace("_", " ").title()
    replacements = {
        "Ntt": "NTT",
        "Intt": "INTT",
        "Ct": "CT",
        "Gs": "GS",
        "Kyber": "Kyber",
        "Toy NTT": "Toy NTT",
    }
    for source, target in replacements.items():
        label = label.replace(source, target)
    return label


def notebook_label(path: Path) -> str:
    if path.parent == Path("notebooks"):
        return humanize_path_part(path.stem)
    category = humanize_path_part(path.parent.parent.name)
    bundle = humanize_path_part(path.parent.name)
    role = humanize_path_part(path.stem)
    return f"{category} / {bundle} / {role}"


def relative_notebook_link(current_path: Path, target_path: Path) -> str:
    return Path(os.path.relpath(target_path, start=current_path.parent)).as_posix()


def route_chain_markdown(current_path: Path) -> str:
    lines = []
    for index, path in enumerate(NOTEBOOK_SEQUENCE, start=1):
        label = notebook_label(path)
        if path == current_path:
            lines.append(f"{index}. **{label}** <- you are here")
        else:
            lines.append(f"{index}. [{label}]({relative_notebook_link(current_path, path)})")
    return "\n".join(lines)


def navigation_cell(current_path: Path) -> dict[str, object]:
    step_index = NOTEBOOK_SEQUENCE.index(current_path)
    previous_path = NOTEBOOK_SEQUENCE[step_index - 1] if step_index > 0 else None
    next_path = NOTEBOOK_SEQUENCE[step_index + 1] if step_index + 1 < len(NOTEBOOK_SEQUENCE) else None

    previous_line = (
        f"- Previous notebook: [{notebook_label(previous_path)}]({relative_notebook_link(current_path, previous_path)})"
        if previous_path is not None
        else "- Previous notebook: you are at the start of the supported route"
    )
    next_line = (
        f"- Next notebook: [{notebook_label(next_path)}]({relative_notebook_link(current_path, next_path)})"
        if next_path is not None
        else "- Next notebook: you are at the end of the supported route"
    )

    body = "\n".join(
        [
            f"You are at **step {step_index + 1} of {len(NOTEBOOK_SEQUENCE)}** in the only supported route.",
            "",
            "Never choose the next notebook manually from the file tree. Use only the links in this cell and the final handoff cell.",
            "",
            "**Immediate navigation**",
            next_line,
            previous_line,
            f"- Restart route: [Start Here]({relative_notebook_link(current_path, NOTEBOOK_SEQUENCE[0])})",
            "",
            "**Official route chain**",
            route_chain_markdown(current_path),
        ]
    )
    return markdown("meta", 1, "route_nav", "Route Guardrails", body)


def handoff_navigation_cell(current_path: Path) -> dict[str, object]:
    step_index = NOTEBOOK_SEQUENCE.index(current_path)
    next_path = NOTEBOOK_SEQUENCE[step_index + 1] if step_index + 1 < len(NOTEBOOK_SEQUENCE) else None
    previous_path = NOTEBOOK_SEQUENCE[step_index - 1] if step_index > 0 else None

    lines = [f"You finished **{notebook_label(current_path)}**."]
    lines.append("")
    lines.append("**Primary next action**")
    if next_path is None:
        lines.append("- Next notebook: you are at the end of the supported route")
    else:
        lines.append(
            f"- Next notebook: [Step {step_index + 2} of {len(NOTEBOOK_SEQUENCE)} - {notebook_label(next_path)}]({relative_notebook_link(current_path, next_path)})"
        )
    lines.append("")
    lines.append("**Recovery links if you get lost**")
    if previous_path is not None:
        lines.append(
            f"- Previous notebook: [{notebook_label(previous_path)}]({relative_notebook_link(current_path, previous_path)})"
        )
    lines.append(f"- Restart route: [Start Here]({relative_notebook_link(current_path, NOTEBOOK_SEQUENCE[0])})")
    return markdown("meta", 1, "handoff", "Next Notebook", "\n".join(lines))


def inject_route_scaffold(current_path: Path, payload: dict[str, object]) -> dict[str, object]:
    cells = list(payload["cells"])
    cells = [cell for cell in cells if cell.get("metadata", {}).get("pedagogy", {}).get("kind") != "route_nav"]

    handoff_found = False
    for index, cell in enumerate(cells):
        if cell.get("metadata", {}).get("pedagogy", {}).get("kind") == "handoff":
            cells[index] = handoff_navigation_cell(current_path)
            handoff_found = True

    if not handoff_found:
        cells.append(handoff_navigation_cell(current_path))

    insert_at = 1 if cells else 0
    cells.insert(insert_at, navigation_cell(current_path))
    payload["cells"] = cells
    return payload


def write_notebook(relative_path: str, payload: dict[str, object]) -> None:
    payload = inject_route_scaffold(Path(relative_path), payload)
    destination = REPO_ROOT / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def handoff_cell(next_notebook: str) -> dict[str, object]:
    return markdown("meta", 1, "handoff", "Next Notebook", f"Next notebook: `{next_notebook}`")


def write_bundle(bundle_dir: Path, bundle_title: str, lecture: list[dict[str, object]], lab: list[dict[str, object]], problems: list[dict[str, object]], studio: list[dict[str, object]]) -> None:
    relative = bundle_dir.as_posix()
    write_notebook(f"{relative}/lecture.ipynb", notebook(f"Lecture: {bundle_title}", lecture))
    write_notebook(f"{relative}/lab.ipynb", notebook(f"Lab: {bundle_title}", lab))
    write_notebook(f"{relative}/problems.ipynb", notebook(f"Problems: {bundle_title}", problems))
    write_notebook(f"{relative}/studio.ipynb", notebook(f"Studio: {bundle_title}", studio))


def build_start_here() -> None:
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
                    This course is for people who need to see the algorithm move.

                    The goal is not to hide behind abstract formulas. The goal is to make the NTT and iNTT feel physically inspectable:

                    - every stage should look like values moving through wires
                    - every wraparound should be visible
                    - every ordering change should be concrete
                    - every Kyber-specific choice should be motivated by what the arithmetic allows
                    """,
                ),
                markdown(
                    "mandatory",
                    1,
                    "route",
                    "Official Route",
                    """
                    Follow exactly one supported route:

                    1. `START_HERE.ipynb`
                    2. `COURSE_BLUEPRINT.ipynb`
                    3. each bundle in `Lecture -> Lab -> Problems -> Studio` order
                    4. `COURSE_COMPLETE.ipynb`

                    Supported bundles:

                    - `foundations/01_convolution_to_toy_ntt`
                    - `foundations/02_negative_wrapped_ntt`
                    - `butterfly_mechanics/03_fast_forward_ct`
                    - `butterfly_mechanics/04_fast_inverse_gs`
                    - `kyber_mapping/05_kyber_ntt_and_base_multiplication`
                    - `professional/06_debugging_ntt_failures`
                    """,
                ),
                markdown(
                    "mandatory",
                    1,
                    "contract",
                    "Visible Cell Contract",
                    """
                    Cell labels are not decoration. They tell you how to use the notebook:

                    - `META` = route, pacing, and handoff
                    - `MANDATORY` = the official walkthrough
                    - `FACULTATIVE` = optional deepening only
                    - difficulty `1-3` is reserved for mandatory work
                    - difficulty `4-10` is reserved for facultative work
                    """,
                ),
                markdown(
                    "meta",
                    1,
                    "operations",
                    "Local Operations",
                    """
                    Repo-local commands:

                    - `scripts/bootstrap.sh`
                    - `scripts/start.sh`
                    - `scripts/status.sh`
                    - `scripts/validate.sh`
                    """,
                ),
                handoff_cell("COURSE_BLUEPRINT.ipynb"),
            ],
        ),
    )


def build_course_blueprint() -> None:
    write_notebook(
        "notebooks/COURSE_BLUEPRINT.ipynb",
        notebook(
            "Course Blueprint",
            [
                markdown(
                    "meta",
                    1,
                    "orientation",
                    "What This Course Separates",
                    """
                    This course keeps three stories separate on purpose:

                    - the algebraic purpose of the transform
                    - the local in-place butterfly dataflow
                    - the Kyber-specific implementation conventions

                    The point is to stop those three from collapsing into one blurry “FFT-like thing”.
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "structure",
                    "The Learning Staircase",
                    """
                    The supported staircase is:

                    1. schoolbook multiplication and diagonals
                    2. cyclic and negacyclic wraparound
                    3. direct negative-wrapped NTT and iNTT
                    4. fast forward CT butterflies
                    5. fast inverse GS butterflies
                    6. bit-reversal and ordering
                    7. Kyber parameter reality and base multiplication
                    8. debugging wrong sign / wrong zeta / wrong order / wrong scale failures
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "bundles",
                    "Bundles",
                    """
                    Each serious module uses the same rhythm:

                    - `lecture.ipynb` = slow explanation plus visual demos
                    - `lab.ipynb` = prediction before execution
                    - `problems.ipynb` = retrieval and reflection
                    - `studio.ipynb` = comparison, debugging, and implementation reading
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "expectation",
                    "What “Blunt And Graphical” Means Here",
                    """
                    The notebooks should not ask the learner to imagine too much in their head.

                    Expect:

                    - schoolbook product grids
                    - wraparound arrows
                    - explicit stage arrays
                    - stage sliders
                    - bit-reversal wire maps
                    - side-by-side wrong vs right traces
                    """,
                ),
                handoff_cell("foundations/01_convolution_to_toy_ntt/lecture.ipynb"),
            ],
        ),
    )


def build_course_complete() -> None:
    write_notebook(
        "notebooks/COURSE_COMPLETE.ipynb",
        notebook(
            "Course Complete",
            [
                markdown(
                    "meta",
                    1,
                    "orientation",
                    "Route Complete",
                    """
                    You reached the end of the supported route.

                    If the course did its job, you should now be able to separate:

                    - raw polynomial multiplication
                    - negacyclic structure
                    - direct NTT / iNTT definitions
                    - fast CT / GS butterfly flow
                    - order changes and scaling
                    - Kyber’s specific modulus and base-multiplication story
                    """,
                ),
                markdown(
                    "mandatory",
                    2,
                    "reflection",
                    "Exit Reflection",
                    """
                    Final written prompts:

                    1. Explain the difference between “the transform as mathematics” and “the butterfly network as an implementation strategy”.
                    2. Explain why Kyber v3 needs more than the naive “just use a 2n-th root” mental model.
                    3. Name the first four checks you would run if an iNTT output looked wrong.
                    """,
                ),
                markdown(
                    "meta",
                    1,
                    "handoff",
                    "Next Notebook",
                    """
                    Next notebook: you are at the end of the supported route. Revisit the studios if you want more repetition.
                    """,
                ),
            ],
        ),
    )


def build_bundle_01() -> None:
    bundle_dir = BUNDLE_DIRS[0]
    write_bundle(
        bundle_dir,
        "Convolution To Toy NTT",
        lecture=[
            markdown(
                "meta",
                1,
                "orientation",
                "Objectives",
                """
                This first bundle is about making the raw multiplication problem visible before any transform is introduced.

                Focus:

                - the schoolbook product grid
                - diagonal sums
                - cyclic vs negacyclic folding
                - a tiny teaser of why transforms help
                """,
            ),
            markdown(
                "mandatory",
                2,
                "explanation",
                "Schoolbook Multiplication Is A Grid",
                """
                Stop thinking “multiply two polynomials” as one sentence.
                The mechanical reality is a grid of pairwise products whose diagonals have to be accumulated.

                If that grid is not concrete, the NTT has nothing to optimize in your mind.
                """,
            ),
            code(
                "mandatory",
                2,
                "demo",
                "Play The Diagonal Sweep",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import convolution_contributions, schoolbook_convolution
                from ntt_learning.visuals import plot_convolution_grid, schoolbook_diagonal_player

                left = [1, 2, 3, 4]
                right = [5, 6, 7, 8]
                raw = schoolbook_convolution(left, right)

                print("raw convolution:", raw)
                for row in convolution_contributions(left, right):
                    print(row)

                display(schoolbook_diagonal_player(left, right))
                fig = plot_convolution_grid(left, right, title="Schoolbook products for [1,2,3,4] * [5,6,7,8]")
                display(fig)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "explanation",
                "Wraparound Is The First Structural Fork",
                """
                Once the raw tail exists, the ring tells you what to do with it.

                - in `x^n - 1`, high-degree terms wrap back with a positive sign
                - in `x^n + 1`, high-degree terms wrap back with a sign flip

                That sign flip is not cosmetic. It is exactly what makes the negacyclic story different.
                """,
            ),
            code(
                "mandatory",
                2,
                "demo",
                "Play The Wraparound Step By Step",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import negacyclic_multiply, schoolbook_convolution, wraparound_contributions
                from ntt_learning.visuals import plot_wraparound, wraparound_comparison_player

                left = [1, 2, 3, 4]
                right = [5, 6, 7, 8]
                raw = schoolbook_convolution(left, right)

                print("raw convolution:", raw)
                print("negacyclic in x^4 + 1:", negacyclic_multiply(left, right, n=4))
                print("cyclic folding rows:")
                for row in wraparound_contributions(raw, n=4, negacyclic=False):
                    print(row)
                print("negacyclic folding rows:")
                for row in wraparound_contributions(raw, n=4, negacyclic=True):
                    print(row)

                display(wraparound_comparison_player(raw, n=4))
                display(plot_wraparound(raw, n=4, negacyclic=False, title="Cyclic folding into x^4 - 1"))
                display(plot_wraparound(raw, n=4, negacyclic=True, title="Negacyclic folding into x^4 + 1"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "explanation",
                "The Tiny Transform Teaser",
                """
                The transform is not magic. It is a change of coordinates chosen so that multiplication gets easier.

                The next bundle will treat the transform itself directly.
                This first bundle only makes sure the learner can see the raw thing being optimized.
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Retrieval Check",
                """
                Answer in words before moving on:

                1. Why do diagonal sums appear in schoolbook multiplication?
                2. What is the one exact sign difference between cyclic and negacyclic folding?
                3. If you cannot track the tail wraparound, what part of the NTT story will stay vague?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Compare Another Example",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import negacyclic_multiply, schoolbook_convolution
                from ntt_learning.visuals import plot_convolution_grid, plot_wraparound

                left = [2, 1, 0, 3]
                right = [4, 0, 1, 2]
                raw = schoolbook_convolution(left, right)

                print("raw convolution:", raw)
                print("negacyclic:", negacyclic_multiply(left, right, n=4))
                display(plot_convolution_grid(left, right, title="A second schoolbook grid"))
                display(plot_wraparound(raw, n=4, negacyclic=True, title="A second negacyclic fold"))
                """,
            ),
            handoff_cell("lab.ipynb"),
        ],
        lab=[
            markdown(
                "meta",
                1,
                "orientation",
                "Lab Goals",
                """
                Predict the movement before you run the code.

                The point is not just to see the picture after the fact.
                The point is to force your eye to anticipate where the products and wraparound terms will land.
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Exercise 1",
                """
                Before running the next cell:

                - name the diagonal sums of the raw schoolbook grid
                - say which tail terms will wrap into slot `0`
                - say whether they add or subtract in `x^4 + 1`
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "Run The Prediction Check",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import negacyclic_multiply, schoolbook_convolution
                from ntt_learning.visuals import plot_convolution_grid, plot_wraparound, schoolbook_diagonal_player, wraparound_comparison_player

                left = [3, 0, 2, 1]
                right = [1, 4, 0, 2]
                raw = schoolbook_convolution(left, right)

                print("raw convolution:", raw)
                print("negacyclic result:", negacyclic_multiply(left, right, n=4))
                display(schoolbook_diagonal_player(left, right))
                display(wraparound_comparison_player(raw, n=4))
                display(plot_convolution_grid(left, right, title="Prediction check grid"))
                display(plot_wraparound(raw, n=4, negacyclic=True, title="Prediction check fold"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Exercise 2",
                """
                Pick one number in the raw tail and follow it all the way to its final slot.
                Do not say “it wraps around”.
                Say exactly:

                - where it started
                - how many wraps happened
                - whether the sign flipped
                - where it finished
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "A Second Visual Drill",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import schoolbook_convolution
                from ntt_learning.visuals import plot_wraparound, wraparound_comparison_player

                raw = schoolbook_convolution([2, 5, 0, 1], [1, 0, 3, 2])
                print("raw convolution:", raw)
                display(wraparound_comparison_player(raw, n=4))
                display(plot_wraparound(raw, n=4, negacyclic=True, title="Trace one tail coefficient by eye"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Reflection prompt:

                - What felt easier to see in the grid than in symbolic polynomial notation?
                - What exactly makes negacyclic folding more annoying than ordinary wraparound?
                - If you had to explain `x^n + 1` to somebody visually, what would you draw?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Try Your Own Arrays",
                """
                import ipywidgets as widgets
                from IPython.display import display

                from ntt_learning.toy_ntt import schoolbook_convolution
                from ntt_learning.visuals import plot_convolution_grid, plot_wraparound

                def preview(a0=1, a1=2, a2=3, a3=4, b0=5, b1=6, b2=7, b3=8):
                    left = [a0, a1, a2, a3]
                    right = [b0, b1, b2, b3]
                    raw = schoolbook_convolution(left, right)
                    display(plot_convolution_grid(left, right, title="Interactive schoolbook grid"))
                    display(plot_wraparound(raw, n=4, negacyclic=True, title="Interactive negacyclic fold"))

                display(
                    widgets.interact(
                        preview,
                        a0=(0, 6),
                        a1=(0, 6),
                        a2=(0, 6),
                        a3=(0, 6),
                        b0=(0, 6),
                        b1=(0, 6),
                        b2=(0, 6),
                        b3=(0, 6),
                    )
                )
                """,
            ),
            handoff_cell("problems.ipynb"),
        ],
        problems=[
            markdown(
                "meta",
                1,
                "orientation",
                "Problem Set Goals",
                """
                This notebook checks whether the multiplication and folding pictures are now stable in memory.
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Multiple-Choice Retrieval",
                """
                Choose one answer for each:

                1. The diagonal sums in schoolbook multiplication come from:
                   A. random coincidence
                   B. grouping terms with the same final degree
                   C. bit-reversal

                2. Negacyclic folding differs from cyclic folding because:
                   A. the wrapped tail flips sign
                   B. the polynomial degrees disappear
                   C. the raw convolution gets shorter before folding

                3. The main reason to study the raw grid before NTT is:
                   A. because the transform is impossible otherwise
                   B. because it makes the optimized algorithm visually grounded
                   C. because Kyber never uses transforms
                """,
            ),
            code(
                "mandatory",
                2,
                "quiz",
                "Answer Key",
                """
                answers = {1: "B", 2: "A", 3: "B"}
                print(answers)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Manual Fold Check",
                """
                Compute the negacyclic fold of the raw vector `[5, 16, 34, 60, 61, 52, 32]` into `x^4 + 1` by hand before running the next cell.
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "Check The Fold",
                """
                from ntt_learning.toy_ntt import negacyclic_reduce

                raw = [5, 16, 34, 60, 61, 52, 32]
                print(negacyclic_reduce(raw, n=4))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Written Reflection",
                """
                In one paragraph, explain why “wrap the tail back” is still too vague unless you also specify:

                - the divisor
                - the target slot
                - the sign rule
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional Challenge",
                """
                from ntt_learning.toy_ntt import wraparound_contributions

                raw = [3, 11, 7, 0, 5, 9, 4]
                for row in wraparound_contributions(raw, n=4, negacyclic=True):
                    print(row)
                """,
            ),
            handoff_cell("studio.ipynb"),
        ],
        studio=[
            markdown(
                "meta",
                1,
                "orientation",
                "Studio Goals",
                """
                This studio is about comparison and diagnosis.
                The learner should leave with a strong visual distinction between cyclic and negacyclic wraparound.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "Two Folds, Same Raw Tail, Different Result",
                """
                If the raw convolution is fixed, the only thing that changes is the ring rule.
                That is exactly why the same tail can produce two different reduced polynomials.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Compare The Two Fold Rules",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import schoolbook_convolution
                from ntt_learning.visuals import plot_wraparound, wraparound_comparison_player

                raw = schoolbook_convolution([1, 2, 3, 4], [5, 6, 7, 8])
                print("raw convolution:", raw)
                display(wraparound_comparison_player(raw, n=4))
                display(plot_wraparound(raw, n=4, negacyclic=False, title="Positive wrap into x^4 - 1"))
                display(plot_wraparound(raw, n=4, negacyclic=True, title="Negative wrap into x^4 + 1"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Debug Checklist",
                """
                If a wraparound result looks wrong, inspect these in order:

                1. Was the raw convolution itself correct?
                2. Was the divisor `x^n - 1` or `x^n + 1`?
                3. Did the wrapped tail land in the right slot?
                4. Did the sign flip happen on the wrapped term?
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "See A Wrong-Sign Failure",
                """
                from ntt_learning.toy_ntt import schoolbook_convolution, negacyclic_reduce

                raw = schoolbook_convolution([1, 2, 3, 4], [5, 6, 7, 8])
                wrong = [raw[0] + raw[4], raw[1] + raw[5], raw[2] + raw[6], raw[3]]

                print("raw:", raw)
                print("wrong sign fold:", wrong)
                print("correct negacyclic fold:", negacyclic_reduce(raw, n=4))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Explain the exact visual difference between “the wrong-sign fold” and “the correct negacyclic fold”.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Fold A Larger Tail",
                """
                from IPython.display import display

                from ntt_learning.visuals import plot_wraparound

                raw = [4, 8, 12, 16, 9, 5, 1, 7, 11]
                display(plot_wraparound(raw, n=4, negacyclic=True, title="Longer tail, same fold rule"))
                """,
            ),
            handoff_cell("../../../foundations/02_negative_wrapped_ntt/lecture.ipynb"),
        ],
    )


def build_bundle_02() -> None:
    bundle_dir = BUNDLE_DIRS[1]
    write_bundle(
        bundle_dir,
        "Negative-Wrapped NTT",
        lecture=[
            markdown(
                "meta",
                1,
                "orientation",
                "Objectives",
                """
                This bundle introduces the transform itself in its negacyclic form.

                Focus:

                - the difference between `ω` and `ψ`
                - direct NTTψ and INTTψ
                - the direct convolution theorem in the negacyclic setting
                - why this is still too slow at `O(n^2)` without butterflies
                """,
            ),
            markdown(
                "mandatory",
                2,
                "explanation",
                "Why ψ Shows Up",
                """
                For negative-wrapped convolution, the clean transform formula uses a `2n`-th root `ψ` with:

                - `ψ^2 = ω`
                - `ψ^n = -1`

                That is what bakes the negacyclic sign rule into the transform itself.
                """,
            ),
            code(
                "mandatory",
                2,
                "demo",
                "Inspect ω, ψ, And The Direct Transform Matrix",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import find_primitive_root, find_psi, ntt_psi_exponent_grid, ntt_psi_matrix
                from ntt_learning.visuals import direct_ntt_player, plot_ntt_psi_exponent_heatmap, plot_ntt_psi_matrix_heatmap

                modulus = 17
                n = 4
                omega = find_primitive_root(n, modulus)
                psi = find_psi(n, modulus)

                print("omega:", omega)
                print("psi:", psi)
                print("exponent grid:")
                for row in ntt_psi_exponent_grid(n):
                    print(row)
                print("NTT_psi matrix:")
                for row in ntt_psi_matrix(n, modulus, psi):
                    print(row)

                display(direct_ntt_player([1, 2, 3, 4], modulus, psi))
                display(plot_ntt_psi_exponent_heatmap(n, title="Exponents 2ij + i for n=4"))
                display(plot_ntt_psi_matrix_heatmap(n, modulus, psi, title="Concrete NTT_psi matrix in Z_17"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "explanation",
                "Direct NTTψ Is Mechanically Clear But Still Quadratic",
                """
                The direct transform is useful because every coefficient and every exponent is visible.
                It is not yet efficient. It still performs the full matrix multiplication.
                """,
            ),
            code(
                "mandatory",
                2,
                "demo",
                "Run A Direct NTTψ / INTTψ Round Trip",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import find_psi, forward_ntt_psi, inverse_ntt_psi
                from ntt_learning.visuals import direct_ntt_player

                signal = [1, 2, 3, 4]
                modulus = 17
                psi = find_psi(len(signal), modulus)
                spectrum = forward_ntt_psi(signal, modulus, psi)

                print("signal:", signal)
                print("spectrum:", spectrum)
                print("inverse recovery:", inverse_ntt_psi(spectrum, modulus, psi))
                display(direct_ntt_player(signal, modulus, psi))
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Use Direct NTTψ For Negacyclic Multiplication",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import find_psi, forward_ntt_psi, inverse_ntt_psi, negacyclic_multiply, pointwise_multiply
                from ntt_learning.visuals import plot_transform_pipeline

                left = [1, 2, 3, 4]
                right = [5, 6, 7, 8]
                modulus = 17
                psi = find_psi(4, modulus)

                left_hat = forward_ntt_psi(left, modulus, psi)
                right_hat = forward_ntt_psi(right, modulus, psi)
                product_hat = pointwise_multiply(left_hat, right_hat, modulus)

                print("NTT_psi(left):", left_hat)
                print("NTT_psi(right):", right_hat)
                print("pointwise product:", product_hat)
                print("inverse of pointwise product:", inverse_ntt_psi(product_hat, modulus, psi))
                print("schoolbook negacyclic:", negacyclic_multiply(left, right, n=4, modulus=modulus))
                display(plot_transform_pipeline(left, right, modulus=modulus, psi=psi, title="Direct negacyclic multiply pipeline"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Retrieval Check",
                """
                1. Why is `ψ` stronger than `ω` in the negacyclic story?
                2. What exact property does the inverse add that the forward transform does not?
                3. Why are we still dissatisfied after seeing the direct transform work correctly?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Compare Positive And Negative Wrapped Transforms",
                """
                from ntt_learning.toy_ntt import find_primitive_root, find_psi, forward_ntt, forward_ntt_psi

                signal = [1, 2, 3, 4]
                modulus = 17
                omega = find_primitive_root(4, modulus)
                psi = find_psi(4, modulus)

                print("positive-wrapped NTT:", forward_ntt(signal, modulus, omega))
                print("negative-wrapped NTT_psi:", forward_ntt_psi(signal, modulus, psi))
                """,
            ),
            handoff_cell("lab.ipynb"),
        ],
        lab=[
            markdown(
                "meta",
                1,
                "orientation",
                "Lab Goals",
                """
                The lab is about prediction inside the direct transform matrix.
                Do not run the next cells until you name the powers and products you expect to matter.
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Exercise 1",
                """
                For `signal = [1,2,3,4]`, `n = 4`, `q = 17`, predict:

                - which powers of `ψ` appear in row `j = 1`
                - whether the inverse should need both `ψ^-1` and `n^-1`
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "Prediction Check",
                """
                from ntt_learning.toy_ntt import find_psi, ntt_psi_exponent_grid

                psi = find_psi(4, 17)
                print("psi:", psi)
                for row_index, row in enumerate(ntt_psi_exponent_grid(4)):
                    print("row", row_index, row)
                """,
            ),
            code(
                "mandatory",
                3,
                "exercise",
                "Interactive Signal Explorer",
                """
                import ipywidgets as widgets
                from IPython.display import display

                from ntt_learning.toy_ntt import find_psi, forward_ntt_psi, inverse_ntt_psi
                from ntt_learning.visuals import direct_ntt_player

                modulus = 17
                psi = find_psi(4, modulus)

                def preview(a0=1, a1=2, a2=3, a3=4):
                    signal = [a0, a1, a2, a3]
                    spectrum = forward_ntt_psi(signal, modulus, psi)
                    print("signal:", signal)
                    print("spectrum:", spectrum)
                    print("inverse:", inverse_ntt_psi(spectrum, modulus, psi))
                    display(direct_ntt_player(signal, modulus, psi))

                display(
                    widgets.interact(
                        preview,
                        a0=(0, 16),
                        a1=(0, 16),
                        a2=(0, 16),
                        a3=(0, 16),
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Exercise 2",
                """
                Explain what the pointwise multiplication in the transform domain is buying you.
                Use the words “replace convolution by slotwise multiplication” in your own sentence.
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "Compare Raw Convolution And Slotwise Multiplication",
                """
                from ntt_learning.toy_ntt import (
                    find_psi,
                    forward_ntt_psi,
                    inverse_ntt_psi,
                    pointwise_multiply,
                    schoolbook_convolution,
                )

                left = [2, 1, 0, 3]
                right = [4, 0, 1, 2]
                psi = find_psi(4, 17)
                left_hat = forward_ntt_psi(left, 17, psi)
                right_hat = forward_ntt_psi(right, 17, psi)

                print("schoolbook raw:", schoolbook_convolution(left, right))
                print("left_hat:", left_hat)
                print("right_hat:", right_hat)
                print("pointwise product:", pointwise_multiply(left_hat, right_hat, 17))
                print("inverse:", inverse_ntt_psi(pointwise_multiply(left_hat, right_hat, 17), 17, psi))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Reflection prompt:

                - What feels concrete in the direct transform matrix?
                - What still feels too expensive or repetitive?
                - Why are butterflies the obvious next step?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Try A Different Modulus",
                """
                from ntt_learning.toy_ntt import find_psi, forward_ntt_psi

                modulus = 97
                psi = find_psi(4, modulus)
                signal = [1, 2, 3, 4]

                print("modulus:", modulus)
                print("psi:", psi)
                print("spectrum:", forward_ntt_psi(signal, modulus, psi))
                """,
            ),
            handoff_cell("problems.ipynb"),
        ],
        problems=[
            markdown(
                "meta",
                1,
                "orientation",
                "Problem Set Goals",
                """
                This notebook checks whether the direct negative-wrapped transform is now mechanically understandable.
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Multiple-Choice Retrieval",
                """
                Choose one answer for each:

                1. In the negacyclic transform, `ψ` matters because:
                   A. it makes the modulus disappear
                   B. it encodes the `x^n + 1` sign structure
                   C. it avoids all inverses

                2. The inverse transform differs from the forward transform by:
                   A. an inverse root and an `n^-1` scaling
                   B. a larger modulus
                   C. removing all twiddle factors

                3. The direct matrix transform is still pedagogically useful because:
                   A. it keeps every coefficient contribution visible
                   B. it is how Kyber is implemented directly at full size
                   C. it removes the need for butterflies
                """,
            ),
            code(
                "mandatory",
                2,
                "quiz",
                "Answer Key",
                """
                answers = {1: "B", 2: "A", 3: "A"}
                print(answers)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Round-Trip Check",
                """
                Verify by code that `INTTψ(NTTψ(a)) = a` for a nontrivial vector.
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "Check The Round Trip",
                """
                from ntt_learning.toy_ntt import find_psi, forward_ntt_psi, inverse_ntt_psi

                signal = [6, 0, 5, 2]
                psi = find_psi(4, 17)
                recovered = inverse_ntt_psi(forward_ntt_psi(signal, 17, psi), 17, psi)
                print(recovered)
                assert recovered == signal
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Written Reflection",
                """
                In one paragraph, explain why the direct transform is the right place to understand the algebra, but not the right place to stop if you care about algorithmic speed.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional Challenge",
                """
                from ntt_learning.toy_ntt import find_psi, forward_ntt_psi

                psi = find_psi(4, 17)
                for signal in ([1, 1, 1, 1], [0, 1, 0, 1], [3, 5, 7, 9]):
                    print(signal, "->", forward_ntt_psi(signal, 17, psi))
                """,
            ),
            handoff_cell("studio.ipynb"),
        ],
        studio=[
            markdown(
                "meta",
                1,
                "orientation",
                "Studio Goals",
                """
                The studio compares direct positive-wrapped and negative-wrapped transforms so the learner stops treating “NTT” as one unqualified object.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "Same Input, Different Transform Story",
                """
                The same coefficient vector can be sent through two different transform stories depending on the quotient ring.
                That difference is not implementation noise. It is structural.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Compare Positive-Wrapped And Negative-Wrapped Views",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import find_primitive_root, find_psi, forward_ntt, forward_ntt_psi
                from ntt_learning.visuals import plot_vector_comparison

                signal = [1, 2, 3, 4]
                modulus = 17
                omega = find_primitive_root(4, modulus)
                psi = find_psi(4, modulus)

                positive = forward_ntt(signal, modulus, omega)
                negative = forward_ntt_psi(signal, modulus, psi)

                print("positive-wrapped NTT:", positive)
                print("negative-wrapped NTT_psi:", negative)
                display(
                    plot_vector_comparison(
                        positive,
                        negative,
                        left_label="positive",
                        right_label="negative",
                        title="Same signal, different transform story",
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Debug Checklist",
                """
                If a direct transform result looks suspicious, inspect:

                1. the chosen modulus
                2. the order of the root
                3. whether you are using `ω` or `ψ`
                4. whether the inverse includes `n^-1`
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "See A Wrong-Root Failure",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import find_primitive_root, find_psi, forward_ntt_psi
                from ntt_learning.visuals import plot_vector_comparison

                signal = [1, 2, 3, 4]
                modulus = 17
                omega = find_primitive_root(4, modulus)
                psi = find_psi(4, modulus)

                correct = forward_ntt_psi(signal, modulus, psi)
                wrong = forward_ntt_psi(signal, modulus, omega)

                print("correct psi-based transform:", correct)
                print("wrongly using omega as if it were psi:", wrong)
                display(
                    plot_vector_comparison(
                        wrong,
                        correct,
                        left_label="wrong_root",
                        right_label="correct",
                        title="Wrong root vs correct root",
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Explain why “pick any root of unity” is not an acceptable habit in this subject.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Matrix Comparison",
                """
                from ntt_learning.toy_ntt import find_primitive_root, find_psi, ntt_psi_matrix

                modulus = 17
                omega = find_primitive_root(4, modulus)
                psi = find_psi(4, modulus)

                print("omega:", omega)
                print("psi:", psi)
                for row in ntt_psi_matrix(4, modulus, psi):
                    print(row)
                """,
            ),
            handoff_cell("../../../butterfly_mechanics/03_fast_forward_ct/lecture.ipynb"),
        ],
    )


def build_bundle_03() -> None:
    bundle_dir = BUNDLE_DIRS[2]
    write_bundle(
        bundle_dir,
        "Fast Forward CT",
        lecture=[
            markdown(
                "meta",
                1,
                "orientation",
                "Objectives",
                """
                This bundle is where the transform stops being a full matrix multiplication and becomes a staged butterfly network.

                Focus:

                - CT as the fast forward NTT strategy
                - visible stage arrays
                - explicit zeta values per pair
                - BO output vs NO output
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "CT Is A Schedule For Reusing Work",
                """
                The point of the CT butterfly is not to invent a new transform.
                The point is to compute the same transform by reusing shared bracket terms instead of recomputing everything from scratch.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "See The Schedule Geometry Before The Numbers",
                """
                from IPython.display import display

                from ntt_learning.visuals import plot_stage_pairing_map, plot_stage_schedule

                display(plot_stage_schedule(8, title="CT schedule skeleton for n=8"))
                display(plot_stage_pairing_map(8, 2, title="Stage 1 pairings for n=8"))
                display(plot_stage_pairing_map(8, 4, title="Stage 2 pairings for n=8"))
                display(plot_stage_pairing_map(8, 8, title="Stage 3 pairings for n=8"))
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Trace The Exact n=4 Paper Example",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace, forward_ntt_psi
                from ntt_learning.visuals import butterfly_story_player, interactive_trace, plot_butterfly_network, plot_trace_overview

                signal = [1, 2, 3, 4]
                modulus = 7681
                psi = 1925
                trace = fast_ntt_psi_ct_trace(signal, modulus, psi)

                print("raw CT output (BO):", trace.raw_output)
                print("bit-reversed back to NO:", trace.normal_order_output)
                print("direct NTT_psi:", forward_ntt_psi(signal, modulus, psi))
                display(butterfly_story_player(trace))
                display(plot_trace_overview(trace, title="CT overview for [1,2,3,4]"))
                display(plot_butterfly_network(trace, title="Full CT network for [1,2,3,4]"))
                display(interactive_trace(trace, title="CT forward trace"))
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "What You Should Notice In The Stage Viewer",
                """
                Do not just read the final answer.
                Notice:

                - which pairs talk to each other in each stage
                - which `zeta` each pair uses
                - how the array order changes before the final bit-reversal correction
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Run The Second n=4 Paper Example",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace
                from ntt_learning.visuals import interactive_trace

                signal = [5, 6, 7, 8]
                trace = fast_ntt_psi_ct_trace(signal, 7681, 1925)
                print("BO output:", trace.raw_output)
                print("NO output:", trace.normal_order_output)
                display(interactive_trace(trace, title="Second CT trace"))
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Go One Stage Deeper With n=8",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace, find_psi
                from ntt_learning.visuals import butterfly_story_player, interactive_trace, plot_butterfly_network, plot_trace_overview

                signal = [0, 1, 2, 3, 4, 5, 6, 7]
                modulus = 97
                psi = find_psi(8, modulus)
                trace = fast_ntt_psi_ct_trace(signal, modulus, psi)

                print("psi:", psi)
                print("BO output:", trace.raw_output)
                print("NO output:", trace.normal_order_output)
                display(butterfly_story_player(trace))
                display(plot_trace_overview(trace, title="Three CT stages for n=8"))
                display(plot_butterfly_network(trace, title="Full CT network for n=8"))
                display(interactive_trace(trace, title="n=8 CT stage explorer"))
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "See BO Output And NO Output Side By Side",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace
                from ntt_learning.visuals import plot_bit_reversal_mapping, plot_vector_comparison

                trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], 7681, 1925)
                display(
                    plot_vector_comparison(
                        trace.raw_output,
                        trace.normal_order_output,
                        left_label="BO",
                        right_label="NO",
                        title="Same CT values, different ordering",
                    )
                )
                display(plot_bit_reversal_mapping(4, title="Why BO becomes NO after bit-reversal"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Retrieval Check",
                """
                1. What does CT change: the transform definition or the computation schedule?
                2. Why is the output naturally in BO rather than NO?
                3. In a stage diagram, what are the first three things you should inspect before any formula?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Inspect Stage Rows As Data",
                """
                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace, stage_rows

                trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], 7681, 1925)
                for stage in trace.stages:
                    print("stage", stage.stage_index)
                    for row in stage_rows(stage):
                        print(row)
                """,
            ),
            handoff_cell("lab.ipynb"),
        ],
        lab=[
            markdown(
                "meta",
                1,
                "orientation",
                "Lab Goals",
                """
                You should predict stage pairings and zetas before running the stage explorer.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "exercise",
                "Exercise 1",
                """
                For the `n = 4` example, predict:

                - which original coefficients pair in stage 1
                - which adjacent positions pair in stage 2
                - why the output is not yet in normal order
                """,
            ),
            code(
                "mandatory",
                3,
                "exercise",
                "Prediction Check For n=4",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace
                from ntt_learning.visuals import butterfly_story_player, interactive_trace

                trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], 7681, 1925)
                display(butterfly_story_player(trace))
                display(interactive_trace(trace, title="Check your n=4 prediction"))
                """,
            ),
            markdown(
                "mandatory",
                3,
                "exercise",
                "Exercise 2",
                """
                For the `n = 8` example, name the stage count before you run the next cell.
                Then name which stage feels most confusing and why.
                """,
            ),
            code(
                "mandatory",
                3,
                "exercise",
                "Prediction Check For n=8",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace, find_psi
                from ntt_learning.visuals import interactive_trace

                trace = fast_ntt_psi_ct_trace([0, 1, 2, 3, 4, 5, 6, 7], 97, find_psi(8, 97))
                display(interactive_trace(trace, title="Check your n=8 prediction"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Reflection prompt:

                - Which stage feels easiest to see by eye?
                - Which stage feels most like “pure schedule” rather than “new algebra”?
                - Why is BO output not a bug?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Change The n=8 Signal",
                """
                import ipywidgets as widgets
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace, find_psi
                from ntt_learning.visuals import interactive_trace

                psi = find_psi(8, 97)

                def preview(a0=0, a1=1, a2=2, a3=3, a4=4, a5=5, a6=6, a7=7):
                    trace = fast_ntt_psi_ct_trace([a0, a1, a2, a3, a4, a5, a6, a7], 97, psi)
                    display(interactive_trace(trace, title="Interactive n=8 CT trace"))

                display(
                    widgets.interact(
                        preview,
                        a0=(0, 12),
                        a1=(0, 12),
                        a2=(0, 12),
                        a3=(0, 12),
                        a4=(0, 12),
                        a5=(0, 12),
                        a6=(0, 12),
                        a7=(0, 12),
                    )
                )
                """,
            ),
            handoff_cell("problems.ipynb"),
        ],
        problems=[
            markdown(
                "meta",
                1,
                "orientation",
                "Problem Set Goals",
                """
                This notebook checks whether the CT schedule is now a visible object rather than a name.
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Multiple-Choice Retrieval",
                """
                Choose one answer for each:

                1. CT makes the transform faster by:
                   A. changing the ring
                   B. reusing bracket structure through staged butterflies
                   C. deleting the inverse

                2. The natural output order of the direct CT schedule discussed here is:
                   A. normal order
                   B. bit-reversed order
                   C. random order

                3. A stage explorer is useful mainly because it:
                   A. hides the pairings
                   B. makes data movement and zeta usage inspectable
                   C. removes the need for examples
                """,
            ),
            code(
                "mandatory",
                2,
                "quiz",
                "Answer Key",
                """
                answers = {1: "B", 2: "B", 3: "B"}
                print(answers)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Paper Example Check",
                """
                Verify that the CT trace on `[1,2,3,4]` in `Z_7681` with `ψ = 1925` lands on the paper’s BO output.
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "Check The BO Output",
                """
                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace

                trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], 7681, 1925)
                print(trace.raw_output)
                assert list(trace.raw_output) == [1467, 3471, 2807, 7621]
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Written Reflection",
                """
                Explain why the phrase “same transform, better schedule” is the right headline for CT.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional Challenge",
                """
                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace, find_psi

                trace = fast_ntt_psi_ct_trace([3, 1, 4, 1, 5, 9, 2, 6], 97, find_psi(8, 97))
                for stage in trace.stages:
                    print(stage.stage_index, stage.output_values)
                """,
            ),
            handoff_cell("studio.ipynb"),
        ],
        studio=[
            markdown(
                "meta",
                1,
                "orientation",
                "Studio Goals",
                """
                This studio compares CT traces and inspects where learners usually lose the plot: stage order, pair order, and BO output.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "Same Schedule, Different Signals",
                """
                The butterfly pattern is structural.
                The signal values change, but the pairing pattern and the zeta schedule stay tied to `n`, the modulus, and the chosen root.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Compare Two CT Traces",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace
                from ntt_learning.visuals import plot_butterfly_network, plot_trace_overview

                trace_a = fast_ntt_psi_ct_trace([1, 2, 3, 4], 7681, 1925)
                trace_b = fast_ntt_psi_ct_trace([5, 6, 7, 8], 7681, 1925)

                display(plot_trace_overview(trace_a, title="CT trace A"))
                display(plot_trace_overview(trace_b, title="CT trace B"))
                display(plot_butterfly_network(trace_a, title="CT network A"))
                display(plot_butterfly_network(trace_b, title="CT network B"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Debug Checklist",
                """
                If a CT implementation looks wrong, inspect:

                1. the chosen `ψ`
                2. the stage pairings
                3. the zeta exponent sequence
                4. whether you remembered the final BO -> NO reorder when comparing against the direct transform
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "See A Wrong-Order Comparison Failure",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace, forward_ntt_psi
                from ntt_learning.visuals import plot_vector_comparison

                trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], 7681, 1925)
                direct = forward_ntt_psi([1, 2, 3, 4], 7681, 1925)

                print("wrong comparison: CT BO output vs direct NO output")
                print(trace.raw_output, direct)
                print("correct comparison: CT NO output vs direct NO output")
                print(trace.normal_order_output, direct)
                display(
                    plot_vector_comparison(
                        trace.raw_output,
                        direct,
                        left_label="CT_BO",
                        right_label="direct_NO",
                        title="Wrong comparison: BO against NO",
                    )
                )
                display(
                    plot_vector_comparison(
                        trace.normal_order_output,
                        direct,
                        left_label="CT_NO",
                        right_label="direct_NO",
                        title="Correct comparison after reordering",
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                In one paragraph, explain why a learner can understand the direct transform and still get lost in CT if the stage order and output order are not shown visually.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Inspect The zeta schedule",
                """
                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace

                trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], 7681, 1925)
                for stage in trace.stages:
                    print("stage", stage.stage_index, "zetas:", stage.zetas)
                """,
            ),
            handoff_cell("../../../butterfly_mechanics/04_fast_inverse_gs/lecture.ipynb"),
        ],
    )


def build_bundle_04() -> None:
    bundle_dir = BUNDLE_DIRS[3]
    write_bundle(
        bundle_dir,
        "Fast Inverse GS",
        lecture=[
            markdown(
                "meta",
                1,
                "orientation",
                "Objectives",
                """
                This bundle makes the inverse flow explicit.

                Focus:

                - GS as the fast inverse schedule
                - BO input and NO output
                - why the final `n^-1` scaling appears
                - how bit-reversal fits the forward/inverse pair
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "GS Feels Like The Same Network Seen From The Other End",
                """
                The inverse is not “mysterious undoing”.
                It is a staged network with the same family resemblance as CT, but with a different direction of arithmetic and a final scaling.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Trace The Exact n=4 GS Paper Example",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace
                from ntt_learning.visuals import interactive_trace, plot_butterfly_network, plot_trace_overview, plot_vector_comparison

                bo_input = [1467, 3471, 2807, 7621]
                trace = fast_intt_psi_gs_trace(bo_input, 7681, 1925)

                print("unscaled NO output:", trace.raw_output)
                print("scaled NO output:", trace.scaled_output)
                display(plot_trace_overview(trace, title="GS overview for the n=4 paper example"))
                display(plot_butterfly_network(trace, title="Full GS network for the n=4 paper example"))
                display(
                    plot_vector_comparison(
                        trace.raw_output,
                        trace.scaled_output,
                        left_label="unscaled",
                        right_label="scaled",
                        title="Why the final n^-1 scaling matters",
                    )
                )
                display(interactive_trace(trace, title="GS inverse trace"))
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "See The Bit-Reversal Map Explicitly",
                """
                from IPython.display import display

                from ntt_learning.visuals import plot_bit_reversal_mapping

                display(plot_bit_reversal_mapping(4, title="Bit-reversal for n=4"))
                display(plot_bit_reversal_mapping(8, title="Bit-reversal for n=8"))
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "Why Scaling Waits Until The End",
                """
                Each GS stage avoids local division by `2`.
                The accumulated effect of those missing local divisions is corrected by the final multiplication with `n^-1`.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Full Forward And Inverse Round Trip",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace, fast_ntt_psi_ct_trace
                from ntt_learning.visuals import plot_vector_comparison

                signal = [1, 2, 3, 4]
                forward_trace = fast_ntt_psi_ct_trace(signal, 7681, 1925)
                inverse_trace = fast_intt_psi_gs_trace(forward_trace.raw_output, 7681, 1925)

                print("forward BO output:", forward_trace.raw_output)
                print("inverse scaled output:", inverse_trace.scaled_output)
                display(
                    plot_vector_comparison(
                        signal,
                        inverse_trace.scaled_output,
                        left_label="original",
                        right_label="recovered",
                        title="Forward CT followed by inverse GS",
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Retrieval Check",
                """
                1. Why does GS want BO input?
                2. Why does the final scaling not disappear?
                3. What would go wrong if you visually compared GS input and CT NO output without respecting the order change?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: A Second GS Example",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace
                from ntt_learning.visuals import interactive_trace

                trace = fast_intt_psi_gs_trace([2489, 6478, 7489, 6607], 7681, 1925)
                print("scaled output:", trace.scaled_output)
                display(interactive_trace(trace, title="Second GS trace"))
                """,
            ),
            handoff_cell("lab.ipynb"),
        ],
        lab=[
            markdown(
                "meta",
                1,
                "orientation",
                "Lab Goals",
                """
                Predict the BO input and the final scaling before you run the stage explorer.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "exercise",
                "Exercise 1",
                """
                Explain before running the next cell:

                - why the GS input must be BO in the standard schedule
                - why the unscaled output is not yet the original signal
                """,
            ),
            code(
                "mandatory",
                3,
                "exercise",
                "Prediction Check",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace
                from ntt_learning.visuals import interactive_trace

                trace = fast_intt_psi_gs_trace([1467, 3471, 2807, 7621], 7681, 1925)
                display(interactive_trace(trace, title="Check your GS prediction"))
                """,
            ),
            markdown(
                "mandatory",
                3,
                "exercise",
                "Exercise 2",
                """
                Predict the bit-reversal of `[0,1,2,3,4,5,6,7]` before running the next cell.
                """,
            ),
            code(
                "mandatory",
                3,
                "exercise",
                "Prediction Check For Ordering",
                """
                from ntt_learning.toy_ntt import bit_reversed_order

                print(bit_reversed_order([0, 1, 2, 3, 4, 5, 6, 7]))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Reflection prompt:

                - Which part of GS felt like a true inverse to you?
                - Which part felt like pure bookkeeping?
                - Why is the ordering story impossible to ignore?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Explore Another BO Input",
                """
                import ipywidgets as widgets
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace
                from ntt_learning.visuals import interactive_trace

                def preview(x0=1467, x1=3471, x2=2807, x3=7621):
                    trace = fast_intt_psi_gs_trace([x0, x1, x2, x3], 7681, 1925)
                    display(interactive_trace(trace, title="Interactive GS trace"))

                display(
                    widgets.interact(
                        preview,
                        x0=(0, 7680),
                        x1=(0, 7680),
                        x2=(0, 7680),
                        x3=(0, 7680),
                    )
                )
                """,
            ),
            handoff_cell("problems.ipynb"),
        ],
        problems=[
            markdown(
                "meta",
                1,
                "orientation",
                "Problem Set Goals",
                """
                This notebook checks whether the inverse flow, ordering, and scaling are now mechanically stable.
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Multiple-Choice Retrieval",
                """
                Choose one answer for each:

                1. GS is used here as the fast schedule for:
                   A. direct forward NTT
                   B. inverse NTT
                   C. schoolbook multiplication

                2. The final `n^-1` matters because:
                   A. each stage skipped local divisions that accumulate
                   B. the modulus changed mid-computation
                   C. bit-reversal requires scaling

                3. In the standard pairing, GS expects:
                   A. NO input and BO output
                   B. BO input and NO output
                   C. random order on both ends
                """,
            ),
            code(
                "mandatory",
                2,
                "quiz",
                "Answer Key",
                """
                answers = {1: "B", 2: "A", 3: "B"}
                print(answers)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Paper Example Check",
                """
                Verify that the GS trace on the paper’s BO input scales back to `[1,2,3,4]`.
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "Check The Final Scaling",
                """
                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace

                trace = fast_intt_psi_gs_trace([1467, 3471, 2807, 7621], 7681, 1925)
                print(trace.scaled_output)
                assert list(trace.scaled_output) == [1, 2, 3, 4]
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Written Reflection",
                """
                In one paragraph, explain why “same structure, opposite direction” is a better intuition for GS than “totally different algorithm”.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional Challenge",
                """
                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace

                trace = fast_intt_psi_gs_trace([2489, 6478, 7489, 6607], 7681, 1925)
                for stage in trace.stages:
                    print(stage.stage_index, stage.output_values)
                """,
            ),
            handoff_cell("studio.ipynb"),
        ],
        studio=[
            markdown(
                "meta",
                1,
                "orientation",
                "Studio Goals",
                """
                The studio puts CT and GS next to each other and treats ordering as a first-class object, not a side note.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "Forward And Inverse Need To Meet In The Middle Cleanly",
                """
                The whole point of the pair is:

                - CT gets you into the transform domain efficiently
                - GS gets you back out efficiently
                - the two only meet cleanly if you respect BO/NO and the final scaling
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "See CT Output Feed GS Input",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace, fast_ntt_psi_ct_trace
                from ntt_learning.visuals import plot_vector_comparison

                signal = [5, 6, 7, 8]
                forward_trace = fast_ntt_psi_ct_trace(signal, 7681, 1925)
                inverse_trace = fast_intt_psi_gs_trace(forward_trace.raw_output, 7681, 1925)

                print("CT BO output:", forward_trace.raw_output)
                print("GS scaled output:", inverse_trace.scaled_output)
                display(
                    plot_vector_comparison(
                        signal,
                        inverse_trace.scaled_output,
                        left_label="start",
                        right_label="after_CT_then_GS",
                        title="CT output cleanly feeds GS input",
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Debug Checklist",
                """
                If the inverse output is wrong, inspect:

                1. whether the input was BO
                2. whether the zetas were inverse-stage zetas
                3. whether the final `n^-1` scaling was applied
                4. whether you compared the correct order against the direct reference
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "See A Missing-Scale Failure",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace
                from ntt_learning.visuals import plot_vector_comparison

                trace = fast_intt_psi_gs_trace([1467, 3471, 2807, 7621], 7681, 1925)
                print("unscaled:", trace.raw_output)
                print("scaled:", trace.scaled_output)
                display(
                    plot_vector_comparison(
                        trace.raw_output,
                        trace.scaled_output,
                        left_label="missing_scale",
                        right_label="correct",
                        title="Missing n^-1 scale vs correct output",
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Explain why “the inverse looked almost right” is a dangerous debugging sentence unless you say what happened with ordering and scaling.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Another bit-reversal map",
                """
                from IPython.display import display

                from ntt_learning.visuals import plot_bit_reversal_mapping

                display(plot_bit_reversal_mapping(16, title="Bit-reversal for n=16"))
                """,
            ),
            handoff_cell("../../../kyber_mapping/05_kyber_ntt_and_base_multiplication/lecture.ipynb"),
        ],
    )


def build_bundle_05() -> None:
    bundle_dir = BUNDLE_DIRS[4]
    write_bundle(
        bundle_dir,
        "Kyber NTT And Base Multiplication",
        lecture=[
            markdown(
                "meta",
                1,
                "orientation",
                "Objectives",
                """
                This bundle ties the transform story to Kyber without throwing away the concrete arithmetic.

                Focus:

                - what Kyber’s `q = 3329`, `n = 256` really allow
                - why the full `2n`-th root mental model breaks at Kyber v3
                - why base multiplication appears
                - how to keep the story NTT-centered without lying about the modulus
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "Kyber Is Not “Just Generic Negacyclic NTT With Big Numbers”",
                """
                The key arithmetic reality is:

                - Kyber v3 has `n = 256`
                - `q = 3329`
                - `256` divides `3328`
                - `512` does **not** divide `3328`

                That means a primitive `256`-th root exists, but a primitive `512`-th root does not.
                So the clean full-length `ψ` story from the toy negative-wrapped transform does not lift over unchanged.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "See The Stage Skeleton For n=16 And n=256",
                """
                from IPython.display import display

                from ntt_learning.visuals import plot_stage_pairing_map, plot_stage_schedule

                display(plot_stage_schedule(16, title="Readable schedule skeleton for n=16"))
                display(plot_stage_pairing_map(16, 2, title="Stage 1 geometry for n=16"))
                display(plot_stage_pairing_map(16, 16, title="Final stage geometry for n=16"))
                display(plot_stage_schedule(256, title="Kyber-scale stage skeleton for n=256"))
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Check The Kyber Root Reality Directly",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import find_primitive_root
                from ntt_learning.visuals import plot_root_order_comparison

                print("3329 - 1 =", 3329 - 1)
                print("primitive 256-th root in Z_3329:", find_primitive_root(256, 3329))
                try:
                    find_primitive_root(512, 3329)
                except Exception as exc:
                    print("512-th root fails exactly because:", exc)

                display(
                    plot_root_order_comparison(
                        [(4, 17), (4, 13), (8, 97), (256, 3329)],
                        title="Which moduli allow n-th and 2n-th root stories?",
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "Tiny Analogue Of The Same Obstruction",
                """
                The easiest way to feel this is to shrink the numbers.
                In `Z_13`, a 4-th root exists because `4 | 12`, but an 8-th root does not because `8` does not divide `12`.

                That is the same shape of obstruction as Kyber v3, only tiny enough to inspect instantly.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Run The Tiny Analogue",
                """
                from ntt_learning.toy_ntt import find_primitive_root

                print("primitive 4-th root in Z_13:", find_primitive_root(4, 13))
                try:
                    find_primitive_root(8, 13)
                except Exception as exc:
                    print("8-th root fails:", exc)
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "Why Base Multiplication Appears",
                """
                Once the ring does not split into fully scalar transform slots in the naive `ψ` way, multiplication in the transform domain is no longer “just multiply scalars slot by slot”.

                A small block structure remains, and that is why pairwise base multiplication appears.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "See A Toy Base Multiplication",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import base_multiply_pair
                from ntt_learning.visuals import plot_base_multiply_pair_diagram

                left = [7, 11]
                right = [5, 13]
                zeta = 4
                modulus = 17

                raw = [left[0] * right[0], left[0] * right[1] + left[1] * right[0], left[1] * right[1]]
                reduced = [(raw[0] + zeta * raw[2]) % modulus, raw[1] % modulus]

                print("raw degree-2 product:", raw)
                print("reduce with x^2 = zeta:", reduced)
                print("base_multiply_pair:", base_multiply_pair(left, right, zeta, modulus))
                display(
                    plot_base_multiply_pair_diagram(
                        left,
                        right,
                        zeta=zeta,
                        modulus=modulus,
                        title="Why Kyber-style multiplication stays in 2-slot blocks",
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Retrieval Check",
                """
                1. What exact divisibility fact blocks the naive full `2n`-th root story in Kyber v3?
                2. Why does that obstruction point you toward base multiplication?
                3. Why would it be misleading to teach Kyber as if the toy `ψ` story carried over unchanged?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Compare Several Moduli",
                """
                def status(n, q):
                    pwc = (q - 1) % n == 0
                    nwc = (q - 1) % (2 * n) == 0
                    return {"n": n, "q": q, "pwc": pwc, "nwc": nwc}

                for sample in [(4, 17), (4, 13), (256, 7681), (256, 3329)]:
                    print(status(*sample))
                """,
            ),
            handoff_cell("lab.ipynb"),
        ],
        lab=[
            markdown(
                "meta",
                1,
                "orientation",
                "Lab Goals",
                """
                The lab is about making the Kyber modulus obstruction explicit enough that it becomes memorable.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "exercise",
                "Exercise 1",
                """
                Before running the next cell, say out loud:

                - why `256 | 3328`
                - why `512` does not divide `3328`
                - what that means for the existence of `ψ`
                """,
            ),
            code(
                "mandatory",
                3,
                "exercise",
                "Prediction Check",
                """
                print("3328 / 256 =", (3329 - 1) // 256)
                print("3328 % 256 =", (3329 - 1) % 256)
                print("3328 % 512 =", (3329 - 1) % 512)
                """,
            ),
            markdown(
                "mandatory",
                3,
                "exercise",
                "Exercise 2",
                """
                Verify the toy base multiplication by hand before running the next cell.
                """,
            ),
            code(
                "mandatory",
                3,
                "exercise",
                "Check The Toy Base Multiplication",
                """
                from ntt_learning.toy_ntt import base_multiply_pair

                print(base_multiply_pair([3, 5], [2, 7], zeta=6, modulus=17))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Reflection prompt:

                - Why is “there is no 512-th root” not just a technical footnote?
                - What false picture of Kyber would survive if you ignored that fact?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Tiny Modulus Classifier",
                """
                import ipywidgets as widgets
                from IPython.display import display

                def classify(q=17, n=4):
                    print({"q": q, "n": n, "pwc": (q - 1) % n == 0, "nwc": (q - 1) % (2 * n) == 0})

                display(widgets.interact(classify, q=(5, 101), n=(2, 16)))
                """,
            ),
            handoff_cell("problems.ipynb"),
        ],
        problems=[
            markdown(
                "meta",
                1,
                "orientation",
                "Problem Set Goals",
                """
                This notebook checks whether the Kyber-specific modulus story is now precise instead of fuzzy.
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Multiple-Choice Retrieval",
                """
                Choose one answer for each:

                1. For Kyber v3, the important root fact is:
                   A. `512` divides `3328`
                   B. `256` divides `3328` but `512` does not
                   C. no relevant root exists at all

                2. Base multiplication appears because:
                   A. the transform-domain multiplication remains structured in small blocks
                   B. scalar multiplication is forbidden in finite fields
                   C. schoolbook multiplication vanished

                3. The biggest pedagogical risk is:
                   A. teaching Kyber as if the toy `ψ` model applied unchanged
                   B. teaching any toy examples at all
                   C. comparing moduli
                """,
            ),
            code(
                "mandatory",
                2,
                "quiz",
                "Answer Key",
                """
                answers = {1: "B", 2: "A", 3: "A"}
                print(answers)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Quick Check",
                """
                Explain in one sentence why a primitive 256-th root is not enough to recover the full toy `ψ` story at `n = 256`.
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "Numerical Check",
                """
                print("2 * 256 =", 2 * 256)
                print("3329 - 1 =", 3329 - 1)
                print("divides?", (3329 - 1) % (2 * 256) == 0)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Written Reflection",
                """
                In one paragraph, explain why the Kyber notebook belongs after the toy direct and fast-transform notebooks rather than before them.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional Challenge",
                """
                samples = [(256, 7681), (256, 3329), (8, 97), (8, 41)]
                for n, q in samples:
                    print({"n": n, "q": q, "n_divides_q_minus_1": (q - 1) % n == 0, "two_n_divides_q_minus_1": (q - 1) % (2 * n) == 0})
                """,
            ),
            handoff_cell("studio.ipynb"),
        ],
        studio=[
            markdown(
                "meta",
                1,
                "orientation",
                "Studio Goals",
                """
                This studio compares the clean toy story with the Kyber-specific modulus reality and treats the mismatch as the lesson.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "The Mismatch Is Not A Bug In The Course",
                """
                The mismatch between “toy full `ψ` story” and “Kyber v3 modulus reality” is exactly what the learner needs to understand.

                That mismatch is why base multiplication and implementation-specific scheduling matter.
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Toy Full ψ Story vs Kyber Root Reality",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import find_psi
                from ntt_learning.visuals import plot_root_order_comparison

                print("toy n=4, q=17 has psi:", find_psi(4, 17))
                try:
                    find_psi(256, 3329)
                except Exception as exc:
                    print("Kyber v3 does not have that full psi story:", exc)

                display(
                    plot_root_order_comparison(
                        [(4, 17), (256, 7681), (256, 3329)],
                        title="Toy full psi story vs Kyber modulus reality",
                    )
                )
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Debug Checklist",
                """
                If somebody says “Kyber is just the same toy negative-wrapped NTT with bigger numbers”, inspect:

                1. whether they checked `2n | q - 1`
                2. whether they accounted for the missing `ψ`
                3. whether they know why base multiplication appears
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "See The Exact Obstruction Again",
                """
                from IPython.display import display

                from ntt_learning.visuals import plot_root_order_comparison

                q = 3329
                n = 256
                print({"q_minus_1": q - 1, "n": n, "2n": 2 * n, "q_minus_1_mod_n": (q - 1) % n, "q_minus_1_mod_2n": (q - 1) % (2 * n)})
                display(plot_root_order_comparison([(256, 3329)], title="Kyber v3 obstruction in one row"))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Explain why the Kyber base-multiplication story is easier to trust once you have already internalized the toy negacyclic transform.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Another toy base multiplication",
                """
                from ntt_learning.toy_ntt import base_multiply_pair

                print(base_multiply_pair([7, 9], [4, 6], zeta=11, modulus=17))
                """,
            ),
            handoff_cell("../../../professional/06_debugging_ntt_failures/lecture.ipynb"),
        ],
    )


def build_bundle_06() -> None:
    bundle_dir = BUNDLE_DIRS[5]
    write_bundle(
        bundle_dir,
        "Debugging NTT Failures",
        lecture=[
            markdown(
                "meta",
                1,
                "orientation",
                "Objectives",
                """
                This final bundle turns common failure modes into visible patterns instead of vague warnings.

                Focus:

                - wrong sign in wraparound
                - wrong root or wrong zeta
                - wrong BO / NO comparison
                - missing final scaling
                - wrong mental model for the Kyber modulus
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "Bad Outputs Have Fingerprints",
                """
                Debugging NTTs is easier when you stop staring at the final vector as one blob.
                Each common mistake leaves a characteristic fingerprint:

                - wrong sign flips specific wrapped slots
                - wrong order makes a correct value set appear shuffled
                - missing `n^-1` keeps the shape but scales everything wrong
                - wrong zeta corrupts local pair structure early
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "See Four Failure Modes Side By Side",
                """
                from IPython.display import display

                from ntt_learning.toy_ntt import (
                    fast_intt_psi_gs_trace,
                    fast_ntt_psi_ct_trace,
                    forward_ntt_psi,
                    negacyclic_reduce,
                    schoolbook_convolution,
                )
                from ntt_learning.visuals import plot_vector_comparison

                signal = [1, 2, 3, 4]
                forward_trace = fast_ntt_psi_ct_trace(signal, 7681, 1925)
                inverse_trace = fast_intt_psi_gs_trace(forward_trace.raw_output, 7681, 1925)

                raw = schoolbook_convolution([1, 2, 3, 4], [5, 6, 7, 8])
                wrong_sign = [raw[0] + raw[4], raw[1] + raw[5], raw[2] + raw[6], raw[3]]
                wrong_order = list(forward_trace.raw_output)
                wrong_scale = list(inverse_trace.raw_output)
                wrong_root = forward_ntt_psi(signal, 7681, 3383)

                print("wrong sign fold:", wrong_sign)
                print("correct sign fold:", negacyclic_reduce(raw, n=4))
                print("wrong BO-vs-NO comparison:", wrong_order)
                print("correct NO output:", forward_trace.normal_order_output)
                print("missing final scaling:", wrong_scale)
                print("wrong root in direct transform:", wrong_root)
                display(
                    plot_vector_comparison(
                        wrong_sign,
                        negacyclic_reduce(raw, n=4),
                        left_label="wrong_sign",
                        right_label="correct_sign",
                        title="Wrong sign vs correct negacyclic fold",
                    )
                )
                display(
                    plot_vector_comparison(
                        wrong_order,
                        forward_trace.normal_order_output,
                        left_label="wrong_order",
                        right_label="correct_order",
                        title="Wrong BO/NO comparison",
                    )
                )
                display(
                    plot_vector_comparison(
                        wrong_scale,
                        inverse_trace.scaled_output,
                        left_label="missing_scale",
                        right_label="correct_scale",
                        title="Missing scale vs corrected inverse",
                    )
                )
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Interactive Failure Picker",
                """
                import ipywidgets as widgets
                from IPython.display import display

                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace, fast_ntt_psi_ct_trace, forward_ntt_psi
                from ntt_learning.visuals import plot_vector_comparison

                forward_trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], 7681, 1925)
                inverse_trace = fast_intt_psi_gs_trace(forward_trace.raw_output, 7681, 1925)

                failures = {
                    "wrong_order": list(forward_trace.raw_output),
                    "correct_order": list(forward_trace.normal_order_output),
                    "missing_scale": list(inverse_trace.raw_output),
                    "scaled": list(inverse_trace.scaled_output),
                    "wrong_root": forward_ntt_psi([1, 2, 3, 4], 7681, 3383),
                }
                references = {
                    "wrong_order": list(forward_trace.normal_order_output),
                    "correct_order": list(forward_trace.normal_order_output),
                    "missing_scale": list(inverse_trace.scaled_output),
                    "scaled": list(inverse_trace.scaled_output),
                    "wrong_root": list(forward_ntt_psi([1, 2, 3, 4], 7681, 1925)),
                }

                def preview(mode="wrong_order"):
                    print(mode, "->", failures[mode])
                    display(
                        plot_vector_comparison(
                            failures[mode],
                            references[mode],
                            left_label=mode,
                            right_label="reference",
                            title=f"{mode} compared with the correct reference",
                        )
                    )

                display(widgets.interact(preview, mode=sorted(failures)))
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Retrieval Check",
                """
                1. Which mistake keeps the general shape of the inverse output but leaves every entry too large by a shared factor?
                2. Which mistake often disappears once you apply the correct BO -> NO reorder?
                3. Which mistake shows up earliest in local pair traces rather than only at the very end?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Trace Rows For Debugging",
                """
                from ntt_learning.toy_ntt import fast_ntt_psi_ct_trace, stage_rows

                trace = fast_ntt_psi_ct_trace([1, 2, 3, 4], 7681, 1925)
                for stage in trace.stages:
                    print("stage", stage.stage_index)
                    for row in stage_rows(stage):
                        print(row)
                """,
            ),
            handoff_cell("lab.ipynb"),
        ],
        lab=[
            markdown(
                "meta",
                1,
                "orientation",
                "Lab Goals",
                """
                The lab asks you to match output fingerprints to the underlying bug.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "exercise",
                "Exercise 1",
                """
                Before running the next cell, predict which of these bug labels goes with each fingerprint:

                - shuffled but otherwise familiar values
                - values that look uniformly too large
                - values broken already in a local stage pair
                """,
            ),
            code(
                "mandatory",
                3,
                "exercise",
                "Prediction Check",
                """
                fingerprints = {
                    "wrong_order": "shuffled but same value set",
                    "missing_scale": "same shape but uniformly off by a factor",
                    "wrong_zeta": "local pair outputs go bad immediately",
                }
                print(fingerprints)
                """,
            ),
            markdown(
                "mandatory",
                3,
                "exercise",
                "Exercise 2",
                """
                Explain why “almost right” is a useless debugging description unless you also specify whether the issue is:

                - sign
                - order
                - zeta
                - scaling
                """,
            ),
            code(
                "mandatory",
                3,
                "exercise",
                "A Small Debugging Drill",
                """
                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace, fast_ntt_psi_ct_trace

                forward_trace = fast_ntt_psi_ct_trace([5, 6, 7, 8], 7681, 1925)
                inverse_trace = fast_intt_psi_gs_trace(forward_trace.raw_output, 7681, 1925)

                print("forward BO output:", forward_trace.raw_output)
                print("forward NO output:", forward_trace.normal_order_output)
                print("inverse unscaled:", inverse_trace.raw_output)
                print("inverse scaled:", inverse_trace.scaled_output)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Reflection",
                """
                Reflection prompt:

                - Which bug fingerprint feels easiest to recognize now?
                - Which one still needs more repetition?
                - What is your debugging order of operations now?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Build Your Own Fingerprint Table",
                """
                import ipywidgets as widgets
                from IPython.display import display

                def note_bug(mode="wrong_order"):
                    print({"mode": mode, "what_to_check_first": {"wrong_order": "bit reversal", "missing_scale": "n^-1", "wrong_zeta": "local pair twiddle", "wrong_sign": "negacyclic fold sign"}[mode]})

                display(widgets.interact(note_bug, mode=["wrong_order", "missing_scale", "wrong_zeta", "wrong_sign"]))
                """,
            ),
            handoff_cell("problems.ipynb"),
        ],
        problems=[
            markdown(
                "meta",
                1,
                "orientation",
                "Problem Set Goals",
                """
                This notebook checks whether the main NTT bug classes are now distinct in memory.
                """,
            ),
            markdown(
                "mandatory",
                2,
                "quiz",
                "Multiple-Choice Retrieval",
                """
                Choose one answer for each:

                1. A shuffled but otherwise familiar forward result most strongly suggests:
                   A. missing final scaling
                   B. wrong BO / NO comparison
                   C. wrong modulus

                2. An inverse output that looks like a clean multiple of the target most strongly suggests:
                   A. missing `n^-1`
                   B. wrong wraparound sign
                   C. wrong bit-reversal map

                3. A local pair that already looks broken in stage 1 most strongly suggests:
                   A. wrong zeta
                   B. correct CT output
                   C. harmless ordering noise
                """,
            ),
            code(
                "mandatory",
                2,
                "quiz",
                "Answer Key",
                """
                answers = {1: "B", 2: "A", 3: "A"}
                print(answers)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Debug Priority Check",
                """
                List the first four checks you would run on a suspicious iNTT output.
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "One Good Ordering",
                """
                debug_order = [
                    "check BO / NO assumption",
                    "check root / zeta schedule",
                    "check final n^-1 scaling",
                    "check sign / wraparound conventions",
                ]
                print(debug_order)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Written Reflection",
                """
                In one paragraph, explain why visible traces are much better debugging tools than only comparing final vectors.
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional Challenge",
                """
                mistakes = {
                    "wrong_order": "fix the permutation first",
                    "missing_scale": "multiply by n^-1",
                    "wrong_zeta": "rebuild the twiddle schedule",
                    "wrong_sign": "inspect the quotient ring",
                }
                for key, value in mistakes.items():
                    print(key, "->", value)
                """,
            ),
            handoff_cell("studio.ipynb"),
        ],
        studio=[
            markdown(
                "meta",
                1,
                "orientation",
                "Studio Goals",
                """
                The last studio compresses the whole course into one debugging mindset.
                """,
            ),
            markdown(
                "mandatory",
                3,
                "explanation",
                "The Whole Course Is A Debugging Ladder",
                """
                Every earlier bundle built one layer of the debugging stack:

                - schoolbook grid and wraparound
                - direct transform algebra
                - CT stage schedule
                - GS inverse schedule
                - bit-reversal and scaling
                - Kyber modulus constraints and base multiplication
                """,
            ),
            code(
                "mandatory",
                3,
                "demo",
                "Print The Whole Debugging Ladder",
                """
                ladder = [
                    "Can I see the raw schoolbook product grid?",
                    "Can I explain the negacyclic wraparound sign?",
                    "Can I reproduce the direct NTT_psi / INTT_psi round trip?",
                    "Can I trace CT stages with the right zetas?",
                    "Can I trace GS stages with the right order and scaling?",
                    "Can I explain why Kyber v3 does not inherit the full toy psi story unchanged?",
                ]
                for item in ladder:
                    print("-", item)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "exercise",
                "Final Debug Checklist",
                """
                Keep this order:

                1. ring rule and wraparound
                2. root existence and root choice
                3. stage pairings and zetas
                4. BO vs NO comparison
                5. final `n^-1` scaling
                6. Kyber-specific modulus / base-multiplication assumptions
                """,
            ),
            code(
                "mandatory",
                2,
                "exercise",
                "One Last Round Trip",
                """
                from ntt_learning.toy_ntt import fast_intt_psi_gs_trace, fast_ntt_psi_ct_trace

                signal = [3, 1, 4, 1]
                forward_trace = fast_ntt_psi_ct_trace(signal, 17, 2)
                inverse_trace = fast_intt_psi_gs_trace(forward_trace.raw_output, 17, 2)

                print("signal:", signal)
                print("forward BO:", forward_trace.raw_output)
                print("inverse scaled:", inverse_trace.scaled_output)
                """,
            ),
            markdown(
                "mandatory",
                2,
                "reflection",
                "Final Reflection",
                """
                Final prompt:

                - Which image now anchors your understanding of NTT best: the schoolbook grid, the fold arrows, the CT stage view, the GS stage view, or the bit-reversal map?
                - Why that one?
                """,
            ),
            code(
                "facultative",
                4,
                "exploration",
                "Optional: Personal Debug Rule",
                """
                personal_rule = "Never trust a final vector until I have checked the stage trace, the order, and the scaling."
                print(personal_rule)
                """,
            ),
            handoff_cell("../../../COURSE_COMPLETE.ipynb"),
        ],
    )


def build_notebooks() -> None:
    build_start_here()
    build_course_blueprint()
    build_bundle_01()
    build_bundle_02()
    build_bundle_03()
    build_bundle_04()
    build_bundle_05()
    build_bundle_06()
    build_course_complete()


if __name__ == "__main__":
    build_notebooks()
