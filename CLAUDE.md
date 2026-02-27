# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AACH登山データ抽出ツール — a Japanese mountain climbing record extraction tool. It has two interfaces:
- `mountain_extractor.py`: CLI tool for filtering and analyzing the CSV database
- `mountain_extractor.html`: Standalone browser-based version (no server needed; reads CSV via FileReader API)

The CSV data file is `AACH山行DB～2016年V1.2 - 山行一覧.csv`.

## Common Commands

```bash
# Show available mountain areas and seasons
python mountain_extractor.py list DATA.csv

# Extract records for a member (partial name match, prints to console)
python mountain_extractor.py personal DATA.csv "田中太郎"

# Extract + save to CSV + show analysis
python mountain_extractor.py personal DATA.csv "田中太郎" -o out.csv --analyze

# Extract by mountain area, season, or route keyword (AND logic for keywords)
python mountain_extractor.py condition DATA.csv -a 北アルプス -s 夏 -r 縦走 スキー -o out.csv --analyze
```

## Code Architecture

### `mountain_extractor.py`

Three CLI subcommands (`personal`, `condition`, `list`) each map to a `cmd_*` function.

Key functions:
- `load_csv()`: Tries multiple encodings (`utf-8-sig`, `utf-8`, `shift_jis`, `cp932`) to handle Excel-exported CSVs
- `save_csv()`: Writes BOM-attached UTF-8 (`utf-8-sig`) for Excel compatibility, outputting only `OUTPUT_COLUMNS`
- `extract_personal()`: Splits `メンバー` field on whitespace, normalizes each token with `normalize_name()`, then partial-matches
- `extract_condition()`: Filters by 山域 (exact), シーズン (exact), and ルート・特記事項 keywords (OR match)
- `normalize_name()`: Strips role prefixes like `L:` and parenthetical suffixes like `（CL）` from member tokens
- `analyze()`: Dispatches to `_analyze_*` helpers for bar-chart stats (seasonal, area, timeline, member co-occurrence, stagnation, route keywords, activity days)

### Member field format

The `メンバー` column uses space-separated tokens, each optionally prefixed with a role (e.g., `L:稲田昌植`) or suffixed with a parenthetical (e.g., `田中太郎（CL）`). `normalize_name()` strips these before matching.

### Output columns

`OUTPUT_COLUMNS = ['年度', '暦年', '開始日', '終了日', '行動', '停滞', 'メンバー', '山域', 'シーズン', 'ルート・特記事項', '出典']`

The input CSV has additional columns (`リンク`, `種別`) that are excluded from output.

### `mountain_extractor.html`

A self-contained single-file app — open directly in a browser, no server needed. Key architecture points:

- **CSV loading**: uses `FileReader.readAsText(file, 'utf-8')` — only UTF-8 is supported (unlike the Python tool's multi-encoding fallback). The BOM-prepended output from `save_csv()` is compatible.
- **State**: three module-level arrays — `allRecords`, `personalRecords`, `conditionRecords` — hold all data in memory.
- **App flow**: Step 1 loads CSV → Step 2 selects app mode (個人抽出 or 条件抽出) → results + analysis shown inline.
- **Results display**: capped at 100 rows on screen; full results exported via CSV download (BOM-prepended UTF-8, same column set as `OUTPUT_COLUMNS`).
- **Area/Season selects**: single-selection `<select>` dropdowns populated from the loaded data; no `multiple` attribute (unlike CLI's `-a`/`-s` which accept multiple values).
- **Route keyword search**: up to 5 keyword inputs, AND logic (`every(kw => route.includes(kw))`), matching the CLI `condition` subcommand.
- **Analysis**: rendered as inline HTML bar charts via `buildBarAnalysis()` and helper functions — mirrors the CLI `analyze()` themes but without the ASCII bar-chart style.
- **`normalizeName()`** in JS and **`normalize_name()`** in Python are equivalent — both strip `Role:` prefixes and `（suffix）` parentheticals.

### CLI/HTML behavioral differences

| Behavior | CLI (`mountain_extractor.py`) | HTML |
|---|---|---|
| CSV encoding | Auto-detects utf-8-sig / utf-8 / shift_jis / cp932 | UTF-8 only |
| Multiple areas/seasons | Multiple values via `-a`/`-s` flags | Single selection |
| Result display | All records printed to stdout | First 100 shown; full set in CSV download |
| Analysis output | ASCII bar chart to stdout | Inline HTML bar chart |
