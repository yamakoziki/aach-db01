# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Japanese mountain climbing data extraction tool (`mountain_extractor.py`) that processes CSV files containing historical mountain climbing records. The tool extracts records for specific members from a comprehensive climbing database.

## Common Commands

### Running the Tool
```bash
# Extract records for a specific member (output to console)
python mountain_extractor.py AACHV1.0.csv "メンバー名"

# Extract records and save to CSV file
python mountain_extractor.py AACHV1.0.csv "メンバー名" -o output_file.csv
```

### Testing
```bash
# Test with sample data
python mountain_extractor.py AACHV1.0.csv "稲田昌植"
```

## Data Structure

### Input CSV Columns (Required)
- 年度 (Fiscal Year)
- 暦年 (Calendar Year) 
- 開始日 (Start Date)
- 終了日 (End Date)
- 行動 (Activity)
- 停滞 (Stagnation)
- メンバー (Members) - used for filtering
- 山域 (Mountain Area)
- シーズン (Season)
- ルート・特記事項 (Route/Special Notes)
- 出典 (Source)
- リンク (Link)
- 種別 (Type)

### Output CSV Columns (Filtered)
The tool outputs a subset of columns: 年度, 暦年, 開始日, 終了日, 行動, 停滞, メンバー, 山域, シーズン, ルート・特記事項

## Code Architecture

- Single-file Python script with clear separation of concerns
- `extract_member_records()`: Main extraction logic with member name matching
- `save_to_csv()`: Handles CSV output with proper encoding (utf-8)
- `print_records()`: Formats console output for readability
- Error handling for file operations and encoding issues
- Command-line interface using argparse for easy usage