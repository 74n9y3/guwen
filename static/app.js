const shelves = document.querySelector("#shelves")
const genres = document.querySelector("#genres")
const list = document.querySelector("#list")
const listMeta = document.querySelector("#listMeta")
const q = document.querySelector("#q")
const searchForm = document.querySelector("#searchForm")
const empty = document.querySelector("#empty")
const poemEl = document.querySelector("#poem")
const poemTitle = document.querySelector("#poemTitle")
const poemMeta = document.querySelector("#poemMeta")
const variant = document.querySelector("#variant")
const verse = document.querySelector("#verse")
const fav = document.querySelector("#fav")
const speak = document.querySelector("#speak")
const study = document.querySelector("#study")
const catalog = document.querySelector("#catalog")
const catalogBack = document.querySelector("#catalogBack")
const openCatalog = document.querySelector("#openCatalog")
const glyph = document.querySelector("#glyph")
const glyphChar = document.querySelector("#glyphChar")
const glyphReading = document.querySelector("#glyphReading")
const glyphNote = document.querySelector("#glyphNote")
const readHint = document.querySelector("#readHint")
const glyphLine = document.querySelector("#glyphLine")
const glyphMsg = document.querySelector("#glyphMsg")
const glyphInline = document.querySelector("#glyphInline")
const inlineLabel = document.querySelector("#inlineLabel")
const sensesLabel = document.querySelector("#sensesLabel")
const glyphSenses = document.querySelector("#glyphSenses")
const glyphWords = document.querySelector("#glyphWords")
const glyphUsed = document.querySelector("#glyphUsed")
const interpret = document.querySelector("#interpret")
const sideMsg = document.querySelector("#sideMsg")
const used = document.querySelector("#used")
const summary = document.querySelector("#summary")
const vernBlock = document.querySelector("#vernBlock")
const words = document.querySelector("#words")
const chat = document.querySelector("#chat")
const askForm = document.querySelector("#askForm")
const ask = document.querySelector("#ask")
const pyToggle = document.querySelector("#pyToggle")
const vernToggle = document.querySelector("#vernToggle")
const settings = document.querySelector("#settings")
const alts = document.querySelector("#alts")
const readingForm = document.querySelector("#readingForm")
const readingInput = document.querySelector("#readingInput")
const resetReading = document.querySelector("#resetReading")

