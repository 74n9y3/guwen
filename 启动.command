#!/bin/zsh
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "正在准备运行环境…"
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
if [[ ! -f data/poems.db ]]; then
  echo "第一次使用，正在建立诗库，可能要几分钟…"
  .venv/bin/python import_poetry.py
fi
exec .venv/bin/python server.py
