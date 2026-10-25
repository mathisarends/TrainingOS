"""Run the same checks locally and in CI."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {
    "lint": [["ruff", "check", "."], ["ruff", "format", "--check", "."]],
    "types": [["mypy", "backend/src"]],
    "test": [["pytest", *sys.argv[2:]]],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=["all", *CHECKS], default="all", nargs="?")
    args, _ = parser.parse_known_args()
    checks = list(CHECKS) if args.check == "all" else [args.check]
    for name in checks:
        for command in CHECKS[name]:
            result = subprocess.run([sys.executable, "-m", *command], cwd=ROOT, check=False)
            if result.returncode:
                raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