const LANG_KEY = "guwen-lang"
const I18N = {
  zh: {
    catalog: "目录",
    searchPlaceholder: "搜题目、作者，或半句诗",
    pinyin: "拼音",
    vernacular: "白话",
    settings: "设置",
    langToggle: "English",
    emptyHint: "打开目录选一首，或在上面搜半句。",
    collapse: "收起",
    askPlaceholder: "问这句，或问一个词",
    askButton: "问",
    voiceReading: "男声 · 朗读",
    voiceClear: "男声 · 清楚",
    voiceYoung: "男声 · 年轻",
    rate: "语速",
    openStudy: "白话",
    foot: "原文来自开源诗库，已转简体。白话由你配置的 AI 现写。",
    close: "关闭",
    readingPlaceholder: "改读音",
    saveReading: "记住",
    resetReading: "恢复",
    inLine: "这一句里",
    senses: "文言里还常作",
    providersTitle: "免费接口",
    providersHint: "按这个顺序自动换。一家额度用完或连不上，就用下一家。密钥不在这个页面上。",
    shelf_tang300: "唐诗三百首",
    shelf_ci300: "宋词三百首",
    shelf_shijing: "诗经",
    shelf_chuci: "楚辞",
    shelf_fav: "收藏",
    genre_all: "全部",
    genre_诗: "诗",
    genre_词: "词",
    genre_诗经: "诗经",
    genre_楚辞: "楚辞",
    genre_曲: "曲",
    count: (n) => n + " 首",
    noResults: "没有这首。可以少几个字，或在作者和诗题之间空一格。",
    limited: (n) => n + " 首，先显示这些。句子再写完整一点会更准。",
    emptyList: "这里还是空的。",
    fav: "收藏",
    faved: "已收藏",
    used: (name) => "这一次用的是 " + name,
    interpret: "用白话讲一遍",
    interpretAgain: "再讲一遍",
    clipped: "只讲了开头。",
    userPrefix: "问  ",
    noReadings: "没有现成读音，可以自己填。",
    noPinyin: "无注音",
    lookingUp: "正在查这个字…",
    glossFrom: (name) => "查自 " + name,
    speak: "朗读",
    stop: "停止",
    preparing: "正在准备朗读…",
    playFailed: "没有播出来",
    speakFailed: "没有读出来",
    rateSlow: "慢",
    rateSlower: "稍慢",
    rateNormal: "正常",
    rateFaster: "稍快",
    interpreting: "正在读这首…",
    thinking: "正在想…",
    noProviders: "没有读到可用的免费接口。",
    requestFailed: "请求失败",
    customProvider: "自备接口",
    readNotes: "注意读音",
    checkingReadings: "正在请 AI 核对多音字…",
    readingNote: (note) => "读音：" + note,
  },
  en: {
    catalog: "Contents",
    searchPlaceholder: "Search title, author, or part of a line (in Chinese)",
    pinyin: "Pinyin",
    vernacular: "Translation",
    settings: "Settings",
    langToggle: "中文",
    emptyHint: "Open Contents to pick a poem, or search for part of a line above.",
    collapse: "Hide",
    askPlaceholder: "Ask about a line or a word",
    askButton: "Ask",
    voiceReading: "Male · Recital",
    voiceClear: "Male · Clear",
    voiceYoung: "Male · Young",
    rate: "Speed",
    openStudy: "Explain",
    foot: "Texts come from an open-source poetry corpus, converted to simplified Chinese. Explanations are written on the fly by the AI you configure.",
    close: "Close",
    readingPlaceholder: "Fix pinyin",
    saveReading: "Save",
    resetReading: "Reset",
    inLine: "In this line",
    senses: "Other classical senses",
    providersTitle: "AI providers",
    providersHint: "Tried in this order. If one runs out of quota or can't be reached, the next one is used. API keys are never shown here.",
    shelf_tang300: "300 Tang Poems",
    shelf_ci300: "300 Song Ci",
    shelf_shijing: "Book of Songs",
    shelf_chuci: "Songs of Chu",
    shelf_fav: "Favorites",
    genre_all: "All",
    genre_诗: "Shi",
    genre_词: "Ci",
    genre_诗经: "Book of Songs",
    genre_楚辞: "Songs of Chu",
    genre_曲: "Qu",
    count: (n) => n + (n === 1 ? " poem" : " poems"),
    noResults: "No match. Try fewer characters, or put a space between author and title.",
    limited: (n) => "Showing the first " + n + ". A longer phrase gives better matches.",
    emptyList: "Nothing here yet.",
    fav: "Favorite",
    faved: "Favorited",
    used: (name) => "Answered by " + name,
    interpret: "Explain in English",
    interpretAgain: "Explain again",
    clipped: "Only the beginning is explained. ",
    userPrefix: "Q  ",
    noReadings: "No known readings; type one yourself.",
    noPinyin: "No pinyin",
    lookingUp: "Looking up this character…",
    glossFrom: (name) => "From " + name,
    speak: "Read aloud",
    stop: "Stop",
    preparing: "Preparing audio…",
    playFailed: "Playback failed",
    speakFailed: "Could not read aloud",
    rateSlow: "Slow",
    rateSlower: "Slower",
    rateNormal: "Normal",
    rateFaster: "Faster",
    interpreting: "Reading the poem…",
    thinking: "Thinking…",
    noProviders: "No AI provider is configured.",
    requestFailed: "Request failed",
    customProvider: "Custom API",
    readNotes: "Watch the pronunciation",
    checkingReadings: "Asking the AI to check characters with several readings…",
    readingNote: (note) => "Pronunciation: " + note,
  },
}

let lang = initialLang()

function initialLang() {
  const saved = localStorage.getItem(LANG_KEY)
  if (saved === "zh" || saved === "en") return saved
  return /^zh/i.test(navigator.language || "") ? "zh" : "en"
}

function t(key, ...args) {
  const value = I18N[lang][key] ?? I18N.zh[key] ?? key
  return typeof value === "function" ? value(...args) : value
}

const SHELVES = ["tang300", "ci300", "shijing", "chuci", "fav"]
const GENRES = ["", "诗", "词", "诗经", "楚辞", "曲"]

let shelf = "tang300"
let genre = ""
let browsing = true
let currentId = 0
let current = null
let popRuby = null
let selected = null
let glossTicket = 0
let speakToken = 0
let timer = 0
let composing = false

function post(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}), "X-Lang": lang }
  const response = await fetch(path, { ...options, headers })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || t("requestFailed"))
  return data
}

function paintShelves() {
  shelves.replaceChildren()
  for (const id of SHELVES) {
    const button = document.createElement("button")
    button.type = "button"
    button.className = "chip" + (browsing && shelf === id ? " on" : "")
    button.dataset.shelf = id
    button.textContent = t("shelf_" + id)
    button.addEventListener("click", () => selectShelf(id))
    shelves.append(button)
  }
}

