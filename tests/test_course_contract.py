from __future__ import annotations

import json
import unittest
from pathlib import Path

from ntt_learning.course import (
    ALL_NOTEBOOKS,
    CELL_ROLES,
    FACULTATIVE_DIFFICULTIES,
    MANDATORY_DIFFICULTIES,
    REPO_ROOT,
    ROUTE_NOTEBOOKS,
    ROUTE_ONLY_ROLES,
    TECHNICAL_NOTEBOOKS,
)


def read_notebook(relative_path: Path) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def cell_source(cell: dict[str, object]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


class CourseContractTests(unittest.TestCase):
    def test_expected_notebooks_exist(self) -> None:
        for notebook in ALL_NOTEBOOKS:
            self.assertTrue((REPO_ROOT / notebook).exists(), notebook.as_posix())

    def test_every_labeled_cell_has_contract_metadata(self) -> None:
        for notebook in ALL_NOTEBOOKS:
            payload = read_notebook(notebook)
            for cell in payload["cells"]:
                source = cell_source(cell).strip()
                if not source:
                    continue

                pedagogy = cell.get("metadata", {}).get("pedagogy", {})
                role = pedagogy.get("role")
                difficulty = pedagogy.get("difficulty")
                kind = pedagogy.get("kind")

                self.assertIn(role, CELL_ROLES, f"{notebook}: bad role")
                self.assertIsInstance(difficulty, int, f"{notebook}: missing difficulty")
                self.assertIsInstance(kind, str, f"{notebook}: missing kind")

                if role == "mandatory":
                    self.assertIn(difficulty, MANDATORY_DIFFICULTIES, f"{notebook}: bad mandatory difficulty")
                if role == "facultative":
                    self.assertIn(
                        difficulty,
                        FACULTATIVE_DIFFICULTIES,
                        f"{notebook}: bad facultative difficulty",
                    )

                if cell["cell_type"] == "markdown":
                    if kind == "theme":
                        self.assertIn("<style>", source, f"{notebook}: theme cell should inject styles")
                    else:
                        title = pedagogy.get("title")
                        self.assertIn('class="ntt-cell-head', source, f"{notebook}: missing notebook chrome")
                        self.assertIn(f'<h2 class="ntt-cell-title">{title}</h2>', source, f"{notebook}: missing content title")
                if cell["cell_type"] == "code":
                    title = pedagogy.get("title")
                    self.assertTrue(source.startswith(f"# {title}"), f"{notebook}: code cell should start with content title")

    def test_role_labels_do_not_appear_as_headlines(self) -> None:
        for notebook in ALL_NOTEBOOKS:
            payload = read_notebook(notebook)
            for cell in payload["cells"]:
                if cell["cell_type"] != "markdown":
                    continue
                source = cell_source(cell)
                self.assertNotIn("## META", source, f"{notebook}: role label leaked into headline")
                self.assertNotIn("## MANDATORY", source, f"{notebook}: role label leaked into headline")
                self.assertNotIn("## FACULTATIVE", source, f"{notebook}: role label leaked into headline")

    def test_route_notebooks_stay_pure(self) -> None:
        for notebook in ROUTE_NOTEBOOKS:
            payload = read_notebook(notebook)
            for cell in payload["cells"]:
                self.assertEqual(cell["cell_type"], "markdown", f"{notebook}: route notebook should be markdown only")
                role = cell.get("metadata", {}).get("pedagogy", {}).get("role")
                self.assertIn(role, ROUTE_ONLY_ROLES, f"{notebook}: route notebook contains non-route role")

    def test_every_notebook_has_handoff(self) -> None:
        for notebook in ALL_NOTEBOOKS:
            payload = read_notebook(notebook)
            sources = [cell_source(cell) for cell in payload["cells"]]
            self.assertTrue(any("Next notebook:" in source for source in sources), f"{notebook}: missing handoff")
            self.assertTrue(any("](" in source for source in sources if "Next notebook:" in source), f"{notebook}: handoff should be clickable")

    def test_every_notebook_has_route_guardrails(self) -> None:
        for notebook in ALL_NOTEBOOKS:
            payload = read_notebook(notebook)
            route_nav_cells = [
                cell
                for cell in payload["cells"]
                if cell.get("metadata", {}).get("pedagogy", {}).get("kind") == "route_nav"
            ]
            self.assertEqual(len(route_nav_cells), 1, f"{notebook}: expected one route navigation cell")
            source = cell_source(route_nav_cells[0])
            self.assertIn("Official route chain", source, f"{notebook}: missing route chain")
            self.assertIn("Restart route:", source, f"{notebook}: missing restart link")
            self.assertIn("](", source, f"{notebook}: route navigation must contain clickable links")

    def test_technical_notebooks_include_interaction_prompts(self) -> None:
        for notebook in TECHNICAL_NOTEBOOKS:
            payload = read_notebook(notebook)
            kinds = {
                cell.get("metadata", {}).get("pedagogy", {}).get("kind")
                for cell in payload["cells"]
            }
            self.assertTrue(
                {"quiz", "exercise", "reflection"} & kinds,
                f"{notebook}: expected quiz/exercise/reflection content",
            )


if __name__ == "__main__":
    unittest.main()
