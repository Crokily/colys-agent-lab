#!/usr/bin/env python3
"""Search local agent JSONL sessions and print resumable summaries."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
SKIP_ROLES = {"system", "developer", "tool", "toolresult", "tool_result", "bashexecution"}
SKIP_BLOCK_TYPES = {
    "thinking",
    "reasoning",
    "tool_use",
    "tooluse",
    "tool_call",
    "toolcall",
    "tool_result",
    "toolresult",
    "function_call",
    "function_call_output",
    "image",
    "input_image",
}
NOISE_PREFIXES = (
    "# AGENTS.md instructions",
    "<environment_context>",
    "<permissions instructions>",
    "<skills_instructions>",
    "<system-reminder>",
    "Base directory for this skill:",
    "You are Codex,",
    "You are Claude Code",
)


@dataclasses.dataclass
class TextChunk:
    role: str
    text: str
    ts: float | None = None


@dataclasses.dataclass
class SessionSummary:
    agent: str
    session_id: str
    path: Path
    cwd: str | None = None
    title: str | None = None
    first_ts: float | None = None
    last_ts: float | None = None
    chunks: list[TextChunk] = dataclasses.field(default_factory=list)
    search_parts: list[str] = dataclasses.field(default_factory=list)
    message_count: int = 0
    bytes_read: int = 0

    def update_time(self, ts: float | None) -> None:
        if ts is None:
            return
        if self.first_ts is None or ts < self.first_ts:
            self.first_ts = ts
        if self.last_ts is None or ts > self.last_ts:
            self.last_ts = ts

    def add_text(self, role: str, text: str, ts: float | None, max_chunk_chars: int, max_search_chars: int) -> None:
        text = clean_text(text)
        if not text or is_noise(role, text):
            return
        role = role or "message"
        if self.chunks and self.chunks[-1].role == role and self.chunks[-1].text == text:
            return
        self.message_count += 1
        self.update_time(ts)
        clipped = text if len(text) <= max_chunk_chars else text[:max_chunk_chars].rstrip() + " ..."
        if len(self.chunks) < 200:
            self.chunks.append(TextChunk(role=role, text=clipped, ts=ts))
        current = sum(len(part) for part in self.search_parts)
        if current < max_search_chars:
            self.search_parts.append(text[: max_search_chars - current])

    @property
    def sort_ts(self) -> float:
        return self.last_ts or self.first_ts or self.path.stat().st_mtime

    def matches(self, query: str | None) -> bool:
        if not query:
            return True
        haystack = "\n".join(self.search_parts).lower()
        query_l = query.lower().strip()
        if not query_l:
            return True
        if query_l in haystack:
            return True
        terms = [term for term in re.split(r"\s+", query_l) if term]
        return bool(terms) and all(term in haystack for term in terms)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search Claude/Codex/Pi JSONL session files, group by session, and print resume commands."
    )
    parser.add_argument("terms", nargs="*", help="Search terms. Omit to list recent sessions.")
    parser.add_argument("-q", "--query", help="Search query. Overrides positional terms.")
    parser.add_argument(
        "--agents",
        default="all",
        help="Comma-separated agents to include: all, claude, codex, pi, generic. Default: all.",
    )
    parser.add_argument("--root", action="append", default=[], help="Additional file or directory root to scan.")
    parser.add_argument(
        "--no-default-roots",
        action="store_true",
        help="Scan only --root paths instead of default Claude/Codex/Pi locations.",
    )
    parser.add_argument("--cwd", help="Only show sessions whose cwd contains this string.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum sessions to print. Default: 20.")
    parser.add_argument("--snippet-chars", type=int, default=260, help="Characters per snippet. Default: 260.")
    parser.add_argument("--snippets", type=int, default=3, help="Snippets per session. Default: 3.")
    parser.add_argument("--max-files", type=int, default=20000, help="Maximum JSONL files to scan. Default: 20000.")
    parser.add_argument("--max-file-mb", type=float, default=100.0, help="Skip files larger than this. Default: 100.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    query = args.query if args.query is not None else " ".join(args.terms).strip()
    query = query or None
    agents = parse_agent_filter(args.agents)

    files = discover_files(args, agents)
    sessions: dict[tuple[str, str, str], SessionSummary] = {}
    skipped = 0

    for path, hint in files:
        if len(sessions) > args.max_files * 4:
            break
        try:
            if path.stat().st_size > args.max_file_mb * 1024 * 1024:
                skipped += 1
                continue
        except OSError:
            skipped += 1
            continue
        for summary in parse_jsonl(path, hint, args):
            if summary.agent not in agents and "all" not in agents:
                continue
            key = (summary.agent, summary.session_id, str(summary.path))
            existing = sessions.get(key)
            if existing is None:
                sessions[key] = summary
            else:
                merge_summary(existing, summary)

    results = [
        item
        for item in sessions.values()
        if item.matches(query) and (not args.cwd or (item.cwd and args.cwd.lower() in item.cwd.lower()))
    ]
    results.sort(key=lambda item: item.sort_ts, reverse=True)
    results = results[: max(args.limit, 0)]

    if args.json:
        print_json(results, query, len(files), skipped, args)
    else:
        print_text(results, query, len(files), skipped, args)
    return 0


def parse_agent_filter(value: str) -> set[str]:
    agents = {part.strip().lower() for part in value.split(",") if part.strip()}
    valid = {"all", "claude", "codex", "pi", "generic"}
    unknown = agents - valid
    if unknown:
        raise SystemExit(f"Unknown agent(s): {', '.join(sorted(unknown))}")
    return agents or {"all"}


def discover_files(args: argparse.Namespace, agents: set[str]) -> list[tuple[Path, str | None]]:
    candidates: list[tuple[Path, str | None]] = []
    if not args.no_default_roots:
        home = Path.home()
        claude_root = Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")).expanduser()
        codex_root = Path(os.environ.get("CODEX_HOME", home / ".codex")).expanduser()
        pi_agent_root = Path(os.environ.get("PI_CODING_AGENT_DIR", home / ".pi" / "agent")).expanduser()
        pi_session_root = Path(os.environ.get("PI_CODING_AGENT_SESSION_DIR", pi_agent_root / "sessions")).expanduser()
        default_specs = [
            ("claude", claude_root / "projects"),
            ("claude", claude_root / "sessions"),
            ("claude", claude_root / "history.jsonl"),
            ("codex", codex_root / "sessions"),
            ("codex", codex_root / "history.jsonl"),
            ("codex", codex_root / "session_index.jsonl"),
            ("pi", pi_session_root),
            ("pi", home / ".pi" / "sessions"),
        ]
        for agent, root in default_specs:
            if "all" in agents or agent in agents:
                candidates.extend(expand_root(root, agent))
    for root in args.root:
        candidates.extend(expand_root(Path(root).expanduser(), None))

    seen: set[Path] = set()
    result: list[tuple[Path, str | None]] = []
    for path, hint in candidates:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append((path, hint))
        if len(result) >= args.max_files:
            break
    return result


def expand_root(root: Path, hint: str | None) -> list[tuple[Path, str | None]]:
    if not root.exists():
        return []
    if root.is_file():
        return [(root, hint)] if root.suffix == ".jsonl" else []
    files: list[tuple[Path, str | None]] = []
    for path in root.rglob("*.jsonl"):
        if path.is_file():
            files.append((path, hint))
    return files


def parse_jsonl(path: Path, hint: str | None, args: argparse.Namespace) -> list[SessionSummary]:
    summaries: dict[str, SessionSummary] = {}
    detected_agent = hint or agent_from_path(path) or "generic"
    fallback_id = id_from_path(path) or path.stem
    current_session_id: str | None = None

    try:
        raw_size = path.stat().st_size
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                detected_agent = hint or agent_from_object(obj) or detected_agent
                found_session_id = session_id_from_obj(detected_agent, obj)
                if found_session_id:
                    current_session_id = found_session_id
                session_id = found_session_id or current_session_id or fallback_id
                summary = summaries.get(session_id)
                if summary is None:
                    summary = SessionSummary(agent=detected_agent, session_id=session_id, path=path, bytes_read=raw_size)
                    summaries[session_id] = summary
                apply_metadata(summary, detected_agent, obj)
                for role, text, ts in extract_texts(detected_agent, obj):
                    summary.add_text(role, text, ts, max_chunk_chars=4000, max_search_chars=300000)
    except OSError:
        return []

    for summary in summaries.values():
        if summary.first_ts is None and summary.last_ts is None:
            try:
                summary.update_time(path.stat().st_mtime)
            except OSError:
                pass
        if not summary.cwd:
            summary.cwd = cwd_from_path(summary.agent, path)
    return list(summaries.values())


def agent_from_path(path: Path) -> str | None:
    raw = str(path).lower()
    if "/.claude/" in raw:
        return "claude"
    if "/.codex/" in raw:
        return "codex"
    if "/.pi/" in raw or "/pi/" in raw and "/sessions/" in raw:
        return "pi"
    return None


def agent_from_object(obj: dict[str, Any]) -> str | None:
    typ = obj.get("type")
    if typ in {"thread.started", "turn.started", "item.completed", "item.started", "session_meta", "event_msg", "response_item", "turn_context"}:
        return "codex"
    if typ == "session" and "version" in obj and "cwd" in obj:
        return "pi"
    if "sessionId" in obj and ("message" in obj or typ in {"custom-title", "agent-name", "summary", "user", "assistant"}):
        return "claude"
    return None


def id_from_path(path: Path) -> str | None:
    match = UUID_RE.search(path.name)
    if match:
        return match.group(0)
    return None


def session_id_from_obj(agent: str, obj: dict[str, Any]) -> str | None:
    for key in ("sessionId", "session_id", "thread_id"):
        value = obj.get(key)
        if isinstance(value, str) and value:
            return value
    payload = obj.get("payload")
    if isinstance(payload, dict):
        if obj.get("type") == "session_meta" and isinstance(payload.get("id"), str):
            return payload["id"]
        for key in ("session_id", "sessionId", "thread_id"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
    if agent == "pi" and obj.get("type") == "session" and isinstance(obj.get("id"), str):
        return obj["id"]
    return None


def apply_metadata(summary: SessionSummary, agent: str, obj: dict[str, Any]) -> None:
    ts = timestamp_from_obj(obj)
    summary.update_time(ts)
    cwd = cwd_from_obj(obj)
    if cwd:
        summary.cwd = cwd
    title = title_from_obj(agent, obj)
    if title:
        summary.title = title


def timestamp_from_obj(obj: dict[str, Any]) -> float | None:
    for key in ("timestamp", "ts", "created_at", "updated_at"):
        if key in obj:
            parsed = parse_timestamp(obj.get(key))
            if parsed is not None:
                return parsed
    payload = obj.get("payload")
    if isinstance(payload, dict):
        for key in ("timestamp", "started_at", "completed_at", "created_at"):
            if key in payload:
                parsed = parse_timestamp(payload.get(key))
                if parsed is not None:
                    return parsed
    message = obj.get("message")
    if isinstance(message, dict):
        parsed = parse_timestamp(message.get("timestamp"))
        if parsed is not None:
            return parsed
    return None


def parse_timestamp(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value > 10_000_000_000:
            return float(value) / 1000.0
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return parse_timestamp(int(text))
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            return datetime.fromisoformat(text).timestamp()
        except ValueError:
            return None
    return None


def cwd_from_obj(obj: dict[str, Any]) -> str | None:
    for key in ("cwd", "project", "working_directory", "workingDirectory"):
        value = obj.get(key)
        if isinstance(value, str) and value:
            return value
    payload = obj.get("payload")
    if isinstance(payload, dict):
        for key in ("cwd", "project", "working_directory", "workingDirectory"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def cwd_from_path(agent: str, path: Path) -> str | None:
    if agent != "pi":
        return None
    for part in path.parts:
        if part.startswith("--") and part.endswith("--") and len(part) > 4:
            inner = part[2:-2]
            if inner:
                return "/" + inner.replace("-", "/")
    return None


def title_from_obj(agent: str, obj: dict[str, Any]) -> str | None:
    if agent == "claude":
        for key in ("customTitle", "agentName"):
            value = obj.get(key)
            if isinstance(value, str) and value:
                return value
    for key in ("title", "name", "summary"):
        value = obj.get(key)
        if isinstance(value, str) and value:
            return clean_text(value)[:120]
    payload = obj.get("payload")
    if isinstance(payload, dict):
        for key in ("title", "name", "summary"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return clean_text(value)[:120]
    return None


def extract_texts(agent: str, obj: dict[str, Any]) -> Iterable[tuple[str, str, float | None]]:
    if agent == "claude":
        yield from extract_claude_texts(obj)
    elif agent == "codex":
        yield from extract_codex_texts(obj)
    elif agent == "pi":
        yield from extract_pi_texts(obj)
    else:
        yield from extract_generic_texts(obj)


def extract_claude_texts(obj: dict[str, Any]) -> Iterable[tuple[str, str, float | None]]:
    ts = timestamp_from_obj(obj)
    message = obj.get("message")
    if isinstance(message, dict):
        role = str(message.get("role") or obj.get("type") or "message")
        text = extract_content_text(message.get("content"))
        if text:
            yield role, text, ts
    typ = obj.get("type")
    if typ in {"queue-operation", "last-prompt"} and isinstance(obj.get("content"), str):
        yield "user", obj["content"], ts
    if isinstance(obj.get("display"), str):
        yield "user", obj["display"], ts
    if typ == "summary" and isinstance(obj.get("summary"), str):
        yield "summary", obj["summary"], ts


def extract_codex_texts(obj: dict[str, Any]) -> Iterable[tuple[str, str, float | None]]:
    ts = timestamp_from_obj(obj)
    typ = obj.get("type")
    if isinstance(obj.get("text"), str) and obj.get("session_id"):
        yield "user", obj["text"], ts
    if typ in {"response_item"}:
        payload = obj.get("payload")
        if isinstance(payload, dict) and payload.get("type") == "message":
            role = str(payload.get("role") or "message")
            text = extract_content_text(payload.get("content"))
            if text:
                yield role, text, ts
    if typ == "event_msg":
        payload = obj.get("payload")
        if isinstance(payload, dict):
            ptype = payload.get("type")
            if ptype == "user_message" and isinstance(payload.get("message"), str):
                yield "user", payload["message"], ts
            elif ptype == "agent_message" and isinstance(payload.get("message"), str):
                yield "assistant", payload["message"], ts
    if typ in {"item.completed", "item.started"}:
        item = obj.get("item")
        if isinstance(item, dict):
            item_type = item.get("type")
            if item_type == "agent_message" and isinstance(item.get("text"), str):
                yield "assistant", item["text"], ts
            elif item_type == "user_message" and isinstance(item.get("text"), str):
                yield "user", item["text"], ts
            elif item_type == "command_execution" and isinstance(item.get("command"), str):
                yield "command", "$ " + item["command"], ts


def extract_pi_texts(obj: dict[str, Any]) -> Iterable[tuple[str, str, float | None]]:
    ts = timestamp_from_obj(obj)
    typ = obj.get("type")
    if typ == "message":
        message = obj.get("message")
        if isinstance(message, dict):
            role = str(message.get("role") or "message")
            text = extract_content_text(message.get("content"))
            if text:
                yield role, text, ts
    if typ in {"compaction", "branch_summary"}:
        for key in ("summary", "content", "text"):
            value = obj.get(key)
            if isinstance(value, str) and value:
                yield "summary", value, ts


def extract_generic_texts(obj: dict[str, Any]) -> Iterable[tuple[str, str, float | None]]:
    ts = timestamp_from_obj(obj)
    role = str(obj.get("role") or obj.get("type") or "message")
    for key in ("text", "content", "message", "summary"):
        value = obj.get(key)
        if isinstance(value, dict) and "content" in value:
            role = str(value.get("role") or role)
            text = extract_content_text(value.get("content"))
        else:
            text = extract_content_text(value)
        if text:
            yield role, text, ts
            return


def extract_content_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [extract_content_text(item) for item in value]
        return "\n".join(part for part in parts if part)
    if isinstance(value, dict):
        block_type = str(value.get("type") or "").replace("-", "_").lower()
        if block_type in SKIP_BLOCK_TYPES:
            return ""
        for key in ("text", "input_text", "output_text", "message", "content"):
            if key in value:
                return extract_content_text(value.get(key))
        return ""
    return ""


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_noise(role: str, text: str) -> bool:
    role_key = role.replace("-", "_").lower()
    if role_key in SKIP_ROLES:
        return True
    if any(text.startswith(prefix) for prefix in NOISE_PREFIXES):
        return True
    if len(text) > 2000 and (
        "aggregated_output" in text
        or "base_instructions" in text
        or "tool_use_id" in text
        or "hook_success" in text
    ):
        return True
    return False


def merge_summary(target: SessionSummary, source: SessionSummary) -> None:
    target.cwd = target.cwd or source.cwd
    target.title = target.title or source.title
    target.update_time(source.first_ts)
    target.update_time(source.last_ts)
    target.message_count += source.message_count
    target.bytes_read += source.bytes_read
    target.chunks.extend(source.chunks[: max(0, 200 - len(target.chunks))])
    current = sum(len(part) for part in target.search_parts)
    for part in source.search_parts:
        if current >= 300000:
            break
        target.search_parts.append(part[: 300000 - current])
        current += len(part)


def print_text(results: list[SessionSummary], query: str | None, scanned: int, skipped: int, args: argparse.Namespace) -> None:
    label = f' matching "{query}"' if query else ""
    print(f"Found {len(results)} session(s){label}. Scanned {scanned} file(s), skipped {skipped}.")
    for index, session in enumerate(results, 1):
        print()
        print(f"{index}. [{session.agent}] {format_ts(session.sort_ts)}")
        if session.title:
            print(f"   title: {session.title}")
        print(f"   id: {session.session_id}")
        print(f"   cwd: {session.cwd or '-'}")
        print(f"   file: {display_path(session.path)}")
        print(f"   messages: {session.message_count}")
        print(f"   resume: {resume_command(session)}")
        snippets = select_snippets(session, query, args.snippets, args.snippet_chars)
        if snippets:
            print("   snippets:")
            for role, snippet in snippets:
                print(f"   - {role}: {snippet}")


def print_json(results: list[SessionSummary], query: str | None, scanned: int, skipped: int, args: argparse.Namespace) -> None:
    payload = {
        "query": query,
        "scanned_files": scanned,
        "skipped_files": skipped,
        "results": [
            {
                "agent": item.agent,
                "session_id": item.session_id,
                "time": format_ts(item.sort_ts),
                "cwd": item.cwd,
                "title": item.title,
                "file": str(item.path),
                "message_count": item.message_count,
                "resume": resume_command(item),
                "snippets": [
                    {"role": role, "text": text}
                    for role, text in select_snippets(item, query, args.snippets, args.snippet_chars)
                ],
            }
            for item in results
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def select_snippets(session: SessionSummary, query: str | None, count: int, width: int) -> list[tuple[str, str]]:
    if count <= 0:
        return []
    chunks = session.chunks
    selected: list[TextChunk] = []
    if query:
        query_l = query.lower()
        terms = [term for term in re.split(r"\s+", query_l) if term]
        for chunk in chunks:
            text_l = chunk.text.lower()
            if query_l in text_l or any(term in text_l for term in terms):
                selected.append(chunk)
                if len(selected) >= count:
                    break
    if not selected:
        selected = chunks[: max(count - 1, 0)]
        if chunks and chunks[-1] not in selected:
            selected.append(chunks[-1])
    return [(chunk.role, make_snippet(chunk.text, query, width)) for chunk in selected[:count]]


def make_snippet(text: str, query: str | None, width: int) -> str:
    text = clean_text(text)
    if len(text) <= width:
        return text
    pos = -1
    if query:
        text_l = text.lower()
        query_l = query.lower()
        pos = text_l.find(query_l)
        if pos < 0:
            for term in re.split(r"\s+", query_l):
                if term:
                    pos = text_l.find(term)
                    if pos >= 0:
                        break
    if pos < 0:
        return text[:width].rstrip() + " ..."
    start = max(0, pos - width // 3)
    end = min(len(text), start + width)
    prefix = "... " if start else ""
    suffix = " ..." if end < len(text) else ""
    return prefix + text[start:end].strip() + suffix


def resume_command(session: SessionSummary) -> str:
    sid = shlex.quote(session.session_id)
    if session.agent == "claude":
        base = f"claude --resume {sid}" if session.session_id else "claude --resume"
        return with_cwd(session.cwd, base)
    if session.agent == "codex":
        base = f"codex resume {sid}" if session.session_id else "codex resume"
        return with_cwd(session.cwd, base)
    if session.agent == "pi":
        target = shlex.quote(str(session.path))
        base = f"pi --session {target}"
        return with_cwd(session.cwd, base)
    return f"# No known resume command; inspect {shlex.quote(str(session.path))}"


def with_cwd(cwd: str | None, command: str) -> str:
    if not cwd:
        return command
    return f"cd {shlex.quote(cwd)} && {command}"


def display_path(path: Path) -> str:
    try:
        home = Path.home()
        return str(path).replace(str(home), "~", 1) if path.is_relative_to(home) else str(path)
    except AttributeError:
        text = str(path)
        home_text = str(Path.home())
        return text.replace(home_text, "~", 1) if text.startswith(home_text) else text


def format_ts(ts: float | None) -> str:
    if ts is None:
        return "-"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1)
