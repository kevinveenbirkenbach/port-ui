#!/usr/bin/env python3
"""
main.py - Proxy to Makefile targets for managing the Portfolio CMS Docker application.
Automatically generates CLI commands based on the Makefile definitions.
"""
import argparse
import subprocess
import sys
import re
from pathlib import Path

MAKEFILE_PATH = Path(__file__).resolve().parent / "Makefile"


def load_targets(makefile_path):
    """
    Parse the Makefile to extract targets and their help comments.
    Assumes each target is defined as 'name:' and the following line that starts
    with '\t#' provides its help text.
    """
    targets = []
    pattern = re.compile(r"^([A-Za-z0-9_\-]+):")
    with open(makefile_path, 'r') as f:
        lines = f.readlines()
    for idx, line in enumerate(lines):
        m = pattern.match(line)
        if m:
            name = m.group(1)
            help_text = ''
            # look for next non-empty line
            if idx + 1 < len(lines) and lines[idx+1].lstrip().startswith('#'):
                help_text = lines[idx+1].lstrip('# ').strip()
            targets.append((name, help_text))
    return targets


def run_command(command, dry_run=False):
    """Utility to run shell commands."""
    print(f"Executing: {' '.join(command)}")
    if dry_run:
        print("Dry run enabled: command not executed.")
        return
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="CLI proxy to Makefile targets for Portfolio CMS Docker app"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated Make command without executing it."
    )

    subparsers = parser.add_subparsers(
        title="Available commands",
        dest="command",
        required=True
    )

    targets = load_targets(MAKEFILE_PATH)
    for name, help_text in targets:
        sp = subparsers.add_parser(name, help=help_text)
        sp.set_defaults(target=name)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd = ["make", args.target]
    run_command(cmd, dry_run=args.dry_run)


if __name__ == "__main__":
    from pathlib import Path
    main()