function paintGenres() {
  genres.replaceChildren()
  for (const id of GENRES) {
    const button = document.createElement("button")
    button.type = "button"
    button.className = "chip" + (genre === id ? " on" : "")
    button.textContent = t("genre_" + (id || "all"))
    button.addEventListener("click", () => {
      genre = id
      paintGenres()
      const query = q.value.trim()
      if (query) search(query)
    })
    genres.append(button)
  }
}

function selectShelf(next) {
  shelf = next
  browsing = true
  genre = ""
  q.value = ""
  genres.hidden = true
  paintShelves()
  paintGenres()
  loadShelf(shelf)
}

async function loadShelf(name) {
  const data = await api("/api/browse?shelf=" + encodeURIComponent(name))
  shelf = data.shelf
  browsing = true
  paintShelves()
  listMeta.textContent = t("shelf_" + data.shelf) + " · " + t("count", data.items.length)
  renderList(data.items)
}

async function search(query) {
  browsing = false
  genres.hidden = false
  paintShelves()
  paintGenres()
  const data = await api("/api/search?q=" + encodeURIComponent(query) + "&genre=" + encodeURIComponent(genre))
  if (!data.items.length) {
    listMeta.textContent = t("noResults")
  } else if (data.limited) {
    listMeta.textContent = t("limited", data.items.length)
  } else {
    listMeta.textContent = t("count", data.items.length)
  }
  renderList(data.items)
}

function renderList(items) {
  list.replaceChildren()
  if (!items.length) {
    const note = document.createElement("p")
    note.className = "list-meta"
    note.textContent = t("emptyList")
    list.append(note)
    return
  }
  for (const item of items) {
    const button = document.createElement("button")
    button.type = "button"
    button.className = "item"
    button.dataset.id = String(item.id)
    const title = document.createElement("strong")
    title.textContent = item.title
    const meta = document.createElement("span")
    meta.className = "meta"
    meta.textContent = [item.author, item.dynasty, item.genre].filter(Boolean).join(" · ")
    const first = document.createElement("span")
    first.className = "first"
    first.textContent = item.first || ""
    button.append(title, meta, first)
    button.addEventListener("click", () => openPoem(item.id))
    list.append(button)
  }
  markActive()
}

function markActive() {
  for (const button of list.querySelectorAll(".item")) {
    button.classList.toggle("on", Number(button.dataset.id) === currentId)
  }
  const active = list.querySelector(".item.on")
  if (active) active.scrollIntoView({ block: "nearest" })
}

function metaLine(poem) {
  const tune = poem.rhythmic && poem.rhythmic !== poem.title ? poem.rhythmic : ""
  const section = poem.section && poem.section !== poem.title ? poem.section : ""
  return [poem.dynasty, poem.author, poem.genre, tune, section].filter(Boolean).join(" · ")
}

function displayRows(tokens) {
  const rows = []
  let buf = []
  let han = 0
  for (const token of tokens) {
    buf.push(token)
    if (token.han) han += 1
    if (/[，。！？；]/.test(token.t) && han >= 2) {
      rows.push(buf)
      buf = []
      han = 0
    }
  }
  if (buf.length) rows.push(buf)
  return rows.length ? rows : [tokens]
}

function renderPoem(poem) {
  empty.hidden = true
  poemEl.hidden = false
  document.querySelector("#poemTools").hidden = false
  poemMeta.textContent = metaLine(poem)
  variant.hidden = !poem.variant
  variant.textContent = poem.variant || ""
  fav.textContent = poem.favorite ? t("faved") : t("fav")
  fav.classList.toggle("on", poem.favorite)
  renderText(poem)
  renderSide(poem)
  applyNote(poem.note)
}

function rubyFor(token) {
  const ruby = document.createElement("ruby")
  ruby.classList.toggle("ai", Boolean(token.ai))
  ruby.append(token.t)
  const rt = document.createElement("rt")
  rt.textContent = token.p || ""
  ruby.append(rt)
  return ruby
}

function paintReadHint(poem) {
  readHint.replaceChildren()
  const notes = poem.reading_notes || []
  readHint.hidden = !notes.length
  if (!notes.length) return
  const label = document.createElement("span")
  label.textContent = t("readNotes")
  readHint.append(label)
  for (const item of notes) {
    const chip = document.createElement("button")
    chip.type = "button"
    chip.className = "read-chip" + (item.changed ? " changed" : "")
    chip.textContent = item.char + " " + item.reading
    chip.title = item.note || ""
    if (item.line >= 0) chip.addEventListener("click", () => showGlyph(item.line, item.offset))
    else chip.disabled = true
    readHint.append(chip)
  }
}

