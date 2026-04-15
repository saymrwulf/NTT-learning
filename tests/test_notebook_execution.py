from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

from ntt_learning.course import REPO_ROOT, TECHNICAL_NOTEBOOKS

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def read_notebook(relative_path: Path) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def code_sources(relative_path: Path) -> list[str]:
    payload = read_notebook(relative_path)
    sources: list[str] = []
    for cell in payload["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        if isinstance(source, list):
            sources.append("".join(source))
        else:
            sources.append(str(source))
    return sources


class NotebookExecutionTests(unittest.TestCase):
    def test_technical_notebooks_execute_as_plain_python(self) -> None:
        for notebook in TECHNICAL_NOTEBOOKS:
            namespace = {"__name__": "__main__"}
            sources = code_sources(notebook)
            self.assertTrue(sources, f"{notebook}: expected at least one code cell")
            with self.subTest(notebook=notebook.as_posix()):
                with contextlib.redirect_stdout(io.StringIO()):
                    for index, source in enumerate(sources):
                        code_object = compile(
                            source,
                            filename=f"{notebook.as_posix()}::cell-{index}",
                            mode="exec",
                        )
                        exec(code_object, namespace, namespace)


if __name__ == "__main__":
    unittest.main()

