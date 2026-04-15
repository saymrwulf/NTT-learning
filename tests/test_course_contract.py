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
                    self.assertTrue(source.startswith(f"## {role.upper()}"), f"{notebook}: missing visible label")
                if cell["cell_type"] == "code":
                    self.assertTrue(source.startswith(f"# {role.upper()}"), f"{notebook}: missing visible label")

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

