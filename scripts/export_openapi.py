"""Export the backend's public contract for the Lit Canon client generator."""

import argparse
import json
from pathlib import Path

from backend.app import create_app

OUTPUT = Path(__file__).resolve().parents[1] / "frontend" / "openapi.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without writing files")
    args = parser.parse_args()
    schema = create_app().openapi()
    if args.check:
        if not OUTPUT.exists() or json.loads(OUTPUT.read_text(encoding="utf-8")) != schema:
            raise SystemExit("Frontend OpenAPI is stale. Run scripts/export_openapi.py.")
        print("Frontend OpenAPI matches the backend.")
        return
    OUTPUT.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {OUTPUT}")


if __name__ == "__main__":
    main()
