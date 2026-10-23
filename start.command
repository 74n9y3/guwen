#!/bin/zsh
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "正在准备运行环境…"
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
if [[ "$(head -c 15 data/poems.db 2>/dev/null)" != "SQLite format 3" ]]; then
  ./get-poems.command
fi
exec .venv/bin/python server.py
