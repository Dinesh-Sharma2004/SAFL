from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

REQUIRED_COLUMNS = {"state", "headline", "date", "source_name", "source_url", "activity_type"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate notebook candidate CSV and copy it into the dashboard data folder.")
    parser.add_argument("--input", required=True, help="Candidate CSV emitted by the notebook")
    parser.add_argument("--output", required=True, help="Dashboard CSV destination")
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    destination = Path(args.output).expanduser().resolve()

    if not source.is_file():
        print(f"ERROR: notebook output CSV does not exist: {source}", file=sys.stderr)
        return 2

    try:
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = set(reader.fieldnames or [])
            missing = sorted(REQUIRED_COLUMNS - headers)
            if missing:
                print("ERROR: CSV is missing required columns: " + ", ".join(missing), file=sys.stderr)
                print("Found columns: " + ", ".join(reader.fieldnames or []), file=sys.stderr)
                return 3
            records = [row for row in reader if any(str(value or "").strip() for value in row.values())]
    except (OSError, UnicodeError, csv.Error) as exc:
        print(f"ERROR: cannot read candidate CSV: {exc}", file=sys.stderr)
        return 4

    if not records:
        print("ERROR: candidate CSV contains no data records. Dashboard data was not overwritten.", file=sys.stderr)
        return 5

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"Validated {len(records):,} candidate records.")
    print(f"Notebook CSV: {source}")
    print(f"Dashboard CSV: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
