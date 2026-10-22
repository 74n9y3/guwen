"""把 chinese-poetry 的原文转成简体，写入本地诗库。"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

from opencc import OpenCC

from guwen_text import fts_doc, fts_query, plain_key

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "data" / "chinese-poetry"
DB = ROOT / "data" / "poems.db"

SCHEMA = """
CREATE TABLE poems (
  id INTEGER PRIMARY KEY,
  source_id TEXT UNIQUE,
  title TEXT NOT NULL,
  title_key TEXT NOT NULL,
  author TEXT NOT NULL,
  author_key TEXT NOT NULL,
  dynasty TEXT NOT NULL,
  genre TEXT NOT NULL,
  rhythmic TEXT NOT NULL,
  section TEXT NOT NULL,
  shelf TEXT NOT NULL,
  sort_key INTEGER NOT NULL,
  first_line TEXT NOT NULL,
  paragraphs TEXT NOT NULL,
  content TEXT NOT NULL,
  variant TEXT NOT NULL DEFAULT ''
);

CREATE VIRTUAL TABLE poems_fts USING fts5(
  title, author, rhythmic, body,
  tokenize = "unicode61 remove_diacritics 0"
);

CREATE TABLE pinyin_fix (
  poem_id INTEGER NOT NULL,
  line_no INTEGER NOT NULL,
  offset INTEGER NOT NULL,
  reading TEXT NOT NULL,
  PRIMARY KEY (poem_id, line_no, offset)
);

