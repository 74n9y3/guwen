"""本地古文阅读：原文、拼音、AI 白话。只监听本机。"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
import sqlite3
import sys
import threading
import traceback
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pypinyin import Style, pinyin

from guwen_text import fts_query, is_hanzi, plain_key

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "poems.db"
SPEECH_DIR = ROOT / "data" / "speech"
SETTINGS_PATH = ROOT / "data" / "settings.json"
STATIC = ROOT / "static"
ENV_PATH = ROOT / ".env"

READING_CHARS = set("abcdefghijklmnopqrstuvwxyzüāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜńňǹḿ")
SETTINGS_LOCK = threading.Lock()
READING_CACHE: dict[str, list[str]] = {}

EXTRA_SCHEMA = """
CREATE TABLE IF NOT EXISTS pinyin_fix (
  poem_id INTEGER NOT NULL,
  line_no INTEGER NOT NULL,
  offset INTEGER NOT NULL,
  reading TEXT NOT NULL,
  PRIMARY KEY (poem_id, line_no, offset)
);
CREATE TABLE IF NOT EXISTS ai_notes (
  poem_id INTEGER PRIMARY KEY,
  body TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ai_notes_en (
  poem_id INTEGER PRIMARY KEY,
  body TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ai_readings (
  poem_id INTEGER PRIMARY KEY,
  body TEXT NOT NULL,
  provider TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ai_messages (
  id INTEGER PRIMARY KEY,
  poem_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS favorites (
  poem_id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS glosses (
  cache_key TEXT PRIMARY KEY,
  char TEXT NOT NULL,
  line TEXT NOT NULL,
  body TEXT NOT NULL,
  provider TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


NOTE_TABLES = {"zh": "ai_notes", "en": "ai_notes_en"}
TITLE_LINE = -1

EN_ERRORS = {
    "没有返回正文": "The model returned nothing",
    "没有可用的免费接口。": "No AI provider is configured. See the README to add one in .env.",
    "免费接口都没通。": "None of the AI providers responded. ",
    "找不到这首": "Poem not found",
    "先写问题": "Type a question first",
    "问题太长了，缩短一点": "The question is too long; please shorten it",
    "这个字对不上": "That character doesn't match the text",
    "标点不用解释": "Punctuation has no gloss",
    "这个字不用标音": "This character takes no pinyin",
    "读音只用拼音字母": "Use pinyin letters only",
    "换个字再搜": "Try different search words",
    "朗读暂时连不上": "Text-to-speech is unreachable right now",
    "没有生成声音": "No audio was produced",
    "这首没有可以读的字": "Nothing to read aloud in this poem",
    "内容太长": "Request too large",
    "请求读不懂": "Malformed request",
    "出错了": "Something went wrong",
    "核对读音时没读懂回答": "Couldn't parse the AI's pronunciation check",
}


class AppError(Exception):
    pass


def pick_lang(value: str | None) -> str:
    return "en" if str(value or "").strip().lower().startswith("en") else "zh"


def localize(message: str, lang: str) -> str:
    if lang != "en":
        return message
    for source, target in EN_ERRORS.items():
        if message == source:
            return target
        if message.startswith(source):
            return target + message[len(source) :]
    return message


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


FREE_SPECS = {
    "groq": ("GROQ_API_KEY", "GROQ_MODEL", "GROQ_BASE_URL", "qwen/qwen3.8-27b", "https://api.groq.com/openai/v1", "Groq"),
    "nvidia": (
        "NVIDIA_API_KEY",
        "NVIDIA_MODEL",
        "NVIDIA_BASE_URL",
        "nvidia/nemotron-3-super-120b-a12b",
        "https://integrate.api.nvidia.com/v1",
        "NVIDIA",
    ),
    "openrouter": (
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "OPENROUTER_BASE_URL",
        "openrouter/free",
        "https://openrouter.ai/api/v1",
        "OpenRouter",
    ),
    "gemini": (
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "GEMINI_BASE_URL",
        "gemini-flash-lite-latest",
        "https://generativelanguage.googleapis.com/v1beta/openai",
        "Gemini",
    ),
    "cerebras": (
        "CEREBRAS_API_KEY",
        "CEREBRAS_MODEL",
        "CEREBRAS_BASE_URL",
        "gpt-oss-120b",
        "https://api.cerebras.ai/v1",
        "Cerebras",
    ),
    "sambanova": (
        "SAMBANOVA_API_KEY",
        "SAMBANOVA_MODEL",
        "SAMBANOVA_BASE_URL",
        "Meta-Llama-3.3-70B-Instruct",
        "https://api.sambanova.ai/v1",
        "SambaNova",
    ),
}


def read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.split("#", 1)[0].strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def provider_chain() -> list[dict]:
    env = read_env(ENV_PATH)
    chain: list[dict] = []
    custom_key = env.get("LLM_API_KEY", "").strip()
    custom_base = env.get("LLM_BASE_URL", "").strip()
    custom_model = env.get("LLM_MODEL", "").strip()
    if custom_key and custom_base and custom_model:
        chain.append(
            {
                "id": "custom",
                "name": env.get("LLM_PROVIDER", "").strip() or "自备接口",
                "model": custom_model,
                "base_url": custom_base,
                "api_key": custom_key,
            }
        )
    bai_key = env.get("BAI_API_KEY", "").strip()
    use_bai = env.get("LLM_TRY_BAI_AFTER_GROQ", "true").lower() != "false"
    if bai_key and use_bai:
        chain.append(
            {
                "id": "b.ai",
                "name": "b.ai",
                "model": env.get("BAI_MODEL", "").strip() or "deepseek-v4-flash",
                "base_url": env.get("BAI_BASE_URL", "").strip() or "https://api.b.ai/v1",
                "api_key": bai_key,
            }
        )
    order = [item.strip().lower() for item in env.get("LLM_FREE_ORDER", "groq,nvidia,openrouter,gemini").split(",") if item.strip()]
    for name in order:
        spec = FREE_SPECS.get(name)
        if spec is None:
            continue
        key_name, model_name, base_name, default_model, default_base, label = spec
        key = env.get(key_name, "").strip()
        if not key:
            continue
        chain.append(
            {
                "id": name,
                "name": label,
                "model": env.get(model_name, "").strip() or default_model,
                "base_url": env.get(base_name, "").strip() or default_base,
                "api_key": key,
            }
        )
    return chain


def chat_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1") or base.endswith("/openai"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def redact(text: str) -> str:
    cleaned = re.sub(r"(sk-|gsk_|nvapi-|csk-|or-v1-)[A-Za-z0-9_\-]+", r"\1…", text)
    cleaned = re.sub(r"AQ\.[A-Za-z0-9_\-]+", "AQ.…", cleaned)
    return cleaned[:180]


def message_text(payload: dict) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(str(part.get("text") or ""))
            else:
                parts.append(str(part))
        content = "".join(parts)
    return str(content or "").strip()


def call_one(provider: dict, messages: list[dict], temperature: float, max_tokens: int = 2000) -> str:
    body = json.dumps(
        {
            "model": provider["model"],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": messages,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {
        "Authorization": "Bearer " + provider["api_key"],
        "Content-Type": "application/json",
    }
    if provider["id"] == "openrouter":
        headers["HTTP-Referer"] = "http://127.0.0.1:8765"
        headers["X-Title"] = "guwen"
    request = urllib.request.Request(chat_url(provider["base_url"]), data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=40 if max_tokens <= 2000 else 120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = redact(error.read().decode("utf-8", "replace"))
        raise AppError(f"{error.code} {detail}") from None
    except (urllib.error.URLError, TimeoutError) as error:
        raise AppError(redact(str(error))) from None
    text = message_text(payload)
    if not text:
        raise AppError("没有返回正文")
    return text


def call_model(messages: list[dict], temperature: float = 0.3, max_tokens: int = 2000) -> tuple[str, str]:
    chain = provider_chain()
    if not chain:
        raise AppError("没有可用的免费接口。")
    errors = []
    for provider in chain:
        try:
            text = call_one(provider, messages, temperature, max_tokens)
            return text, provider["name"]
        except Exception as error:
            detail = redact(str(error))
            errors.append(f"{provider['name']}：{detail}")
            print(f"换下一家 {provider['name']}: {detail}", file=sys.stderr, flush=True)
    raise AppError("免费接口都没通。" + " ".join(errors))


def parse_model_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.S)
        if not match:
            raise ValueError("not json")
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("not object")
    return value


def normalize_note(obj: dict, covered: int, total: int) -> dict:
    summary = str(obj.get("summary") or "").strip()
    raw_lines = obj.get("lines") if isinstance(obj.get("lines"), list) else []
    lines = [str(item).strip() for item in raw_lines]
    words = []
    raw_words = obj.get("words") if isinstance(obj.get("words"), list) else []
    for item in raw_words:
        if not isinstance(item, dict):
            continue
        word = str(item.get("word") or "").strip()
        gloss = str(item.get("note") or item.get("meaning") or "").strip()
        if word and gloss:
            words.append({"word": word, "note": gloss})
        if len(words) >= 8:
            break
    if not summary and not any(lines) and not words:
        raise ValueError("empty")
    return {
        "summary": summary,
        "lines": lines,
        "words": words,
        "covered": covered,
        "total": total,
        "clipped": covered < total,
    }


def readings_for(char: str) -> list[str]:
    cached = READING_CACHE.get(char)
    if cached is not None:
        return cached
    options: list[str] = []
    for item in pinyin(char, style=Style.TONE, heteronym=True, errors=lambda chars: [chars]):
        for reading in item:
            if reading and reading != char and reading not in options:
                options.append(reading)
    READING_CACHE[char] = options
    return options


def line_tokens(text: str, fixes: dict[int, str], ai: dict[int, str] | None = None) -> list[dict]:
    ai = ai or {}
    try:
        raw = pinyin(text, style=Style.TONE, heteronym=False, errors=lambda chars: [""])
    except Exception:
        raw = []
    if len(raw) != len(text):
        raw = []
        for char in text:
            if is_hanzi(char):
                raw.append(pinyin(char, style=Style.TONE, heteronym=False)[0])
            else:
                raw.append([""])
    tokens = []
    for index, char in enumerate(text):
        han = is_hanzi(char)
        reading = ""
        if han:
            reading = fixes.get(index) or ai.get(index) or (raw[index][0] if raw[index] else "")
            if reading == char:
                reading = ""
        tokens.append(
            {
                "t": char,
                "p": reading,
                "han": han,
                "i": index,
                "fixed": index in fixes,
                "ai": index in ai and index not in fixes,
            }
        )
    return tokens


def poem_lines(row: sqlite3.Row) -> list[str]:
    value = json.loads(row["paragraphs"])
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def list_item(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "author": row["author"],
        "dynasty": row["dynasty"],
        "genre": row["genre"],
        "rhythmic": row["rhythmic"],
        "first": row["first_line"],
    }


def load_poem(conn: sqlite3.Connection, poem_id: int, lang: str = "zh") -> dict:
    row = conn.execute("SELECT * FROM poems WHERE id = ?", (poem_id,)).fetchone()
    if row is None:
        raise AppError("找不到这首")
    fixes: dict[int, dict[int, str]] = {}
    for fix in conn.execute(
        "SELECT line_no, offset, reading FROM pinyin_fix WHERE poem_id = ?",
        (poem_id,),
    ):
        fixes.setdefault(fix["line_no"], {})[fix["offset"]] = fix["reading"]
    ai_row = conn.execute("SELECT body FROM ai_readings WHERE poem_id = ?", (poem_id,)).fetchone()
    ai_items = json.loads(ai_row["body"]).get("items", []) if ai_row else []
    ai_fixes: dict[int, dict[int, str]] = {}
    for item in ai_items:
        if item.get("changed"):
            ai_fixes.setdefault(item["line"], {})[item["offset"]] = item["reading"]
    reading_notes = [
        {
            "line": item["line"],
            "offset": item["offset"],
            "char": item["char"],
            "reading": item["reading"],
            "changed": bool(item.get("changed")),
            "note": item.get(lang) or item.get("zh") or "",
        }
        for item in ai_items
    ]
    lines = []
    for index, text in enumerate(poem_lines(row)):
        lines.append({"tokens": line_tokens(text, fixes.get(index, {}), ai_fixes.get(index))})
    note_row = conn.execute(f"SELECT body FROM {NOTE_TABLES[lang]} WHERE poem_id = ?", (poem_id,)).fetchone()
    note = json.loads(note_row["body"]) if note_row else None
    messages = [
        {"role": item["role"], "content": item["content"]}
        for item in conn.execute(
            "SELECT role, content FROM ai_messages WHERE poem_id = ? AND lang = ? ORDER BY id",
            (poem_id, lang),
        )
    ]
    favorite = conn.execute("SELECT 1 FROM favorites WHERE poem_id = ?", (poem_id,)).fetchone()
    return {
        "id": row["id"],
        "title": row["title"],
        "title_tokens": line_tokens(row["title"] or "", {}, ai_fixes.get(TITLE_LINE)),
        "readings_checked": ai_row is not None,
        "reading_notes": reading_notes,
        "author": row["author"],
        "dynasty": row["dynasty"],
        "genre": row["genre"],
        "rhythmic": row["rhythmic"],
        "section": row["section"],
        "favorite": favorite is not None,
        "variant": row["variant"] or "",
        "lines": lines,
        "note": note,
        "messages": messages,
    }


def poem_plain_lines(conn: sqlite3.Connection, poem_id: int) -> tuple[sqlite3.Row, list[str]]:
    row = conn.execute("SELECT * FROM poems WHERE id = ?", (poem_id,)).fetchone()
    if row is None:
        raise AppError("找不到这首")
    return row, poem_lines(row)


def format_poem(row: sqlite3.Row, lines: list[str]) -> str:
    head = [f"题目：{row['title']}", f"作者：{row['author'] or '不详'}", f"朝代：{row['dynasty']}", f"体裁：{row['genre']}"]
    if row["rhythmic"] and row["rhythmic"] != row["title"]:
        head.append(f"词牌：{row['rhythmic']}")
    if row["section"] and row["section"] != row["title"]:
        head.append(f"篇次：{row['section']}")
    if row["variant"]:
        head.append("版本：" + row["variant"])
    body = "\n".join(f"{index + 1}. {line}" for index, line in enumerate(lines))
    return "\n".join(head) + "\n\n" + body


def select_lines_for_model(lines: list[str]) -> tuple[list[str], bool]:
    chosen = []
    total = 0
    for line in lines:
        if chosen and total + len(line) > 12000:
            break
        chosen.append(line)
        total += len(line)
        if len(chosen) >= 250:
            break
    return chosen, len(chosen) < len(lines)


def interpret(poem_id: int, refresh: bool, lang: str = "zh") -> dict:
    table = NOTE_TABLES[lang]
    conn = connect()
    try:
        if not refresh:
            cached = conn.execute(f"SELECT body FROM {table} WHERE poem_id = ?", (poem_id,)).fetchone()
            if cached:
                return json.loads(cached["body"])
        row, lines = poem_plain_lines(conn, poem_id)
        sent, clipped = select_lines_for_model(lines)
        clip_note = ""
        if lang == "en":
            if clipped:
                clip_note = (
                    f"The poem has {len(lines)} lines; only the first {len(sent)} are given below. "
                    f"\"lines\" covers only these {len(sent)}.\n"
                )
            system = (
                "You are helping an English-speaking learner of Chinese read this classical poem. "
                "Write in plain, natural English. Keep it short and close to the original. "
                "No lesson plans, no exam points, no stock appreciation essays. "
                "If you are unsure about an allusion, say so; never invent sources. "
                "Return JSON only, no Markdown. "
                '{"summary":"two or three sentences on what the poem is about",'
                '"lines":["an English rendering of each original line"],'
                '"words":[{"word":"a word from the original, in Chinese characters","note":"what it means in this line, in English"}]} '
                f"\"lines\" must have exactly {len(sent)} items, in the original order, none merged or skipped. "
                "\"words\": at most 8, only the ones likely to trip up a learner."
            )
        else:
            if clipped:
                clip_note = f"全诗 {len(lines)} 句，下面只给开头 {len(sent)} 句。lines 只覆盖这 {len(sent)} 句。\n"
            system = (
                "你在帮一个人读这一首诗词。用简体白话，短，紧贴原文。"
                "不要写教案，不要写考点，不要写套话赏析。"
                "典故拿不准就明说不确定，不要编书名。"
                "只返回 JSON，不要 Markdown。"
                '{"summary":"两三句说明这首在说什么","lines":["与原文逐句对应的白话"],'
                '"words":[{"word":"原文中的词","note":"在这一句里的意思"}]}'
                f"lines 必须正好 {len(sent)} 条，顺序与原文一致，不要合并，不要漏。"
                "words 最多 8 个，只挑会绊住现代读者的字词。"
            )
        user = clip_note + format_poem(row, sent)
        raw, provider_name = call_model(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        try:
            note = normalize_note(parse_model_json(raw), len(sent), len(lines))
            note["provider"] = provider_name
        except (ValueError, json.JSONDecodeError):
            note = {
                "summary": raw.strip(),
                "lines": [],
                "words": [],
                "covered": 0,
                "total": len(lines),
                "clipped": clipped,
                "raw": True,
                "provider": provider_name,
            }
        conn.execute(
            f"""
            INSERT INTO {table} (poem_id, body, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(poem_id) DO UPDATE SET body = excluded.body, updated_at = excluded.updated_at
            """,
            (poem_id, json.dumps(note, ensure_ascii=False), now()),
        )
        conn.commit()
        return note
    finally:
        conn.close()


def ask(poem_id: int, question: str, lang: str = "zh") -> tuple[str, str]:
    question = question.strip()
    if not question:
        raise AppError("先写问题")
    if len(question) > 500:
        raise AppError("问题太长了，缩短一点")
    conn = connect()
    try:
        row, lines = poem_plain_lines(conn, poem_id)
        sent, clipped = select_lines_for_model(lines)
        note_row = conn.execute(f"SELECT body FROM {NOTE_TABLES[lang]} WHERE poem_id = ?", (poem_id,)).fetchone()
        context = format_poem(row, sent)
        if clipped:
            context += "\n\n(The poem continues; only the beginning is included.)" if lang == "en" else "\n\n（后面还有，这里只附了开头。）"
        if note_row:
            note = json.loads(note_row["body"])
            if note.get("summary"):
                context += ("\n\nExisting summary: " if lang == "en" else "\n\n已有的白话提要：") + note["summary"]
        history = [
            {"role": item["role"], "content": item["content"]}
            for item in conn.execute(
                "SELECT role, content FROM ai_messages WHERE poem_id = ? AND lang = ? ORDER BY id DESC LIMIT 8",
                (poem_id, lang),
            )
        ]
        history.reverse()
        while history and history[0]["role"] != "user":
            history.pop(0)
        if lang == "en":
            system = (
                "You are helping an English-speaking learner of Chinese read the poem below. "
                "Answer directly in plain English text, without Markdown, and keep it short. "
                "When you quote Chinese words, add pinyin in parentheses. "
                "If unsure, say so; never invent sources for allusions. Do not write an appreciation essay or a lesson plan."
            )
        else:
            system = (
                "你在帮一个人读下面这首诗词。用简体白话直接回答，短一点。"
                "不确定就说不确定，不要编典故出处，不要写成赏析作文或教案。"
            )
        messages = [
            {"role": "system", "content": system + "\n\n" + context},
            *history,
            {"role": "user", "content": question},
        ]
        answer, provider_name = call_model(messages, temperature=0.3)
        stamp = now()
        conn.execute(
            "INSERT INTO ai_messages (poem_id, role, content, created_at, lang) VALUES (?, 'user', ?, ?, ?)",
            (poem_id, question, stamp, lang),
        )
        conn.execute(
            "INSERT INTO ai_messages (poem_id, role, content, created_at, lang) VALUES (?, 'assistant', ?, ?, ?)",
            (poem_id, answer, stamp, lang),
        )
        conn.commit()
        return answer, provider_name
    finally:
        conn.close()


def normalize_gloss(obj: dict, char: str, line: str) -> dict:
    in_line = str(obj.get("in_line") or "").strip()
    senses = []
    for item in obj.get("senses") or []:
        text = str(item).strip()
        if text:
            senses.append(text)
        if len(senses) >= 4:
            break
    words = []
    for item in obj.get("words") or []:
        if isinstance(item, dict):
            word = str(item.get("word") or "").strip()
            note = str(item.get("note") or "").strip()
        else:
            word, note = str(item).strip(), ""
        if word:
            words.append({"word": word, "note": note})
        if len(words) >= 3:
            break
    if not in_line and not senses and not words:
        raise ValueError("empty")
    return {"char": char, "line": line, "in_line": in_line, "senses": senses, "words": words}


def gloss(poem_id: int, line_no: int, offset: int, lang: str = "zh") -> dict:
    conn = connect()
    try:
        row, lines = poem_plain_lines(conn, poem_id)
        if line_no < 0 or line_no >= len(lines) or offset < 0 or offset >= len(lines[line_no]):
            raise AppError("这个字对不上")
        line = lines[line_no]
        char = line[offset]
        if not is_hanzi(char):
            raise AppError("标点不用解释")
        version = "v2-en" if lang == "en" else "v2"
        cache_key = hashlib.sha1(f"{version}\n{char}\n{line}".encode("utf-8")).hexdigest()
        cached = conn.execute(
            "SELECT body, provider FROM glosses WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if cached:
            body = json.loads(cached["body"])
            body["provider"] = cached["provider"]
            body["char"] = char
            return body
        if lang == "en":
            system = (
                "You are a concise classical Chinese dictionary for English-speaking learners. "
                "Explain only the single character the user picked. "
                "First give its meaning in this line, then other common senses in classical Chinese. "
                "Write in English, briefly. Do not include pinyin. Never invent sources. "
                "Return JSON only: "
                '{"in_line":"its meaning in this line","senses":["other classical senses"],'
                '"words":[{"word":"a related word in Chinese characters","note":"its meaning in English"}]} '
                "\"senses\": classical senses only; each starts with a short classical Chinese phrase using the character, "
                "followed by a brief English explanation. Skip meanings found only in modern colloquial Chinese. "
                "\"words\": at most 3 words common in classical Chinese. Write fewer if unsure."
            )
        else:
            system = (
                "你是一本简明文言词典。只解释用户点到的那一个字。"
                "先说它在这一句里的意思，再列文言里其他常见义项。"
                "用简体白话，短。不要写拼音，不要编书名。"
                "只返回 JSON："
                '{"in_line":"在这一句里的意思","senses":["其他文言义"],'
                '"words":[{"word":"相关的词","note":"意思"}]}'
                "senses 只写文言文里的义项，每条先给一个文言说法，再跟一句短白话。"
                "不要写现代口语里才有的意思。"
                "words 只收古汉语里常见的词，最多 3 个。不确定就少写。"
            )
        user = (
            f"题目：{row['title']}\n作者：{row['author'] or '不详'}\n"
            f"这一句：{line}\n要解释的字：{char}\n"
            f"它是这一句的第 {offset + 1} 个字。"
        )
        raw, provider_name = call_model(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
        try:
            body = normalize_gloss(parse_model_json(raw), char, line)
        except (ValueError, json.JSONDecodeError):
            body = {"char": char, "line": line, "in_line": raw.strip(), "senses": [], "words": []}
        conn.execute(
            """
            INSERT INTO glosses (cache_key, char, line, body, provider, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
              body = excluded.body, provider = excluded.provider, updated_at = excluded.updated_at
            """,
            (cache_key, char, line, json.dumps(body, ensure_ascii=False), provider_name, now()),
        )
        conn.commit()
        body["provider"] = provider_name
        return body
    finally:
        conn.close()


def reading_candidates(title: str, lines: list[str]) -> list[dict]:
    candidates = []
    for line_no, text in [(TITLE_LINE, title), *enumerate(lines)]:
        for token in line_tokens(text, {}):
            if not token["han"] or not token["p"]:
                continue
            options = readings_for(token["t"])
            if len(options) < 2:
                continue
            offset = token["i"]
            candidates.append(
                {
                    "id": len(candidates) + 1,
                    "line": line_no,
                    "offset": offset,
                    "char": token["t"],
                    "current": token["p"],
                    "options": options,
                    "context": text[:offset] + "【" + token["t"] + "】" + text[offset + 1 :],
                }
            )
            if len(candidates) >= 160:
                return candidates
    return candidates


def check_readings(poem_id: int) -> None:
    conn = connect()
    try:
        if conn.execute("SELECT 1 FROM ai_readings WHERE poem_id = ?", (poem_id,)).fetchone():
            return
        row, lines = poem_plain_lines(conn, poem_id)
        sent, _ = select_lines_for_model(lines)
        candidates = reading_candidates(row["title"] or "", sent)
        items = []
        provider_name = ""
        if candidates:
            system = (
                "你在给一首古诗词校对拼音。下面列出诗里的多音字，每个有编号、所在的句子（用【】标出这个字）、"
                "程序现在给的读音和可选读音。"
                "读音一律以现行规范为准：《现代汉语词典》、《普通话异读词审音表》和现行语文课本的注音。"
                "审音表已统读的字按统读音，不要为押韵改用古音或叶音（例如“斜”统读 xié，不读 xiá）；"
                "有流行的古读时，只在说明里提一句。"
                "注意这个字在这一句里的词义、人名地名、通假字。拿不准就不要改。"
                "挑出两类字：一是现在的读音不对的，给出正确读音；"
                "二是读音已经对、但常被读错的，reading 照抄现在的读音。"
                "第二类只挑学生和普通读者真会读错的，最多 5 个；"
                "像“相见”的相、“何处”的处这种一般人不会读错的，不要列。"
                "reading 必须从这个字的可选读音里原样选一个。"
                "只返回 JSON，不要 Markdown："
                '{"items":[{"id":编号,"reading":"正确读音","zh":"一句简体中文，说明这里为什么这样读",'
                '"en":"the same reason in one short English sentence"}]}'
                '没有要提醒的就返回 {"items":[]}。'
            )
            listing = "\n".join(
                f"{item['id']}. {item['char']} | {'题目' if item['line'] == TITLE_LINE else '第' + str(item['line'] + 1) + '句'}："
                f"{item['context']} | 现在：{item['current']} | 可选：{'、'.join(item['options'])}"
                for item in candidates
            )
            user = f"题目：{row['title']}\n作者：{row['author'] or '不详'}\n朝代：{row['dynasty']}\n\n{listing}"
            parsed = None
            for _ in range(2):
                raw, provider_name = call_model(
                    [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    temperature=0.1,
                    max_tokens=6000,
                )
                try:
                    parsed = parse_model_json(raw)
                    break
                except (ValueError, json.JSONDecodeError):
                    print(f"读音核对回答不是 JSON：{raw[:300]!r}", file=sys.stderr, flush=True)
            if parsed is None:
                raise AppError("核对读音时没读懂回答")
            by_id = {item["id"]: item for item in candidates}
            seen = set()
            kept = 0
            for entry in parsed.get("items") or []:
                if not isinstance(entry, dict):
                    continue
                try:
                    candidate = by_id.get(int(entry.get("id")))
                except (TypeError, ValueError):
                    continue
                reading = str(entry.get("reading") or "").strip().lower()
                if candidate is None or candidate["id"] in seen or reading not in candidate["options"]:
                    continue
                changed = reading != candidate["current"]
                if not changed:
                    if kept >= 5:
                        continue
                    kept += 1
                seen.add(candidate["id"])
                items.append(
                    {
                        "line": candidate["line"],
                        "offset": candidate["offset"],
                        "char": candidate["char"],
                        "reading": reading,
                        "changed": changed,
                        "zh": str(entry.get("zh") or "").strip(),
                        "en": str(entry.get("en") or "").strip(),
                    }
                )
                if len(items) >= 12:
                    break
        conn.execute(
            """
            INSERT INTO ai_readings (poem_id, body, provider, updated_at) VALUES (?, ?, ?, ?)
            ON CONFLICT(poem_id) DO UPDATE SET
              body = excluded.body, provider = excluded.provider, updated_at = excluded.updated_at
            """,
            (poem_id, json.dumps({"items": items}, ensure_ascii=False), provider_name, now()),
        )
        conn.commit()
    finally:
        conn.close()


def clean_reading(reading: str) -> str:
    text = reading.strip().lower().replace("u:", "ü").replace("v", "ü")
    if not text or len(text) > 16 or any(char not in READING_CHARS for char in text):
        raise AppError("读音只用拼音字母")
    return text


def search(query: str, genre: str) -> dict:
    match = fts_query(query)
    if not match:
        raise AppError("换个字再搜")
    if genre not in {"", "诗", "词", "诗经", "楚辞", "曲"}:
        genre = ""
    key = plain_key(query)
    prefix = key if " " not in query.strip() and len(key) >= 4 else ""
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT p.id, p.title, p.author, p.dynasty, p.genre, p.rhythmic, p.first_line
            FROM poems_fts
            JOIN poems p ON p.id = poems_fts.rowid
            WHERE poems_fts MATCH ?
              AND (? = '' OR p.genre = ?)
            ORDER BY CASE WHEN p.title_key = ? THEN 0 ELSE 1 END,
                     CASE WHEN p.author_key = ? THEN 0 ELSE 1 END,
                     CASE WHEN ? != '' AND (
                       p.first_line = ?
                       OR p.first_line LIKE ? || '，%'
                       OR p.first_line LIKE ? || '。%'
                       OR p.first_line LIKE ? || '、%'
                       OR p.first_line LIKE ? || '；%'
                       OR p.first_line LIKE ? || '？%'
                       OR p.first_line LIKE ? || '！%'
                     ) THEN 0 ELSE 1 END,
                     CASE WHEN ? != '' AND p.first_line LIKE ? || '%' THEN 0 ELSE 1 END,
                     CASE WHEN p.shelf != '' THEN 0 ELSE 1 END,
                     bm25(poems_fts, 2.0, 1.5, 1.2, 1.0),
                     p.id
            LIMIT 40
            """,
            (match, genre, genre, key, key, *([prefix] * 8), prefix, prefix),
        ).fetchall()
    finally:
        conn.close()
    return {"items": [list_item(row) for row in rows], "limited": len(rows) == 40}


def browse(shelf: str) -> dict:
    conn = connect()
    try:
        if shelf == "fav":
            label = "收藏"
            rows = conn.execute(
                """
                SELECT p.id, p.title, p.author, p.dynasty, p.genre, p.rhythmic, p.first_line
                FROM favorites f
                JOIN poems p ON p.id = f.poem_id
                ORDER BY f.created_at DESC
                """
            ).fetchall()
        elif shelf == "shijing":
            label = "诗经"
            rows = conn.execute(
                """
                SELECT id, title, author, dynasty, genre, rhythmic, first_line
                FROM poems WHERE genre = '诗经' ORDER BY id
                """
            ).fetchall()
        elif shelf == "chuci":
            label = "楚辞"
            rows = conn.execute(
                """
                SELECT id, title, author, dynasty, genre, rhythmic, first_line
                FROM poems WHERE genre = '楚辞' ORDER BY id
                """
            ).fetchall()
        elif shelf == "ci300":
            label = "宋词三百首"
            rows = conn.execute(
                """
                SELECT id, title, author, dynasty, genre, rhythmic, first_line
                FROM poems WHERE shelf = 'ci300' ORDER BY sort_key, id
                """
            ).fetchall()
        else:
            shelf = "tang300"
            label = "唐诗三百首"
            rows = conn.execute(
                """
                SELECT id, title, author, dynasty, genre, rhythmic, first_line
                FROM poems WHERE shelf = 'tang300' ORDER BY sort_key, id
                """
            ).fetchall()
        return {"shelf": shelf, "label": label, "items": [list_item(row) for row in rows]}
    finally:
        conn.close()


SPEECH_VOICES = {
    "zh-CN-YunjianNeural": "男声 · 朗读",
    "zh-CN-YunyangNeural": "男声 · 清楚",
    "zh-CN-YunxiNeural": "男声 · 年轻",
}


def speech_pieces(title: str, author: str, lines: list[str]) -> list[dict]:
    pieces = [{"text": title.rstrip("。！？") + "。", "line": -1, "part": 0}]
    if author:
        pieces.append({"text": author + "。", "line": -1, "part": 0})
    for index, line in enumerate(lines):
        buf = ""
        han = 0
        part = 0
        for char in line:
            buf += char
            if is_hanzi(char):
                han += 1
            if char in "，。！？；" and han >= 2:
                pieces.append({"text": buf, "line": index, "part": part})
                buf = ""
                han = 0
                part += 1
        if buf.strip():
            pieces.append({"text": buf, "line": index, "part": part})
    return pieces


def synthesize_speech(poem_id: int, voice: str) -> dict:
    if voice not in SPEECH_VOICES:
        voice = "zh-CN-YunjianNeural"
    conn = connect()
    try:
        row, lines = poem_plain_lines(conn, poem_id)
    finally:
        conn.close()
    pieces = speech_pieces(row["title"], row["author"] or "", lines)
    full = "".join(piece["text"] for piece in pieces)
    if not full.strip():
        raise AppError("这首没有可以读的字")
    key = hashlib.sha1(f"{voice}\n{full}".encode("utf-8")).hexdigest()
    SPEECH_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = SPEECH_DIR / f"{key}.mp3"
    mark_path = SPEECH_DIR / f"{key}.json"
    if not (audio_path.exists() and mark_path.exists()):
        audio, marks = asyncio.run(render_speech(full, pieces, voice))
        audio_path.write_bytes(audio)
        mark_path.write_text(json.dumps(marks, ensure_ascii=False), encoding="utf-8")
    return {
        "audio": base64.b64encode(audio_path.read_bytes()).decode("ascii"),
        "mime": "audio/mpeg",
        "marks": json.loads(mark_path.read_text(encoding="utf-8")),
        "voice": voice,
    }


async def render_speech(full: str, pieces: list[dict], voice: str) -> tuple[bytes, list[dict]]:
    import edge_tts

    communicate = edge_tts.Communicate(full, voice)
    audio = bytearray()
    bounds = []
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                bounds.append(chunk)
    except Exception as error:
        raise AppError("朗读暂时连不上") from error
    if not audio:
        raise AppError("没有生成声音")
    marks = []
    cursor = 0
    for bound in bounds:
        text = str(bound.get("text") or "")
        found = full.find(text, cursor) if text else cursor
        if found < 0:
            found = cursor
        piece = pieces[0]
        passed = 0
        for item in pieces:
            if found < passed + len(item["text"]):
                piece = item
                break
            passed += len(item["text"])
        marks.append(
            {
                "t": round(int(bound.get("offset") or 0) / 10_000_000, 3),
                "line": piece["line"],
                "part": piece["part"],
            }
        )
        cursor = found + len(text)
    return bytes(audio), marks


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        if str(args[1] if len(args) > 1 else "").startswith("5"):
            super().log_message(fmt, *args)

    @property
    def lang(self) -> str:
        return pick_lang(self.headers.get("X-Lang"))

    def send_error_json(self, message: str, status: int) -> None:
        self.send_json({"error": localize(message, self.lang)}, status)

    def send_json(self, payload: dict, status: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > 100_000:
            raise AppError("内容太长")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            raise AppError("请求读不懂") from None
        if not isinstance(data, dict):
            raise AppError("请求读不懂")
        return data

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        try:
            if path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if path == "/":
                self.send_file(STATIC / "index.html")
                return
            if path.startswith("/static/"):
                name = path[len("/static/") :]
                file = (STATIC / name).resolve()
                if not file.is_relative_to(STATIC.resolve()) or not file.is_file():
                    self.send_error(404)
                    return
                self.send_file(file)
                return
            if path == "/api/browse":
                self.send_json(browse(query.get("shelf", ["tang300"])[0]))
                return
            if path == "/api/search":
                self.send_json(search(query.get("q", [""])[0], query.get("genre", [""])[0]))
                return
            if path == "/api/poem":
                self.send_json(self.with_conn_poem(int(query.get("id", ["0"])[0])))
                return
            if path == "/api/readings":
                char = query.get("c", [""])[0]
                options = readings_for(char) if len(char) == 1 and is_hanzi(char) else []
                self.send_json({"readings": options})
                return
            if path == "/api/settings":
                chain = provider_chain()
                self.send_json(
                    {
                        "providers": [
                            {"name": item["name"], "model": item["model"]}
                            for item in chain
                        ]
                    }
                )
                return
            self.send_error(404)
        except AppError as error:
            self.send_error_json(str(error), 400)
        except Exception:
            traceback.print_exc()
            self.send_error_json("出错了", 500)

    def with_conn_poem(self, poem_id: int) -> dict:
        conn = connect()
        try:
            return load_poem(conn, poem_id, self.lang)
        finally:
            conn.close()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            data = self.read_body()
            path = parsed.path
            if path == "/api/reading":
                self.save_reading(data)
                return
            if path == "/api/favorite":
                self.save_favorite(data)
                return
            if path == "/api/gloss":
                body = gloss(int(data.get("id") or 0), int(data.get("line") or 0), int(data.get("offset") or 0), self.lang)
                self.send_json(body)
                return
            if path == "/api/interpret":
                note = interpret(int(data.get("id") or 0), bool(data.get("refresh")), self.lang)
                self.send_json({"note": note})
                return
            if path == "/api/ask":
                answer, provider_name = ask(int(data.get("id") or 0), str(data.get("question") or ""), self.lang)
                self.send_json({"answer": answer, "provider": provider_name})
                return
            if path == "/api/check-readings":
                poem_id = int(data.get("id") or 0)
                check_readings(poem_id)
                self.send_json(self.with_conn_poem(poem_id))
                return
            if path == "/api/speak":
                body = synthesize_speech(int(data.get("id") or 0), str(data.get("voice") or ""))
                self.send_json(body)
                return
            self.send_error(404)
        except AppError as error:
            self.send_error_json(str(error), 400)
        except Exception:
            traceback.print_exc()
            self.send_error_json("出错了", 500)

    def save_reading(self, data: dict) -> None:
        poem_id = int(data.get("id") or 0)
        line_no = int(data.get("line") or 0)
        offset = int(data.get("offset") or 0)
        reading = str(data.get("reading") or "")
        conn = connect()
        try:
            row, lines = poem_plain_lines(conn, poem_id)
            if line_no < 0 or line_no >= len(lines) or offset < 0 or offset >= len(lines[line_no]):
                raise AppError("这个字对不上")
            if not is_hanzi(lines[line_no][offset]):
                raise AppError("这个字不用标音")
            if reading.strip():
                cleaned = clean_reading(reading)
                conn.execute(
                    """
                    INSERT INTO pinyin_fix (poem_id, line_no, offset, reading) VALUES (?, ?, ?, ?)
                    ON CONFLICT(poem_id, line_no, offset) DO UPDATE SET reading = excluded.reading
                    """,
                    (poem_id, line_no, offset, cleaned),
                )
            else:
                conn.execute(
                    "DELETE FROM pinyin_fix WHERE poem_id = ? AND line_no = ? AND offset = ?",
                    (poem_id, line_no, offset),
                )
            conn.commit()
            self.send_json(load_poem(conn, poem_id, self.lang))
        finally:
            conn.close()

    def save_favorite(self, data: dict) -> None:
        poem_id = int(data.get("id") or 0)
        conn = connect()
        try:
            poem_plain_lines(conn, poem_id)
            existing = conn.execute("SELECT 1 FROM favorites WHERE poem_id = ?", (poem_id,)).fetchone()
            if existing:
                conn.execute("DELETE FROM favorites WHERE poem_id = ?", (poem_id,))
                favorite = False
            else:
                conn.execute(
                    "INSERT INTO favorites (poem_id, created_at) VALUES (?, ?)",
                    (poem_id, now()),
                )
                favorite = True
            conn.commit()
            self.send_json({"favorite": favorite})
        finally:
            conn.close()

    def send_file(self, path: Path) -> None:
        kind = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
        }.get(path.suffix, "application/octet-stream")
        raw = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(raw)


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit("还没有诗库。先运行：.venv/bin/python import_poetry.py")
    conn = connect()
    conn.executescript(EXTRA_SCHEMA)
    columns = {item["name"] for item in conn.execute("PRAGMA table_info(ai_messages)")}
    if "lang" not in columns:
        conn.execute("ALTER TABLE ai_messages ADD COLUMN lang TEXT NOT NULL DEFAULT 'zh'")
        conn.commit()
    conn.close()
    server = None
    port = 8765
    for candidate in range(8765, 8775):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            port = candidate
            break
        except OSError:
            continue
    if server is None:
        raise SystemExit("8765 到 8774 端口都被占用了")
    url = f"http://127.0.0.1:{port}"
    print(f"可以阅读了： {url}", flush=True)
    print("关掉这个窗口就停。", flush=True)
    if os_environ_open():
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停下", flush=True)


def os_environ_open() -> bool:
    import os

    return os.environ.get("GUWEN_OPEN", "1") != "0"


if __name__ == "__main__":
    main()
