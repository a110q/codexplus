from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from codex_session_delete.models import ExportResult, ExportStatus, SessionRef


_WINDOWS_FILENAME_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WHITESPACE_RE = re.compile(r"\s+")


class MarkdownExportService:
    def __init__(self, db_path: Path | None):
        self.db_path = db_path

    def export(self, session: SessionRef) -> ExportResult:
        if self.db_path is None:
            return self._failed(session.session_id, "未配置本地 Codex 数据库")
        if not self.db_path.exists():
            return self._failed(session.session_id, f"数据库不存在：{self.db_path}")

        thread_id = self._normalize_session_id(session.session_id)
        try:
            with sqlite3.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                if not self._supports_codex_threads(db):
                    return self._failed(thread_id, "不支持当前本地存储结构")
                row = db.execute("SELECT id, title, rollout_path FROM threads WHERE id = ?", (thread_id,)).fetchone()
        except sqlite3.Error as exc:
            return self._failed(thread_id, f"读取本地数据库失败：{exc}")

        if row is None:
            return self._failed(thread_id, "未找到对应会话")

        title = self._display_title(str(row["title"] or session.title or ""))
        rollout_path_value = str(row["rollout_path"] or "")
        if not rollout_path_value:
            return self._failed(thread_id, "会话缺少 rollout 文件路径")
        rollout_path = Path(rollout_path_value)
        if not rollout_path.is_file():
            return self._failed(thread_id, f"rollout 文件不存在：{rollout_path}")

        try:
            messages = self._load_messages(rollout_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return self._failed(thread_id, f"读取 rollout 失败：{exc}")

        if not messages:
            return self._failed(thread_id, "未找到可导出的用户或助手消息")

        filename = self._build_filename(title, thread_id)
        markdown = self._render_markdown(title, messages)
        return ExportResult(
            status=ExportStatus.EXPORTED,
            session_id=thread_id,
            message=f"已导出为 Markdown：{filename}",
            filename=filename,
            markdown=markdown,
        )

    def _supports_codex_threads(self, db: sqlite3.Connection) -> bool:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "threads" not in tables:
            return False
        columns = {row[1] for row in db.execute('PRAGMA table_info("threads")')}
        return {"id", "title", "rollout_path"}.issubset(columns)

    def _load_messages(self, rollout_path: Path) -> list[tuple[str, str | None, str]]:
        messages: list[tuple[str, str | None, str]] = []
        with rollout_path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                if not raw_line.strip():
                    continue
                event = json.loads(raw_line)
                if event.get("type") != "response_item":
                    continue
                payload = event.get("payload")
                if not isinstance(payload, dict):
                    continue
                if payload.get("type") != "message":
                    continue
                role = payload.get("role")
                if role not in {"user", "assistant"}:
                    continue
                body = self._serialize_message_content(payload.get("content"))
                if not body:
                    continue
                speaker = "User" if role == "user" else "Assistant"
                messages.append((speaker, self._format_timestamp(event.get("timestamp")), body))
        return messages

    def _serialize_message_content(self, content: object) -> str:
        if not isinstance(content, list):
            return ""
        blocks: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type in {"input_text", "output_text"}:
                text = self._normalize_newlines(str(block.get("text") or "")).strip("\n")
                if text.strip():
                    blocks.append(text)
                continue
            if block_type == "input_image":
                image_url = str(block.get("image_url") or "").strip()
                if image_url and not image_url.startswith("data:"):
                    blocks.append(f"> Image attachment\n[Image link](<{image_url}>)")
                else:
                    blocks.append("> Image attachment")
        return "\n\n".join(block for block in blocks if block.strip()).strip()

    def _format_timestamp(self, value: object) -> str | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return timestamp.astimezone().strftime("%Y-%m-%d %H:%M:%S")

    def _display_title(self, value: str) -> str:
        normalized = _WHITESPACE_RE.sub(" ", self._normalize_newlines(value)).strip()
        return normalized or "Untitled session"

    def _build_filename(self, title: str, thread_id: str) -> str:
        cleaned_title = _WINDOWS_FILENAME_CHARS_RE.sub(" ", title)
        cleaned_title = _WHITESPACE_RE.sub(" ", cleaned_title).strip(" .")
        safe_title = (cleaned_title or "Untitled session")[:80].rstrip(" .") or "Untitled session"
        safe_thread_id = _WINDOWS_FILENAME_CHARS_RE.sub("-", thread_id).strip() or "thread"
        return f"{safe_title}-{safe_thread_id}.md"

    def _render_markdown(self, title: str, messages: list[tuple[str, str | None, str]]) -> str:
        lines = [f"# {title}", ""]
        for speaker, timestamp, body in messages:
            lines.append(f"### {speaker}")
            if timestamp:
                lines.append(f"_{timestamp}_")
            lines.append("")
            lines.append(body.rstrip())
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _normalize_session_id(self, session_id: str) -> str:
        return session_id.removeprefix("local:")

    def _normalize_newlines(self, value: str) -> str:
        return value.replace("\r\n", "\n").replace("\r", "\n")

    def _failed(self, session_id: str, message: str) -> ExportResult:
        return ExportResult(
            status=ExportStatus.FAILED,
            session_id=session_id,
            message=message,
            filename=None,
            markdown=None,
        )