function renderText(poem) {
  poemTitle.replaceChildren()
  for (const token of poem.title_tokens || [{ t: poem.title, p: "", han: false }]) {
    if (!token.han) {
      const plain = document.createElement("span")
      plain.className = "title-plain"
      plain.textContent = token.t
      poemTitle.append(plain)
      continue
    }
    poemTitle.append(rubyFor(token))
  }
  paintReadHint(poem)
  verse.replaceChildren()
  poem.lines.forEach((line, lineNo) => {
    displayRows(line.tokens).forEach((tokens, part) => {
      const row = document.createElement("div")
      row.className = "row" + (part === 0 ? " stanza" : "")
      row.dataset.line = String(lineNo)
      row.dataset.part = String(part)
      const orig = document.createElement("p")
      orig.className = "orig"
      for (const token of tokens) {
        if (!token.han) {
          const punct = document.createElement("span")
          punct.className = "punct"
          punct.textContent = token.t
          orig.append(punct)
          continue
        }
        const ruby = rubyFor(token)
        ruby.dataset.offset = String(token.i)
        ruby.dataset.fixed = token.fixed ? "1" : "0"
        orig.append(ruby)
      }
      const vern = document.createElement("p")
      vern.className = "vern"
      vern.hidden = true
      row.append(orig, vern)
      verse.append(row)
    })
  })
}

const readingChecks = new Set()

async function checkReadings(poem) {
  if (poem.readings_checked || readingChecks.has(poem.id)) return
  readingChecks.add(poem.id)
  readHint.hidden = false
  readHint.textContent = t("checkingReadings")
  const asked = lang
  try {
    const fresh = await post("/api/check-readings", { id: poem.id })
    if (!current || current.id !== fresh.id) return
    if (lang !== asked) {
      openPoem(fresh.id)
      return
    }
    current.title_tokens = fresh.title_tokens
    current.lines = fresh.lines
    current.reading_notes = fresh.reading_notes
    current.readings_checked = true
    renderText(current)
    applyNote(current.note)
    if (selected) {
      markGlyph(selected.line, selected.offset)
      paintGlyphReading(selected.line, selected.offset)
      placeGlyph()
    }
  } catch {
    if (current && current.id === poem.id) paintReadHint(current)
  }
}

function renderSide(poem) {
  sideMsg.textContent = ""
  used.textContent = poem.note && poem.note.provider ? t("used", poem.note.provider) : ""
  chat.replaceChildren()
  for (const message of poem.messages || []) {
    appendMessage(message.role, message.content)
  }
  interpret.textContent = poem.note ? t("interpretAgain") : t("interpret")
  interpret.disabled = false
}

function applyNote(note) {
  const rows = [...verse.querySelectorAll(".row")]
  for (const row of rows) {
    const vern = row.querySelector(".vern")
    vern.textContent = ""
    vern.hidden = true
  }
  vernBlock.replaceChildren()
  vernBlock.hidden = true
  summary.hidden = true
  words.replaceChildren()
  vernToggle.disabled = true
  if (!note) return
  const covered = note.covered || 0
  const aligned = note.lines && note.lines.length > 0 && note.lines.length === covered
  if (aligned) {
    const lastOfLine = new Map()
    for (const row of rows) lastOfLine.set(Number(row.dataset.line), row)
    for (const [index, text] of note.lines.entries()) {
      const row = lastOfLine.get(index)
      if (!row || !text) continue
      const vern = row.querySelector(".vern")
      vern.textContent = text
      vern.hidden = false
    }
    vernToggle.disabled = false
  } else if (note.lines && note.lines.length) {
    for (const text of note.lines) {
      const paragraph = document.createElement("p")
      paragraph.textContent = text
      vernBlock.append(paragraph)
    }
    vernBlock.hidden = false
    vernToggle.disabled = false
  }
  if (note.summary) {
    const prefix = note.clipped ? t("clipped") : ""
    summary.textContent = prefix + note.summary
    summary.hidden = false
  }
  for (const item of note.words || []) {
    const term = document.createElement("dt")
    term.textContent = item.word
    const gloss = document.createElement("dd")
    gloss.textContent = item.note
    words.append(term, gloss)
  }
}

function appendMessage(role, content) {
  const block = document.createElement("div")
  block.className = "bubble " + role
  block.textContent = role === "user" ? t("userPrefix") + content : content
  chat.append(block)
}

