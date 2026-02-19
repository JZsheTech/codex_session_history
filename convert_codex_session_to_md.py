#!/usr/bin/env python3
"""
Convert Codex session jsonl files into readable markdown execution traces.

Features:
1) concise mode: truncate long message blocks by threshold.
2) full mode: output complete content for every record.

Examples:
  # single file
  python convert_codex_session_to_md.py \
    /Users/bytedance/.codex/sessions/2026/02/04/rollout-2026-02-04T17-12-00-019c27ec-40f1-7092-8175-bc4a8af45ab1.jsonl \
    --truncate-threshold  3000  --truncate-keep 2000  \
    --mode concise --output-dir ./session_traces

  # batch directories
  python convert_codex_session_to_md.py \
    /Users/bytedance/.codex/sessions/2026/02/19/ \
    --truncate-threshold  3000  --truncate-keep 2000  \
    --mode concise --output-dir ./batch_session_traces
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Block:
    label: str
    text: str
    language: str = "text"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Codex session jsonl files to markdown traces."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input jsonl file(s) and/or directory path(s) that contain jsonl files.",
    )
    parser.add_argument(
        "--mode",
        choices=["concise", "full"],
        default="concise",
        help="concise: truncate long blocks; full: output full content.",
    )
    parser.add_argument(
        "--truncate-threshold",
        type=int,
        default=2000,
        help="Concise mode only: truncate when block length is greater than this value.",
    )
    parser.add_argument(
        "--truncate-keep",
        type=int,
        default=800,
        help="Concise mode only: number of leading characters to keep after truncation.",
    )
    parser.add_argument(
        "--output-dir",
        default="session_markdown_traces",
        help="Directory to write markdown files.",
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Optional output markdown path. Only valid when exactly one input jsonl file is provided.",
    )
    return parser.parse_args()


def truncate_text(text: str, mode: str, threshold: int, keep: int) -> str:
    if mode != "concise":
        return text
    if len(text) <= threshold:
        return text
    keep = max(0, min(keep, len(text)))
    suffix = f"\n\n[TRUNCATED: original_length={len(text)}, shown={keep}]"
    return text[:keep] + suffix


def to_pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return to_pretty_json(value)
    return str(value)


def maybe_parse_json_string(value: Any) -> Any | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped:
        return None
    if stripped[0] not in "{[":
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def format_code_block(text: str, language: str) -> list[str]:
    fence = "```"
    if "```" in text:
        fence = "~~~~"
    return [f"{fence}{language}", text, fence]


def extract_message_blocks(content: Any) -> list[Block]:
    blocks: list[Block] = []
    if not isinstance(content, list):
        return blocks
    for idx, item in enumerate(content, start=1):
        if not isinstance(item, dict):
            blocks.append(Block(label=f"content[{idx}]", text=to_text(item)))
            continue
        ctype = item.get("type", "unknown")
        text = item.get("text")
        if text is None:
            text = to_pretty_json(item)
        blocks.append(Block(label=f"content[{idx}] ({ctype})", text=to_text(text)))
    return blocks


def summarize_record(record: dict[str, Any]) -> tuple[str, list[tuple[str, str]], list[Block]]:
    line_type = to_text(record.get("type", "unknown"))
    payload = record.get("payload")
    if not isinstance(payload, dict):
        meta = [("line_type", line_type)]
        blocks = [Block(label="record", text=to_pretty_json(record), language="json")]
        return line_type, meta, blocks

    if line_type == "session_meta":
        p = payload
        meta = [
            ("line_type", line_type),
            ("session_id", to_text(p.get("id"))),
            ("cwd", to_text(p.get("cwd"))),
            ("originator", to_text(p.get("originator"))),
            ("source", to_text(p.get("source"))),
            ("cli_version", to_text(p.get("cli_version"))),
            ("model_provider", to_text(p.get("model_provider"))),
        ]
        blocks: list[Block] = []
        base_text = (((p.get("base_instructions") or {}).get("text")) if isinstance(p.get("base_instructions"), dict) else None)
        if base_text:
            blocks.append(Block("base_instructions.text", to_text(base_text)))
        git_info = p.get("git")
        if git_info is not None:
            blocks.append(Block("git", to_pretty_json(git_info), language="json"))
        return "session_meta", meta, blocks

    if line_type == "turn_context":
        p = payload
        meta = [
            ("line_type", line_type),
            ("turn_id", to_text(p.get("turn_id"))),
            ("cwd", to_text(p.get("cwd"))),
            ("model", to_text(p.get("model"))),
            ("approval_policy", to_text(p.get("approval_policy"))),
            ("effort", to_text(p.get("effort"))),
            ("summary", to_text(p.get("summary"))),
        ]
        blocks = []
        if p.get("sandbox_policy") is not None:
            blocks.append(Block("sandbox_policy", to_pretty_json(p.get("sandbox_policy")), language="json"))
        if p.get("collaboration_mode") is not None:
            blocks.append(Block("collaboration_mode", to_pretty_json(p.get("collaboration_mode")), language="json"))
        if p.get("user_instructions"):
            blocks.append(Block("user_instructions", to_text(p.get("user_instructions"))))
        if p.get("developer_instructions"):
            blocks.append(Block("developer_instructions", to_text(p.get("developer_instructions"))))
        return "turn_context", meta, blocks

    if line_type == "event_msg":
        p = payload
        event_type = to_text(p.get("type", "unknown"))
        title = f"event_msg.{event_type}"
        meta: list[tuple[str, str]] = [("line_type", line_type), ("event_type", event_type)]
        blocks: list[Block] = []

        if event_type == "user_message":
            meta.extend(
                [
                    ("images_count", str(len(p.get("images") or []))),
                    ("local_images_count", str(len(p.get("local_images") or []))),
                ]
            )
            blocks.append(Block("message", to_text(p.get("message"))))
        elif event_type == "agent_message":
            blocks.append(Block("message", to_text(p.get("message"))))
        elif event_type == "agent_reasoning":
            blocks.append(Block("text", to_text(p.get("text"))))
        elif event_type == "token_count":
            info = p.get("info")
            if info is not None:
                blocks.append(Block("info", to_pretty_json(info), language="json"))
            if p.get("rate_limits") is not None:
                blocks.append(Block("rate_limits", to_pretty_json(p.get("rate_limits")), language="json"))
        else:
            blocks.append(Block("payload", to_pretty_json(p), language="json"))

        return title, meta, blocks

    if line_type == "response_item":
        p = payload
        item_type = to_text(p.get("type", "unknown"))
        meta: list[tuple[str, str]] = [("line_type", line_type), ("item_type", item_type)]
        blocks: list[Block] = []
        title = f"response_item.{item_type}"

        if item_type == "message":
            role = to_text(p.get("role", "unknown"))
            phase = to_text(p.get("phase"))
            title = f"response_item.message.{role}"
            meta.append(("role", role))
            if phase:
                meta.append(("phase", phase))
            blocks.extend(extract_message_blocks(p.get("content")))
            return title, meta, blocks

        if item_type == "reasoning":
            summary = p.get("summary")
            if isinstance(summary, list) and summary:
                blocks.extend(extract_message_blocks(summary))
            if p.get("content") is not None:
                blocks.append(Block("content", to_text(p.get("content"))))
            if p.get("encrypted_content") is not None:
                blocks.append(Block("encrypted_content", to_text(p.get("encrypted_content"))))
            return title, meta, blocks

        if item_type in {"function_call", "custom_tool_call"}:
            name = to_text(p.get("name", "unknown_tool"))
            call_id = to_text(p.get("call_id"))
            status = to_text(p.get("status"))
            meta.extend([("name", name), ("call_id", call_id)])
            if status:
                meta.append(("status", status))
            title = f"response_item.{item_type}.{name}"
            arg_field = "arguments" if item_type == "function_call" else "input"
            raw_args = p.get(arg_field)
            parsed = maybe_parse_json_string(raw_args)
            if parsed is not None:
                blocks.append(Block(arg_field, to_pretty_json(parsed), language="json"))
            else:
                blocks.append(Block(arg_field, to_text(raw_args)))
            return title, meta, blocks

        if item_type in {"function_call_output", "custom_tool_call_output"}:
            call_id = to_text(p.get("call_id"))
            meta.append(("call_id", call_id))
            raw_output = p.get("output")
            parsed_output = maybe_parse_json_string(raw_output)
            if parsed_output is not None:
                blocks.append(Block("output", to_pretty_json(parsed_output), language="json"))
            else:
                blocks.append(Block("output", to_text(raw_output)))
            return title, meta, blocks

        if item_type == "web_search_call":
            status = to_text(p.get("status"))
            action = p.get("action")
            meta.append(("status", status))
            action_type = to_text(action.get("type")) if isinstance(action, dict) else ""
            if action_type:
                meta.append(("action_type", action_type))
                title = f"response_item.web_search_call.{action_type}"
            blocks.append(Block("action", to_pretty_json(action), language="json"))
            return title, meta, blocks

        blocks.append(Block("payload", to_pretty_json(p), language="json"))
        return title, meta, blocks

    meta = [("line_type", line_type)]
    blocks = [Block("record", to_pretty_json(record), language="json")]
    return line_type, meta, blocks


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            if not line.strip():
                yield line_number, {
                    "type": "empty_line",
                    "payload": {"raw_line": ""},
                }
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as err:
                yield line_number, {
                    "type": "parse_error",
                    "payload": {
                        "error": str(err),
                        "raw_line": line,
                    },
                }
                continue
            if not isinstance(obj, dict):
                yield line_number, {
                    "type": "non_object_line",
                    "payload": {"value": obj},
                }
                continue
            yield line_number, obj


def normalize_input_files(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in inputs:
        p = Path(item).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"Input path does not exist: {p}")
        if p.is_file():
            if p.suffix.lower() == ".jsonl":
                files.append(p.resolve(strict=False))
            continue
        for candidate in sorted(p.glob("*.jsonl")):
            if candidate.is_file():
                files.append(candidate.resolve(strict=False))
    unique_files: list[Path] = []
    seen: set[str] = set()
    for f in files:
        key = str(f)
        if key in seen:
            continue
        seen.add(key)
        unique_files.append(f)
    return unique_files


def safe_output_path(output_dir: Path, session_file: Path, mode: str) -> Path:
    base_name = f"{session_file.stem}.{mode}.md"
    out_path = output_dir / base_name
    if not out_path.exists():
        return out_path
    idx = 2
    while True:
        candidate = output_dir / f"{session_file.stem}.{mode}.{idx}.md"
        if not candidate.exists():
            return candidate
        idx += 1


def render_session_markdown(
    session_file: Path,
    mode: str,
    truncate_threshold: int,
    truncate_keep: int,
) -> str:
    records = list(iter_jsonl(session_file))
    now = datetime.now().isoformat(timespec="seconds")
    lines: list[str] = []

    lines.append(f"# Codex Session Trace: `{session_file.name}`")
    lines.append("")
    lines.append(f"- source_file: `{session_file}`")
    lines.append(f"- generated_at: `{now}`")
    lines.append(f"- mode: `{mode}`")
    if mode == "concise":
        lines.append(f"- truncate_threshold: `{truncate_threshold}`")
        lines.append(f"- truncate_keep: `{truncate_keep}`")
    lines.append(f"- total_records: `{len(records)}`")
    lines.append("")

    for idx, (line_number, record) in enumerate(records, start=1):
        title, meta, blocks = summarize_record(record)
        top_timestamp = to_text(record.get("timestamp"))

        lines.append(f"## {idx:04d}. `{title}`")
        lines.append("")
        lines.append(f"- jsonl_line: `{line_number}`")
        if top_timestamp:
            lines.append(f"- timestamp: `{top_timestamp}`")
        for k, v in meta:
            if not v:
                continue
            rendered_v = truncate_text(to_text(v), mode, truncate_threshold, truncate_keep)
            lines.append(f"- {k}: `{rendered_v}`")
        lines.append("")

        for block in blocks:
            rendered_text = truncate_text(
                to_text(block.text), mode, truncate_threshold, truncate_keep
            )
            lines.append(f"**{block.label}**")
            lines.append("")
            lines.extend(format_code_block(rendered_text, block.language))
            lines.append("")

        if mode == "full":
            lines.append("**raw_record_json**")
            lines.append("")
            lines.extend(format_code_block(to_pretty_json(record), "json"))
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if args.truncate_threshold < 1:
        raise SystemExit("--truncate-threshold must be >= 1")
    if args.truncate_keep < 1:
        raise SystemExit("--truncate-keep must be >= 1")
    if args.truncate_keep > args.truncate_threshold:
        raise SystemExit("--truncate-keep must be <= --truncate-threshold")

    input_files = normalize_input_files(args.inputs)
    if not input_files:
        raise SystemExit("No jsonl files found from inputs.")

    if args.output_file:
        if len(input_files) != 1:
            raise SystemExit("--output-file can only be used when there is exactly one input jsonl file.")
        output_path = Path(args.output_file).expanduser()
        markdown = render_session_markdown(
            input_files[0],
            mode=args.mode,
            truncate_threshold=args.truncate_threshold,
            truncate_keep=args.truncate_keep,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(json.dumps([str(output_path)], ensure_ascii=False, indent=2))
        return

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[str] = []
    for session_file in input_files:
        markdown = render_session_markdown(
            session_file,
            mode=args.mode,
            truncate_threshold=args.truncate_threshold,
            truncate_keep=args.truncate_keep,
        )
        out_path = safe_output_path(output_dir, session_file, args.mode)
        out_path.write_text(markdown, encoding="utf-8")
        generated.append(str(out_path))

    print(json.dumps(generated, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
