#!/usr/bin/env python3
import ast
import unittest
from pathlib import Path


class TestTestFilesContainUnittestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.tests_dir = self.repo_root / "tests"
        self.assertTrue(
            self.tests_dir.is_dir(),
            f"'tests' directory not found at: {self.tests_dir}",
        )

    def _iter_test_files(self) -> list[Path]:
        return sorted(self.tests_dir.rglob("test_*.py"))

    def _file_contains_runnable_unittest_test(self, path: Path) -> bool:
        source = path.read_text(encoding="utf-8")

        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            raise AssertionError(f"SyntaxError in {path}: {error}") from error

        testcase_aliases = {"TestCase"}
        unittest_aliases = {"unittest"}

        for node in tree.body:
            if isinstance(node, ast.Import):
                for import_name in node.names:
                    if import_name.name == "unittest":
                        unittest_aliases.add(import_name.asname or "unittest")
            elif isinstance(node, ast.ImportFrom) and node.module == "unittest":
                for import_name in node.names:
                    if import_name.name == "TestCase":
                        testcase_aliases.add(import_name.asname or "TestCase")

        def is_testcase_base(base: ast.expr) -> bool:
            if isinstance(base, ast.Name) and base.id in testcase_aliases:
                return True

            if isinstance(base, ast.Attribute) and base.attr == "TestCase":
                return (
                    isinstance(base.value, ast.Name)
                    and base.value.id in unittest_aliases
                )

            return False

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                node.name.startswith("test_")
            ):
                return True

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue

            if not any(is_testcase_base(base) for base in node.bases):
                continue

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    item.name.startswith("test_")
                ):
                    return True

        return False

    def test_all_test_py_files_contain_runnable_tests(self) -> None:
        test_files = self._iter_test_files()
        self.assertTrue(test_files, "No test_*.py files found under tests/")

        offenders = []
        for path in test_files:
            if not self._file_contains_runnable_unittest_test(path):
                offenders.append(path.relative_to(self.repo_root).as_posix())

        self.assertFalse(
            offenders,
            "These test_*.py files do not define any unittest-runnable tests:\n"
            + "\n".join(f"- {path}" for path in offenders),
        )


if __name__ == "__main__":
    unittest.main()