async function openPoem(id) {
  try {
    const poem = await api("/api/poem?id=" + id)
    const scroller = document.querySelector(".read")
    const keepScroll = currentId === poem.id
    const top = scroller.scrollTop
    const switched = currentId !== poem.id
    currentId = poem.id
    current = poem
    document.title = poem.title + " · 古文"
    stopSpeak()
    renderPoem(poem)
    clearGlyph()
    if (switched) study.hidden = true
    setCatalog(false)
    if (keepScroll) scroller.scrollTop = top
    else scroller.scrollTop = 0
    const next = "#p=" + poem.id
    if (location.hash !== next) history.replaceState(null, "", next)
    markActive()
    checkReadings(poem)
  } catch (error) {
    listMeta.textContent = error.message
  }
}

function runQuery() {
  const query = q.value.trim()
  if (!query) {
    genres.hidden = true
    browsing = true
    loadShelf(shelf)
    return
  }
  search(query)
}

verse.addEventListener("click", (event) => {
  const ruby = event.target.closest("ruby")
  if (!ruby || !current) return
  const row = ruby.closest(".row")
  showGlyph(Number(row.dataset.line), Number(ruby.dataset.offset))
})

function clearGlyph() {
  glossTicket += 1
  selected = null
  popRuby = null
  glyph.hidden = true
}

function placeGlyph() {
  if (glyph.hidden || !popRuby) return
  const rect = popRuby.getBoundingClientRect()
  const margin = 12
  const width = glyph.offsetWidth
  const height = glyph.offsetHeight
  let left = rect.left + rect.width / 2 - width / 2
  left = Math.max(margin, Math.min(left, window.innerWidth - width - margin))
  let top = rect.bottom + 10
  if (top + height > window.innerHeight - margin) {
    const above = rect.top - height - 10
    top = above >= margin ? above : margin
  }
  glyph.style.left = left + "px"
  glyph.style.top = top + "px"
}

function setCatalog(open) {
  catalog.hidden = !open
  catalogBack.hidden = !(open && current)
  openCatalog.classList.toggle("on", open)
}

function markGlyph(lineNo, offset) {
  for (const ruby of verse.querySelectorAll("ruby")) {
    const row = ruby.closest(".row")
    const on = Number(row.dataset.line) === lineNo && Number(ruby.dataset.offset) === offset
    ruby.classList.toggle("on", on)
    if (on) popRuby = ruby
  }
}

async function loadReadings(char, currentReading, ticket) {
  alts.replaceChildren()
  try {
    const data = await api("/api/readings?c=" + encodeURIComponent(char))
    if (ticket !== glossTicket) return
    for (const reading of data.readings) {
      const button = document.createElement("button")
      button.type = "button"
      button.textContent = reading
      button.classList.toggle("on", reading === currentReading)
      button.addEventListener("click", () => saveReading(reading))
      alts.append(button)
    }
    if (!data.readings.length) {
      const note = document.createElement("span")
      note.textContent = t("noReadings")
      alts.append(note)
    }
  } catch (error) {
    if (ticket !== glossTicket) return
    alts.textContent = error.message
  }
}

function paintGlyphReading(lineNo, offset) {
  const line = current.lines[lineNo]
  const token = line && line.tokens.find((item) => item.i === offset)
  if (!token) return
  glyphReading.textContent = token.p || t("noPinyin")
  const note = (current.reading_notes || []).find((item) => item.line === lineNo && item.offset === offset)
  glyphNote.textContent = note && note.note ? t("readingNote", note.note) : ""
  glyphNote.hidden = !glyphNote.textContent
}

async function showGlyph(lineNo, offset) {
  const line = current.lines[lineNo]
  const token = line && line.tokens.find((item) => item.i === offset)
  if (!token || !token.han) return
  const ticket = ++glossTicket
  selected = { line: lineNo, offset }
  glyph.hidden = false
  glyphChar.textContent = token.t
  paintGlyphReading(lineNo, offset)
  glyphLine.textContent = line.tokens.map((item) => item.t).join("")
  glyphMsg.textContent = t("lookingUp")
  glyphInline.textContent = ""
  glyphInline.hidden = true
  inlineLabel.hidden = true
  sensesLabel.hidden = true
  glyphSenses.replaceChildren()
  glyphWords.replaceChildren()
  glyphUsed.textContent = ""
  resetReading.hidden = !token.fixed
  readingInput.value = ""
  markGlyph(lineNo, offset)
  placeGlyph()
  loadReadings(token.t, token.p, ticket)
  try {
    const data = await post("/api/gloss", { id: current.id, line: lineNo, offset })
    if (ticket !== glossTicket) return
    glyphMsg.textContent = ""
    glyphInline.textContent = data.in_line || ""
    glyphInline.hidden = !data.in_line
    inlineLabel.hidden = !data.in_line
    sensesLabel.hidden = !(data.senses && data.senses.length)
    for (const sense of data.senses || []) {
      const item = document.createElement("li")
      item.textContent = sense
      glyphSenses.append(item)
    }
    for (const item of data.words || []) {
      const term = document.createElement("dt")
      term.textContent = item.word
      const note = document.createElement("dd")
      note.textContent = item.note || ""
      glyphWords.append(term, note)
    }
    glyphUsed.textContent = data.provider ? t("glossFrom", data.provider) : ""
  } catch (error) {
    if (ticket !== glossTicket) return
    glyphMsg.textContent = error.message
  }
  placeGlyph()
}

