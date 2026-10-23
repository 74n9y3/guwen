#!/bin/zsh
cd "$(dirname "$0")"
DB="data/poems.db"

is_sqlite() {
  [[ -f "$DB" ]] || return 1
  [[ "$(head -c 15 "$DB" 2>/dev/null)" == "SQLite format 3" ]]
}

if is_sqlite; then
  echo "诗库已在 data/poems.db"
  exit 0
fi

mkdir -p data

if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git lfs version >/dev/null 2>&1; then
  echo "正在从 GitHub 下载已建好的诗库…"
  git lfs pull --include="data/poems.db"
  if is_sqlite; then
    echo "已保存到 data/poems.db"
    exit 0
  fi
fi

echo "没有现成诗库，改为下载原文并在本机生成。这一步需要联网，可能要几分钟。"
if [[ ! -d data/chinese-poetry/全唐诗 ]]; then
  rm -rf data/chinese-poetry
  git clone --depth 1 --filter=blob:none --sparse https://github.com/chinese-poetry/chinese-poetry.git data/chinese-poetry
  git -C data/chinese-poetry sparse-checkout set 全唐诗 宋词 诗经 楚辞 元曲 曹操诗集 纳兰性德 五代诗词
fi

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
.venv/bin/python import_poetry.py