CREATE TABLE ai_notes (
  poem_id INTEGER PRIMARY KEY,
  body TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE ai_messages (
  id INTEGER PRIMARY KEY,
  poem_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE favorites (
  poem_id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL
);
"""

DYNASTY = {
    "yuan": "元",
    "tang": "唐",
    "song": "宋",
    "ming": "明",
    "qing": "清",
    "han": "汉",
}


def load_json(path: Path, cc: OpenCC):
    raw = path.read_text(encoding="utf-8-sig")
    converted = cc.convert(raw)
    try:
        return json.loads(converted)
    except json.JSONDecodeError:
        return walk(json.loads(raw), cc)


def walk(obj, cc: OpenCC):
    if isinstance(obj, str):
        return cc.convert(obj)
    if isinstance(obj, list):
        return [walk(item, cc) for item in obj]
    if isinstance(obj, dict):
        return {key: walk(value, cc) for key, value in obj.items()}
    return obj


def str_list(value) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    lines = []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
            if text:
                lines.append(text)
    return lines


def source_id(item: dict, collection: str, index: int, title: str, author: str, paragraphs: list[str]) -> str:
    if item.get("id"):
        return str(item["id"])
    head = "\n".join(paragraphs[:4])
    raw = f"{collection}|{index}|{author}|{title}|{head}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def normalize(item: dict, index: int, collection: str, dynasty: str, genre: str, default_author: str, kind: str) -> dict | None:
    if not isinstance(item, dict):
        return None
    paragraphs = str_list(item.get("paragraphs") or item.get("para") or item.get("content"))
    if not paragraphs:
        return None
    rhythmic = (item.get("rhythmic") or "").strip()
    title = (item.get("title") or rhythmic or "无题").strip()
    author = (item.get("author") or default_author or "").strip()
    section = ""
    if kind == "shijing":
        genre = "诗经"
        dynasty = "先秦"
        author = ""
        section = " · ".join(part for part in (item.get("chapter"), item.get("section")) if part)
    elif kind == "chuci":
        genre = "楚辞"
        dynasty = "先秦"
        section = (item.get("section") or "").strip()
    raw_dyn = str(item.get("dynasty") or "").strip()
    if raw_dyn:
        dynasty = DYNASTY.get(raw_dyn.lower(), raw_dyn)
    if genre == "词" and not rhythmic and "·" in title:
        rhythmic = title.split("·", 1)[0].strip()
    return {
        "source_id": source_id(item, collection, index, title, author, paragraphs),
        "title": title,
        "author": author,
        "dynasty": dynasty,
        "genre": genre,
        "rhythmic": rhythmic,
        "section": section,
        "shelf": "",
        "sort_key": 0,
        "paragraphs": paragraphs,
    }


def insert_poem(conn: sqlite3.Connection, poem: dict) -> int:
    paragraphs = poem["paragraphs"]
    content = "\n".join(paragraphs)
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO poems (
          source_id, title, title_key, author, author_key, dynasty, genre,
          rhythmic, section, shelf, sort_key, first_line, paragraphs, content
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            poem["source_id"],
            poem["title"],
            plain_key(poem["title"]),
            poem["author"],
            plain_key(poem["author"]),
            poem["dynasty"],
            poem["genre"],
            poem["rhythmic"],
            poem["section"],
            poem["shelf"],
            poem["sort_key"],
            paragraphs[0],
            json.dumps(paragraphs, ensure_ascii=False, separators=(",", ":")),
            content,
        ),
    )
    if cur.rowcount == 0:
        return 0
    poem_id = cur.lastrowid
    conn.execute(
        "INSERT INTO poems_fts(rowid, title, author, rhythmic, body) VALUES (?, ?, ?, ?, ?)",
        (
            poem_id,
            fts_doc(poem["title"]),
            fts_doc(poem["author"]),
            fts_doc(poem["rhythmic"]),
            fts_doc(content),
        ),
    )
    return poem_id


def skip_file(path: Path) -> bool:
    name = path.name
    if name in {"authors.json", "intro.json", "唐诗三百首.json", "宋词三百首.json"}:
        return True
    if name.startswith("author"):
        return True
    if "preface" in name:
        return True
    return False


def file_number(path: Path) -> int:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return int(digits) if digits else 10**12


def ingest_file(conn, cc, path: Path, collection: str, dynasty: str, genre: str, default_author: str, kind: str, tang300: dict) -> int:
    data = load_json(path, cc)
    if not isinstance(data, list):
        return 0
    added = 0
    with conn:
        for index, item in enumerate(data):
            poem = normalize(item, index, collection, dynasty, genre, default_author, kind)
            if poem is None:
                continue
            shelf = tang300.get(poem["source_id"])
            if shelf is not None:
                poem["shelf"] = "tang300"
                poem["sort_key"] = shelf
            if insert_poem(conn, poem):
                added += 1
    print(f"{added:5d}  {path.relative_to(SRC)}", flush=True)
    return added


def load_tang300(cc: OpenCC) -> tuple[dict[str, int], dict[str, dict]]:
    data = load_json(SRC / "全唐诗" / "唐诗三百首.json", cc)
    mapping = {}
    items = {}
    for index, item in enumerate(data):
        if isinstance(item, dict) and item.get("id"):
            mapping[str(item["id"])] = index
            items[str(item["id"])] = item
    return mapping, items


def load_ci300(cc: OpenCC) -> list[dict]:
    data = load_json(SRC / "宋词" / "宋词三百首.json", cc)
    return [item for item in data if isinstance(item, dict)]


def head(text: str, size: int = 12) -> str:
    return plain_key(text)[:size]


def mark_anthologies(conn: sqlite3.Connection, tang_items: dict[str, dict], tang_ids: dict[str, int], ci_items: list[dict]) -> None:
    seen = {row[0] for row in conn.execute("SELECT source_id FROM poems WHERE shelf = 'tang300'")}
    tang_marked = len(seen)
    tang_added = 0
    with conn:
        for source, sort_key in tang_ids.items():
            if source in seen:
                continue
            raw = tang_items.get(source)
            if raw is None:
                continue
            poem = normalize(raw, sort_key, "唐诗三百首", "唐", "诗", "", "")
            if poem is None:
                continue
            found = find_existing(conn, poem["author"], poem["title"], poem["paragraphs"][0])
            if found:
                conn.execute(
                    "UPDATE poems SET shelf = 'tang300', sort_key = ? WHERE id = ?",
                    (sort_key, found),
                )
                tang_marked += 1
            else:
                poem["shelf"] = "tang300"
                poem["sort_key"] = sort_key
                if insert_poem(conn, poem):
                    tang_added += 1
                    tang_marked += 1
    print(f"唐诗三百首 对上 {tang_marked} 首，补入 {tang_added} 首", flush=True)

    rows = conn.execute("SELECT id, author_key, first_line FROM poems WHERE genre = '词'").fetchall()
    by_author: dict[str, list] = defaultdict(list)
    for row in rows:
        by_author[row["author_key"]].append(row)
    ci_marked = 0
    ci_added = 0
    with conn:
        for sort_key, item in enumerate(ci_items):
            poem = normalize(item, sort_key, "宋词三百首", "宋", "词", "", "")
            if poem is None:
                continue
            target = head(poem["paragraphs"][0])
            found = None
            for row in by_author.get(plain_key(poem["author"]), []):
                other = head(row["first_line"])
                if not target or not other:
                    continue
                if target.startswith(other[:8]) or other.startswith(target[:8]):
                    found = row["id"]
                    break
            if found:
                conn.execute(
                    "UPDATE poems SET shelf = 'ci300', sort_key = ? WHERE id = ?",
                    (sort_key, found),
                )
                ci_marked += 1
            else:
                poem["shelf"] = "ci300"
                poem["sort_key"] = sort_key
                poem_id = insert_poem(conn, poem)
                if poem_id:
                    ci_added += 1
                    ci_marked += 1
    print(f"宋词三百首 对上 {ci_marked} 首，补入 {ci_added} 首", flush=True)


def find_existing(conn, author: str, title: str, first: str) -> int | None:
    rows = conn.execute(
        "SELECT id, first_line FROM poems WHERE author_key = ? AND title_key = ?",
        (plain_key(author), plain_key(title)),
    ).fetchall()
    target = head(first)
    for row in rows:
        other = head(row["first_line"])
        if target[:8] and other[:8] and (target.startswith(other[:8]) or other.startswith(target[:8])):
            return row["id"]
    return None


# 诗库采用的文字和现在通行本不同。检索时两边都认，阅读页上注明。
KNOWN_VARIANTS = (
    {
        "author": "李白",
        "title": "静夜思",
        "note": "诗库作「看月光」「望山月」。通行本常作「明月光」「望明月」。",
        "alias": "床前明月光，疑是地上霜。举头望明月，低头思故乡。",
    },
)


TITLE_FIXES = (
    ("骆宾王", "在岳咏蝉", "在狱咏蝉"),
)


def apply_title_fixes(conn: sqlite3.Connection) -> None:
    for author, old, new in TITLE_FIXES:
        rows = conn.execute(
            "SELECT id, author, rhythmic, content FROM poems WHERE author = ? AND title = ?",
            (author, old),
        ).fetchall()
        for row in rows:
            conn.execute(
                "UPDATE poems SET title = ?, title_key = ? WHERE id = ?",
                (new, plain_key(new), row["id"]),
            )
            conn.execute("DELETE FROM poems_fts WHERE rowid = ?", (row["id"],))
            conn.execute(
                "INSERT INTO poems_fts(rowid, title, author, rhythmic, body) VALUES (?, ?, ?, ?, ?)",
                (row["id"], fts_doc(new), fts_doc(row["author"]), fts_doc(row["rhythmic"]), fts_doc(row["content"])),
            )
    conn.commit()


def apply_known_variants(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(poems)")}
    if "variant" not in columns:
        conn.execute("ALTER TABLE poems ADD COLUMN variant TEXT NOT NULL DEFAULT ''")
    for item in KNOWN_VARIANTS:
        rows = conn.execute(
            "SELECT id, title, author, rhythmic, content FROM poems WHERE author = ? AND title = ?",
            (item["author"], item["title"]),
        ).fetchall()
        for row in rows:
            conn.execute("UPDATE poems SET variant = ? WHERE id = ?", (item["note"], row["id"]))
            conn.execute("DELETE FROM poems_fts WHERE rowid = ?", (row["id"],))
            conn.execute(
                "INSERT INTO poems_fts(rowid, title, author, rhythmic, body) VALUES (?, ?, ?, ?, ?)",
                (
                    row["id"],
                    fts_doc(row["title"]),
                    fts_doc(row["author"]),
                    fts_doc(row["rhythmic"]),
                    fts_doc(row["content"] + "\n" + item["alias"]),
                ),
            )
    conn.commit()


def sanity(conn: sqlite3.Connection) -> None:
    print("—— 数量 ——", flush=True)
    for genre, count in conn.execute("SELECT genre, COUNT(*) FROM poems GROUP BY genre ORDER BY COUNT(*) DESC"):
        print(f"  {genre} {count}", flush=True)
    for name, query in (("静夜思", "静夜思"), ("床前明月光", "床前明月光"), ("关雎", "关雎")):
        match = fts_query(query)
        rows = conn.execute(
            """
            SELECT poems.title, poems.author FROM poems_fts
            JOIN poems ON poems.id = poems_fts.rowid
            WHERE poems_fts MATCH ?
            ORDER BY CASE WHEN poems.title_key = ? THEN 0 ELSE 1 END, bm25(poems_fts)
            LIMIT 3
            """,
            (match, plain_key(query)),
        ).fetchall()
        print(name, "->", [(row[0], row[1]) for row in rows], flush=True)
        if name == "静夜思" and not rows:
            raise SystemExit("检索自检失败：找不到静夜思")


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"找不到诗库原文：{SRC}")
    DB.parent.mkdir(parents=True, exist_ok=True)
    for extra in (DB, Path(str(DB) + "-wal"), Path(str(DB) + "-shm")):
        if extra.exists():
            extra.unlink()
    cc = OpenCC("t2s")
    print("读取选集…", flush=True)
    tang300, tang_items = load_tang300(cc)
    ci300 = load_ci300(cc)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -200000")
    conn.executescript(SCHEMA)
    total = 0
    for path in sorted((SRC / "全唐诗").glob("poet.tang.*.json"), key=file_number):
        total += ingest_file(conn, cc, path, "全唐诗", "唐", "诗", "", "", tang300)
    for path in sorted((SRC / "全唐诗").glob("poet.song.*.json"), key=file_number):
        total += ingest_file(conn, cc, path, "全宋诗", "宋", "诗", "", "", tang300)
    for path in sorted((SRC / "宋词").glob("ci.song.*.json"), key=file_number):
        total += ingest_file(conn, cc, path, "宋词", "宋", "词", "", "", {})
    total += ingest_file(conn, cc, SRC / "诗经" / "shijing.json", "诗经", "先秦", "诗经", "", "shijing", {})
    total += ingest_file(conn, cc, SRC / "楚辞" / "chuci.json", "楚辞", "先秦", "楚辞", "", "chuci", {})
    total += ingest_file(conn, cc, SRC / "元曲" / "yuanqu.json", "元曲", "元", "曲", "", "", {})
    total += ingest_file(conn, cc, SRC / "曹操诗集" / "caocao.json", "曹操诗集", "汉", "诗", "曹操", "", {})
    total += ingest_file(conn, cc, SRC / "纳兰性德" / "纳兰性德诗集.json", "纳兰性德", "清", "词", "纳兰性德", "", {})
    for path in sorted((SRC / "五代诗词").rglob("*.json")):
        if skip_file(path):
            continue
        total += ingest_file(conn, cc, path, "五代诗词", "五代", "词", "", "", {})
    print(f"写入 {total} 首，正在标记选集…", flush=True)
    conn.execute("CREATE INDEX idx_author_title ON poems(author_key, title_key)")
    conn.execute("CREATE INDEX idx_shelf ON poems(shelf, sort_key)")
    conn.execute("CREATE INDEX idx_genre ON poems(genre)")
    mark_anthologies(conn, tang_items, tang300, ci300)
    conn.execute("PRAGMA synchronous = NORMAL")
    apply_title_fixes(conn)
    apply_known_variants(conn)
    sanity(conn)
    conn.close()
    print(f"完成。数据库 {DB.stat().st_size / 1e6:.0f} MB", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("已中断")