async function saveReading(reading) {
  if (!current || !selected) return
  const lineNo = selected.line
  const offset = selected.offset
  const scroller = document.querySelector(".read")
  const top = scroller.scrollTop
  const poem = await post("/api/reading", {
    id: current.id,
    line: lineNo,
    offset,
    reading,
  })
  current = poem
  currentId = poem.id
  renderPoem(poem)
  scroller.scrollTop = top
  showGlyph(lineNo, offset)
}

readingForm.addEventListener("submit", (event) => {
  event.preventDefault()
  if (readingInput.value.trim()) saveReading(readingInput.value.trim())
})

resetReading.addEventListener("click", () => saveReading(""))

const VOICE_KEY = "guwen-voice"
const RATE_KEY = "guwen-rate"
const VOICE_ORDER = ["Shelley", "Flo", "Sandy", "Reed", "Eddy", "Rocko", "Grandma", "Grandpa", "Tingting", "Meijia", "Sinji"]
const VOICE_LABELS = {
  Shelley: "女声 · 清",
  Flo: "女声 · 柔",
  Sandy: "女声 · 亮",
  Grandma: "年长女声",
  Eddy: "男声 · 清",
  Reed: "男声 · 沉",
  Rocko: "男声 · 厚",
  Grandpa: "年长男声",
  Tingting: "婷婷",
  Meijia: "美佳",
  Sinji: "善怡",
}

function voiceRank(voice) {
  const index = VOICE_ORDER.findIndex((name) => voice.name.startsWith(name))
  return index === -1 ? 40 : index
}

function zhVoices() {
  if (!window.speechSynthesis) return []
  const voices = speechSynthesis.getVoices().filter((voice) => voice.lang && voice.lang.toLowerCase().replace("_", "-").startsWith("zh"))
  const mainland = voices.filter((voice) => /zh-cn/i.test(voice.lang.replace("_", "-")) || /china mainland/i.test(voice.name))
  const pool = mainland.length ? mainland : voices
  const seen = new Set()
  const unique = []
  for (const voice of pool) {
    const key = voice.name + "|" + voice.lang
    if (seen.has(key)) continue
    seen.add(key)
    unique.push(voice)
  }
  unique.sort((a, b) => voiceRank(a) - voiceRank(b) || a.name.localeCompare(b.name))
  return unique
}

function voiceLabel(voice) {
  const name = voice.name.split(" ")[0]
  const place = /taiwan/i.test(voice.name) || /zh-tw/i.test(voice.lang.replace("_", "-")) ? " · 台湾" : ""
  return (VOICE_LABELS[name] || name) + place
}

function paintVoices() {
  const pick = document.querySelector("#voicePick")
  const voices = zhVoices()
  const saved = localStorage.getItem(VOICE_KEY)
  pick.replaceChildren()
  for (const voice of voices) {
    const option = document.createElement("option")
    option.value = voice.name + "|" + voice.lang
    option.textContent = voiceLabel(voice)
    pick.append(option)
  }
  pick.hidden = voices.length < 2
  if (!voices.length) return
  const chosen = voices.find((voice) => voice.name + "|" + voice.lang === saved) || voices[0]
  pick.value = chosen.name + "|" + chosen.lang
}

function chosenVoice() {
  const voices = zhVoices()
  const pick = document.querySelector("#voicePick")
  return voices.find((voice) => voice.name + "|" + voice.lang === pick.value) || voices[0] || null
}

let liveUtterance = null
let keepAlive = 0

let player = null
let playerUrl = ""

function stopSpeak() {
  speakToken += 1
  clearInterval(keepAlive)
  liveUtterance = null
  if (player) {
    player.pause()
    player.src = ""
    player = null
  }
  if (playerUrl) {
    URL.revokeObjectURL(playerUrl)
    playerUrl = ""
  }
  if (window.speechSynthesis) speechSynthesis.cancel()
  speak.classList.remove("on")
  speak.textContent = t("speak")
  for (const row of verse.querySelectorAll(".row.on-read")) row.classList.remove("on-read")
}

