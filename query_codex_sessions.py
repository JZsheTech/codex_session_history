#!/usr/bin/env python3
"""
Query Codex session jsonl file paths by workspace directory and date/date range.

Examples:
  python query_codex_sessions.py \
    --workspace-dir /Users/bytedance/codebase_jz/worktree_exp_codex/1stphorm.com \
    --year 2026 --month 2 --day 5

  python query_codex_sessions.py \
    --workspace-dir /path/to/project \
    --start-date 2026-02-01 --end-date 2026-02-05
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Locate Codex session files by workspace directory and date."
    )
    parser.add_argument(
        "--workspace-dir",
        required=True,
        help="Workspace directory to match against session_meta.payload.cwd",
    )
    parser.add_argument(
        "--sessions-root",
        default=str(Path.home() / ".codex" / "sessions"),
        help="Codex sessions root directory (default: ~/.codex/sessions)",
    )

    # Single-day mode
    parser.add_argument("--year", type=int, help="Year, e.g. 2026")
    parser.add_argument("--month", type=int, help="Month, 1-12")
    parser.add_argument("--day", type=int, help="Day, 1-31")

    # Range mode
    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format (optional alternative to --year/--month/--day)",
    )
    parser.add_argument(
        "--end-date",
        help="End date in YYYY-MM-DD format (defaults to start date if omitted)",
    )

    return parser.parse_args()


def normalize_path(path_str: str) -> str:
    # resolve() with strict=False handles non-existing paths and normalizes symlinks when possible.
    return str(Path(path_str).expanduser().resolve(strict=False))


def parse_iso_datetime(value: str) -> datetime:
    # Codex example: 2026-02-04T08:25:09.350Z
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def parse_date_input(args: argparse.Namespace) -> tuple[date, date]:
    has_ymd = all(v is not None for v in (args.year, args.month, args.day))
    has_range = args.start_date is not None

    if has_ymd and has_range:
        raise ValueError("Use either --year/--month/--day or --start-date/--end-date, not both.")
    if not has_ymd and not has_range:
        raise ValueError("Provide date using --year/--month/--day or --start-date.")

    if has_ymd:
        start = date(args.year, args.month, args.day)
        return start, start

    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date) if args.end_date else start
    if end < start:
        raise ValueError("--end-date must be greater than or equal to --start-date.")
    return start, end


def date_range(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def first_line_json(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            line = f.readline().strip()
        if not line:
            return None
        return json.loads(line)
    except (OSError, json.JSONDecodeError):
        return None


def matches_session(meta: dict, workspace_dir: str, start: date, end: date) -> bool:
    payload = meta.get("payload", {})
    cwd = payload.get("cwd")
    if not isinstance(cwd, str):
        return False

    meta_workspace = normalize_path(cwd)
    if meta_workspace != workspace_dir:
        return False

    timestamp = meta.get("timestamp")
    if not isinstance(timestamp, str):
        timestamp = payload.get("timestamp")
    if not isinstance(timestamp, str):
        return False

    try:
        session_date = parse_iso_datetime(timestamp).date()
    except ValueError:
        return False

    return start <= session_date <= end


def find_sessions(
    sessions_root: Path, workspace_dir: str, start: date, end: date
) -> list[str]:
    results: list[str] = []
    normalized_workspace = normalize_path(workspace_dir)

    for d in date_range(start, end):
        day_dir = sessions_root / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}"
        if not day_dir.is_dir():
            continue

        for jsonl_file in sorted(day_dir.glob("*.jsonl")):
            meta = first_line_json(jsonl_file)
            if not isinstance(meta, dict):
                continue
            if matches_session(meta, normalized_workspace, start, end):
                results.append(str(jsonl_file))

    return results


def main() -> None:
    args = parse_args()
    try:
        start, end = parse_date_input(args)
    except ValueError as err:
        raise SystemExit(f"Argument error: {err}") from err

    sessions_root = Path(args.sessions_root).expanduser().resolve(strict=False)
    paths = find_sessions(sessions_root, args.workspace_dir, start, end)

    # Output exactly as requested: list[session_path]
    print(json.dumps(paths, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
