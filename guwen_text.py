"""检索用的汉字切分。诗库按字建索引，一个字也能搜。"""

import re


def is_hanzi(ch: str) -> bool:
    o = ord(ch)
    return (
        0x3400 <= o <= 0x4DBF
        or 0x4E00 <= o <= 0x9FFF
        or 0xF900 <= o <= 0xFAFF
        or 0x20000 <= o <= 0x2A6DF
    )


def plain_key(s: str) -> str:
    parts: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            parts.append("".join(buf))
            buf.clear()

    for ch in s or "":
        if is_hanzi(ch):
            flush()
            parts.append(ch)
        elif ch.isascii() and ch.isalnum():
            buf.append(ch.lower())
        else:
            flush()
    flush()
    return "".join(parts)


def fts_doc(s: str) -> str:
    parts: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            parts.append("".join(buf))
            buf.clear()

    for ch in s or "":
        if is_hanzi(ch):
            flush()
            parts.append(ch)
        elif ch.isascii() and ch.isalnum():
            buf.append(ch.lower())
        else:
            flush()
    flush()
    return " ".join(parts)


def fts_query(s: str) -> str | None:
    clauses: list[str] = []
    for raw in re.split(r"\s+", (s or "").strip()):
        doc = fts_doc(raw)
        if doc:
            clauses.append('"' + doc + '"')
    if not clauses:
        return None
    return " AND ".join(clauses)