function armKeepAlive(token) {
  clearInterval(keepAlive)
  keepAlive = setInterval(() => {
    if (token !== speakToken) {
      clearInterval(keepAlive)
      return
    }
    if (speechSynthesis.paused || speechSynthesis.speaking) speechSynthesis.resume()
  }, 3000)
}

function speakPoem() {
  if (!current) return
  const speakMsg = document.querySelector("#speakMsg")
  if (speak.classList.contains("on")) {
    stopSpeak()
    speakMsg.textContent = ""
    return
  }
  const token = ++speakToken
  const audio = new Audio()
  player = audio
  audio.src = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
  audio.play().catch(() => {})
  speak.classList.add("on")
  speak.textContent = t("stop")
  speakMsg.textContent = t("preparing")
  const voice = document.querySelector("#voicePick").value
  post("/api/speak", { id: current.id, voice })
    .then((data) => {
      if (token !== speakToken) return
      const binary = atob(data.audio)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i)
      playerUrl = URL.createObjectURL(new Blob([bytes], { type: data.mime || "audio/mpeg" }))
      const marks = data.marks || []
      audio.src = playerUrl
      audio.preservesPitch = true
      audio.playbackRate = speechRate()
      audio.ontimeupdate = () => {
        if (token !== speakToken) return
        let piece = null
        for (const mark of marks) {
          if (mark.t <= audio.currentTime + 0.05) piece = mark
          else break
        }
        markSpoken(piece)
      }
      audio.onended = () => {
        if (token !== speakToken) return
        stopSpeak()
        speakMsg.textContent = ""
      }
      audio.onerror = () => {
        if (token !== speakToken) return
        stopSpeak()
        speakMsg.textContent = t("playFailed")
      }
      speakMsg.textContent = ""
      return audio.play()
    })
    .catch((error) => {
      if (token !== speakToken) return
      stopSpeak()
      speakMsg.textContent = error.message || t("speakFailed")
    })
}

function markSpoken(piece) {
  for (const row of verse.querySelectorAll(".row.on-read")) row.classList.remove("on-read")
  if (!piece || piece.line < 0) return
  const row = verse.querySelector('.row[data-line="' + piece.line + '"][data-part="' + piece.part + '"]')
  if (!row) return
  row.classList.add("on-read")
  row.scrollIntoView({ block: "nearest" })
}

speak.addEventListener("click", speakPoem)
document.querySelector("#voicePick").addEventListener("change", () => {
  localStorage.setItem(VOICE_KEY, document.querySelector("#voicePick").value)
  if (speak.classList.contains("on")) stopSpeak()
})
{
  const pick = document.querySelector("#voicePick")
  const saved = localStorage.getItem(VOICE_KEY)
  if (saved && [...pick.options].some((option) => option.value === saved)) pick.value = saved
}

function speechRate() {
  const value = Number(document.querySelector("#ratePick").value)
  if (!Number.isFinite(value)) return 0.85
  return Math.min(1.2, Math.max(0.7, value / 100))
}

function rateWord(rate) {
  if (rate <= 0.75) return t("rateSlow")
  if (rate <= 0.9) return t("rateSlower")
  if (rate < 1.1) return t("rateNormal")
  return t("rateFaster")
}

function paintRate() {
  const rate = speechRate()
  document.querySelector("#rateLabel").textContent = rateWord(rate)
}

document.querySelector("#ratePick").addEventListener("input", () => {
  localStorage.setItem(RATE_KEY, document.querySelector("#ratePick").value)
  paintRate()
  if (player && player.src && !player.src.startsWith("data:")) player.playbackRate = speechRate()
})
{
  const savedRate = Number(localStorage.getItem(RATE_KEY))
  const pick = document.querySelector("#ratePick")
  if (savedRate >= 70 && savedRate <= 120) pick.value = String(savedRate)
  paintRate()
}

document.querySelector("#openStudy").addEventListener("click", () => {
  study.hidden = false
})
document.querySelector("#closeStudy").addEventListener("click", () => {
  study.hidden = true
})
document.querySelector("#closeGlyph").addEventListener("click", () => clearGlyph())

document.addEventListener("click", (event) => {
  if (glyph.hidden) return
  if (glyph.contains(event.target) || event.target.closest("ruby, .read-chip")) return
  clearGlyph()
})

document.querySelector(".read").addEventListener("scroll", () => {
  if (!glyph.hidden) placeGlyph()
})

openCatalog.addEventListener("click", () => setCatalog(catalog.hidden))
catalogBack.addEventListener("click", () => setCatalog(false))

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (!glyph.hidden) clearGlyph()
    else if (speak.classList.contains("on")) stopSpeak()
    else if (!catalog.hidden && current) setCatalog(false)
    return
  }
  if (event.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
    event.preventDefault()
    q.focus()
  }
})

