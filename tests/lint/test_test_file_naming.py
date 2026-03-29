import unittest
from pathlib import Path


class TestTestFileNaming(unittest.TestCase):
    def test_all_python_files_use_test_prefix(self):
        tests_root = Path(__file__).resolve().parents[1]
        invalid_files = []

        for path in tests_root.rglob("*.py"):
            if path.name == "__init__.py":
                continue

            if not path.name.startswith("test_"):
                invalid_files.append(path.relative_to(tests_root).as_posix())

        self.assertFalse(
            invalid_files,
            "The following Python files do not start with 'test_':\n"
            + "\n".join(f"- {path}" for path in invalid_files),
        )


if __name__ == "__main__":
    unittest.main()
