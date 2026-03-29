#!/usr/bin/env python3
"""Print runtime dependencies from pyproject.toml, one per line."""

import sys
import tomllib
from pathlib import Path

DEFAULT_PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"


def load_runtime_requirements(
    pyproject_path: Path = DEFAULT_PYPROJECT_PATH,
) -> list[str]:
    with pyproject_path.open("rb") as handle:
        pyproject = tomllib.load(handle)
    return list(pyproject["project"]["dependencies"])


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    pyproject_path = Path(args[0]) if args else DEFAULT_PYPROJECT_PATH

    for requirement in load_runtime_requirements(pyproject_path):
        print(requirement)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