fav.addEventListener("click", async () => {
  if (!current) return
  try {
    const data = await post("/api/favorite", { id: current.id })
    current.favorite = data.favorite
    fav.textContent = data.favorite ? t("faved") : t("fav")
    fav.classList.toggle("on", data.favorite)
    if (shelf === "fav" && browsing) loadShelf("fav")
  } catch (error) {
    sideMsg.textContent = error.message
  }
})

interpret.addEventListener("click", async () => {
  if (!current || interpret.disabled) return
  interpret.disabled = true
  sideMsg.textContent = t("interpreting")
  try {
    const data = await post("/api/interpret", { id: current.id, refresh: Boolean(current.note) })
    current.note = data.note
    interpret.textContent = t("interpretAgain")
    sideMsg.textContent = ""
    used.textContent = data.note && data.note.provider ? t("used", data.note.provider) : ""
    applyNote(current.note)
  } catch (error) {
    sideMsg.textContent = error.message
  } finally {
    interpret.disabled = false
  }
})

askForm.addEventListener("submit", async (event) => {
  event.preventDefault()
  if (!current) return
  const question = ask.value.trim()
  if (!question) return
  sideMsg.textContent = t("thinking")
  try {
    const data = await post("/api/ask", { id: current.id, question })
    appendMessage("user", question)
    appendMessage("assistant", data.answer)
    ask.value = ""
    sideMsg.textContent = ""
    if (data.provider) used.textContent = t("used", data.provider)
  } catch (error) {
    sideMsg.textContent = error.message
  }
})

pyToggle.addEventListener("change", () => {
  document.body.classList.toggle("show-py", pyToggle.checked)
})

vernToggle.addEventListener("change", () => {
  document.body.classList.toggle("show-vern", vernToggle.checked)
})

document.querySelector("#home").addEventListener("click", () => setCatalog(true))

q.addEventListener("focus", () => setCatalog(true))

searchForm.addEventListener("submit", (event) => {
  event.preventDefault()
  runQuery()
})

q.addEventListener("compositionstart", () => {
  composing = true
})

q.addEventListener("compositionend", () => {
  composing = false
  runQuery()
})

q.addEventListener("input", () => {
  setCatalog(true)
  if (composing) return
  clearTimeout(timer)
  timer = setTimeout(runQuery, 220)
})

empty.addEventListener("click", (event) => {
  const button = event.target.closest("[data-q]")
  if (!button) return
  q.value = button.dataset.q
  setCatalog(true)
  runQuery()
})

document.querySelector("#openSettings").addEventListener("click", async () => {
  const settingsMsg = document.querySelector("#settingsMsg")
  const list = document.querySelector("#providerList")
  settingsMsg.textContent = ""
  list.replaceChildren()
  try {
    const data = await api("/api/settings")
    for (const item of data.providers || []) {
      const row = document.createElement("li")
      const name = item.name === I18N.zh.customProvider ? t("customProvider") : item.name
      row.textContent = name + " · " + item.model
      list.append(row)
    }
    if (!data.providers || !data.providers.length) settingsMsg.textContent = t("noProviders")
  } catch (error) {
    settingsMsg.textContent = error.message
  }
  settings.showModal()
})

document.querySelector("#closeSettings").addEventListener("click", () => settings.close())

function paintStatic() {
  document.documentElement.lang = lang === "en" ? "en" : "zh-Hans"
  for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = t(el.dataset.i18n)
  for (const el of document.querySelectorAll("[data-i18n-placeholder]")) el.placeholder = t(el.dataset.i18nPlaceholder)
  for (const el of document.querySelectorAll("[data-i18n-aria-label]")) el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel))
  const toggle = document.querySelector("#langToggle")
  toggle.textContent = t("langToggle")
  toggle.lang = lang === "en" ? "zh-Hans" : "en"
  if (!speak.classList.contains("on")) speak.textContent = t("speak")
  if (!current) interpret.textContent = t("interpret")
  paintRate()
  paintShelves()
  paintGenres()
}

document.querySelector("#langToggle").addEventListener("click", () => {
  lang = lang === "en" ? "zh" : "en"
  localStorage.setItem(LANG_KEY, lang)
  clearGlyph()
  paintStatic()
  runQuery()
  if (current) openPoem(current.id)
})

paintStatic()
setCatalog(true)
loadShelf("tang300").then(() => {
  const id = Number((location.hash.match(/p=(\d+)/) || [])[1] || 0)
  if (id) openPoem(id)
})

window.addEventListener("hashchange", () => {
  const id = Number((location.hash.match(/p=(\d+)/) || [])[1] || 0)
  if (id && id !== currentId) openPoem(id)
})
