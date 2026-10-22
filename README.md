# 古文

在自己电脑上读唐诗、宋诗、宋词和其他古文。可以搜索、看拼音、点一个字看解释，也可以让男声把一首诗读出来。

打开方式：双击 `启动.command`，或在项目目录运行：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python server.py
```

浏览器打开 http://127.0.0.1:8765 。诗库 `data/poems.db` 用 Git LFS 存放，克隆后如果读不到诗，先执行 `git lfs pull`。

## 致谢

原文来自开源项目 [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)（最全中文诗歌古典文集数据库）。感谢 [JackeyGao](https://github.com/jackeygao) 和所有贡献者把这些诗整理成可以拿来用的 JSON。这个阅读器只是在那份数据上做了简体转换、检索和阅读；诗句本身不是这里写的。

该数据集以 MIT 许可证发布：

> Copyright (c) 2016 JackeyGao
>
> 许可全文见 [chinese-poetry/LICENSE](https://github.com/chinese-poetry/chinese-poetry/blob/master/LICENSE)。

目前收进本库的有：全唐诗、全宋诗、全宋词、诗经、楚辞、元曲、曹操诗集、纳兰性德、五代诗词，以及唐诗三百首、宋词三百首的篇目。论语、四书五经、蒙学等其他文集没有导入。

## 白话和朗读

点字解释、整首白话，会用你自己在本机 `.env` 里配置的接口。这个文件不会提交。可以写入这些名字：

`BAI_API_KEY`、`GROQ_API_KEY`、`NVIDIA_API_KEY`、`OPENROUTER_API_KEY`、`GEMINI_API_KEY`、`CEREBRAS_API_KEY`、`SAMBANOVA_API_KEY`，以及对应的 `*_MODEL`、`*_BASE_URL`。换用顺序写在 `LLM_FREE_ORDER`。

朗读用的是微软的中文神经语音。第一次读一首诗需要联网，声音生成后缓存在 `data/speech/`，这份缓存也不提交。语速在播放时本地调整。
