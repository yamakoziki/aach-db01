#!/usr/bin/env python3
"""
AACH登山データ抽出ツール

使い方:
  # 個人抽出（OR検索: 表記ゆれ対応）
  python mountain_extractor.py personal DATA.csv "澤柿" "沢柿" [-o out.csv] [--analyze]

  # 個人抽出（AND検索: 複数人が同行した山行を検索）
  python mountain_extractor.py personal DATA.csv "澤柿" "石橋" --name-logic and

  # 山域・シーズン・ルート条件抽出
  python mountain_extractor.py condition DATA.csv [-a 山域1 山域2] [-s シーズン1] \
      [-r キーワード1 キーワード2] [-o out.csv] [--analyze]  # AND検索（デフォルト）

  # ルートキーワードOR検索
  python mountain_extractor.py condition DATA.csv -r 縦走 スキー --route-logic or

  # 一覧確認（山域・シーズンの選択肢を表示）
  python mountain_extractor.py list DATA.csv
"""

import csv
import argparse
import sys
import re
from collections import Counter
from datetime import datetime
from typing import List, Dict, Optional


OUTPUT_COLUMNS = ['年度', '暦年', '開始日', '終了日', '行動', '停滞', 'メンバー', '山域', 'シーズン', 'ルート・特記事項', '出典']
SEP = "-" * 60


# ===== ユーティリティ =====

def normalize_name(name: str) -> str:
    """ロール接頭辞・括弧サフィックスを除去して名前を正規化"""
    name = re.sub(r'^[A-Za-z]+:\s*', '', name)
    name = re.sub(r'[（(][^）)]*[）)]$', '', name)
    return name.strip()


def load_csv(csv_file: str) -> List[Dict]:
    """CSVファイルを読み込んでレコードリストを返す"""
    for encoding in ('utf-8-sig', 'utf-8', 'shift_jis', 'cp932'):
        try:
            with open(csv_file, 'r', encoding=encoding, newline='') as f:
                reader = csv.DictReader(f)
                records = [row for row in reader]
            return records
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            print(f"エラー: ファイル '{csv_file}' が見つかりません。", file=sys.stderr)
            sys.exit(1)
    print(f"エラー: '{csv_file}' のエンコーディングを判別できませんでした。", file=sys.stderr)
    sys.exit(1)


def save_csv(records: List[Dict], output_file: str):
    """抽出結果をCSVファイルに保存（BOM付きUTF-8でExcel対応）"""
    if not records:
        print("保存するレコードがありません。")
        return
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            for r in records:
                writer.writerow({k: r.get(k, '') for k in OUTPUT_COLUMNS})
        print(f"{len(records)}件を '{output_file}' に保存しました。")
    except Exception as e:
        print(f"ファイル保存エラー: {e}", file=sys.stderr)


def print_records(records: List[Dict]):
    """抽出結果を標準出力に表示"""
    if not records:
        print("該当するレコードが見つかりませんでした。")
        return
    print(f"抽出件数: {len(records)}件")
    print(SEP)
    for i, r in enumerate(records, 1):
        print(f"[{i}] {r.get('年度','')} {r.get('開始日','')} ～ {r.get('終了日','')}  {r.get('山域','')}")
        print(f"    シーズン: {r.get('シーズン','')}  行動: {r.get('行動','')}日  停滞: {r.get('停滞','0')}日")
        print(f"    ルート  : {r.get('ルート・特記事項','')}")
        print(f"    メンバー: {r.get('メンバー','')}")
        print()


# ===== 抽出ロジック =====

def extract_personal(records: List[Dict], member_names: List[str], name_logic: str = 'or') -> List[Dict]:
    """メンバー名で登山記録を抽出（部分一致）

    name_logic='or' : いずれかの名前がメンバーに含まれる（表記ゆれ対応・デフォルト）
    name_logic='and': すべての名前がメンバーに含まれる（同行者検索）
    """
    result = []
    for r in records:
        members = (r.get('メンバー', '') or '').split()
        normalized = [normalize_name(m) for m in members]
        if name_logic == 'and':
            if all(any(name in norm for norm in normalized) for name in member_names):
                result.append(r)
        else:
            if any(name in norm for name in member_names for norm in normalized):
                result.append(r)
    return result


def extract_condition(
    records: List[Dict],
    areas: Optional[List[str]] = None,
    seasons: Optional[List[str]] = None,
    route_keywords: Optional[List[str]] = None,
    route_logic: str = 'and',
) -> List[Dict]:
    """山域・シーズン・ルートキーワードで登山記録を抽出"""
    result = []
    for r in records:
        if areas and (r.get('山域', '') or '') not in areas:
            continue
        if seasons and (r.get('シーズン', '') or '') not in seasons:
            continue
        if route_keywords:
            text = (r.get('ルート・特記事項', '') or '') + ' ' + (r.get('山域', '') or '')
            if route_logic == 'or':
                if not any(kw in text for kw in route_keywords):
                    continue
            else:
                if not all(kw in text for kw in route_keywords):
                    continue
        result.append(r)
    return result


# ===== 分析 =====

def analyze(records: List[Dict], theme: str, member_names: List[str] = None):
    """指定テーマで分析結果を出力"""
    if not records:
        print("分析対象のデータがありません。")
        return

    print()
    if theme == 'seasonal':
        _analyze_bar('シーズン別登山回数', Counter(r.get('シーズン','不明') for r in records))

    elif theme == 'area':
        _analyze_bar('山域別登山回数（上位15）', Counter(r.get('山域','不明') for r in records), top=15)

    elif theme == 'timeline':
        cnt = Counter(r.get('暦年','不明') for r in records)
        _analyze_bar('年代別活動回数', cnt, sort_key=lambda x: x[0])

    elif theme == 'member':
        cnt = Counter()
        for r in records:
            for m in (r.get('メンバー','') or '').split():
                n = normalize_name(m)
                if n and n != '不詳' and not any(name in n for name in (member_names or [])):
                    cnt[n] += 1
        title = f"{'・'.join(member_names)}との同行者（上位15名）" if member_names else "参加メンバー頻度（上位15名）"
        _analyze_bar(title, cnt, top=15)

    elif theme == 'stagnation':
        _analyze_stagnation(records)

    elif theme == 'route':
        _analyze_route(records)

    elif theme == 'activity':
        _analyze_activity(records)

    else:
        print(f"不明な分析テーマ: {theme}")


def _analyze_bar(title: str, counter: Counter, top: int = None, sort_key=None):
    entries = counter.most_common(top) if not sort_key else sorted(counter.items(), key=sort_key)
    if top and sort_key:
        entries = entries[:top]
    if not entries:
        print(f"■ {title}\nデータなし")
        return
    max_cnt = max(c for _, c in entries)
    bar_width = 30
    print(f"■ {title}")
    print(SEP)
    for label, cnt in entries:
        bar = '█' * int(cnt / max_cnt * bar_width)
        print(f"  {label:<20} {bar:<30} {cnt}回")
    print()


def _analyze_stagnation(records: List[Dict]):
    with_stay = [r for r in records if _int(r.get('停滞', '0')) >= 1]
    without_stay = [r for r in records if _int(r.get('停滞', '0')) < 1]
    total_days = sum(_int(r.get('停滞', '0')) for r in with_stay)
    total = len(records)
    rate = len(with_stay) / total * 100 if total else 0
    avg = total_days / len(with_stay) if with_stay else 0

    print("■ 停滞分析")
    print(SEP)
    print(f"  総記録数      : {total}件")
    print(f"  停滞あり      : {len(with_stay)}件")
    print(f"  停滞なし      : {len(without_stay)}件")
    print(f"  停滞率        : {rate:.1f}%")
    print(f"  平均停滞日数  : {avg:.1f}日（停滞あり記録のみ）")
    print(f"  累計停滞日数  : {total_days}日")
    print()


def _analyze_route(records: List[Dict]):
    keywords = ['スキー', '初登山', '初登頂', '合宿', '講習会', '縦走', '沢登り', '岩登り', 'ピーク', '尾根']
    cnt = Counter()
    for r in records:
        text = r.get('ルート・特記事項', '') or ''
        for kw in keywords:
            if kw in text:
                cnt[kw] += 1
    _analyze_bar('ルート・活動キーワード出現回数', cnt)


def _analyze_activity(records: List[Dict]):
    days = [_int(r.get('行動', '0')) for r in records if _int(r.get('行動', '0')) > 0]
    if not days:
        print("■ 行動日数分析\nデータなし")
        return
    total = sum(days)
    avg = total / len(days)
    max_d = max(days)
    dist = Counter()
    for d in days:
        if d == 1:
            dist['日帰り(1日)'] += 1
        elif d <= 3:
            dist['2〜3日'] += 1
        elif d <= 7:
            dist['4〜7日'] += 1
        else:
            dist['8日以上'] += 1

    print("■ 行動日数分析")
    print(SEP)
    order = ['日帰り(1日)', '2〜3日', '4〜7日', '8日以上']
    max_cnt = max(dist.values()) if dist else 1
    for k in order:
        if k in dist:
            bar = '█' * int(dist[k] / max_cnt * 30)
            print(f"  {k:<12} {bar:<30} {dist[k]}件")
    print(f"\n  平均行動日数 : {avg:.1f}日")
    print(f"  最長行動日数 : {max_d}日")
    print(f"  総行動日数   : {total}日")
    print()


def _int(v) -> int:
    try:
        return int(str(v).strip())
    except (ValueError, TypeError):
        return 0


# ===== CLI =====

def cmd_personal(args):
    records = load_csv(args.csv_file)
    result = extract_personal(records, args.member_name, args.name_logic)

    if not result:
        sep = ' AND ' if args.name_logic == 'and' else '・'
        names_str = sep.join(args.member_name)
        print(f"「{names_str}」の記録が見つかりませんでした。")
        return

    if args.output:
        save_csv(result, args.output)
    else:
        print_records(result)

    if args.analyze:
        for theme in ['seasonal', 'area', 'timeline', 'member', 'stagnation', 'route']:
            analyze(result, theme, member_names=args.member_name)


def cmd_condition(args):
    records = load_csv(args.csv_file)

    areas = args.area or []
    seasons = args.season or []
    route_kws = [kw for kw in (args.route or []) if kw.strip()]

    if not areas and not seasons and not route_kws:
        print("エラー: 山域(-a)・シーズン(-s)・ルートキーワード(-r)のいずれかを指定してください。", file=sys.stderr)
        sys.exit(1)

    result = extract_condition(records, areas or None, seasons or None, route_kws or None, args.route_logic)

    if not result:
        print("指定条件に該当するレコードが見つかりませんでした。")
        return

    if args.output:
        save_csv(result, args.output)
    else:
        print_records(result)

    if args.analyze:
        for theme in ['area', 'seasonal', 'timeline', 'member', 'stagnation', 'activity']:
            analyze(result, theme)


def cmd_list(args):
    records = load_csv(args.csv_file)
    areas = sorted(set(r.get('山域', '') for r in records if r.get('山域', '')))
    seasons = sorted(set(r.get('シーズン', '') for r in records if r.get('シーズン', '')))
    print(f"総レコード数: {len(records)}件")
    print(SEP)
    print(f"■ 山域一覧（{len(areas)}件）")
    for a in areas:
        print(f"  {a}")
    print()
    print(f"■ シーズン一覧（{len(seasons)}件）")
    for s in seasons:
        print(f"  {s}")


def main():
    parser = argparse.ArgumentParser(
        description='AACH登山データ抽出ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # --- personal ---
    p1 = sub.add_parser('personal', help='メンバー名で抽出（個人抽出）')
    p1.add_argument('csv_file', help='登山データCSVファイル')
    p1.add_argument('member_name', nargs='+', help='メンバー名（部分一致）。複数指定時は --name-logic で AND/OR を選択')
    p1.add_argument('--name-logic', choices=['and', 'or'], default='or',
                    help='メンバー名の検索論理: or=いずれかを含む（デフォルト・表記ゆれ対応）/ and=すべてを含む（同行者検索）')
    p1.add_argument('-o', '--output', help='出力CSVファイルパス')
    p1.add_argument('--analyze', action='store_true', help='分析結果を表示')
    p1.set_defaults(func=cmd_personal)

    # --- condition ---
    p2 = sub.add_parser('condition', help='山域・シーズン・ルートキーワードで抽出')
    p2.add_argument('csv_file', help='登山データCSVファイル')
    p2.add_argument('-a', '--area', nargs='+', metavar='山域', help='山域（複数指定可）')
    p2.add_argument('-s', '--season', nargs='+', metavar='シーズン', help='シーズン（複数指定可）')
    p2.add_argument('-r', '--route', nargs='+', metavar='キーワード', help='ルートキーワード（最大5つ推奨）')
    p2.add_argument('--route-logic', choices=['and', 'or'], default='and',
                    help='ルートキーワードの検索論理: and=すべてを含む（デフォルト）/ or=いずれかを含む')
    p2.add_argument('-o', '--output', help='出力CSVファイルパス')
    p2.add_argument('--analyze', action='store_true', help='分析結果を表示')
    p2.set_defaults(func=cmd_condition)

    # --- list ---
    p3 = sub.add_parser('list', help='山域・シーズンの選択肢を一覧表示')
    p3.add_argument('csv_file', help='登山データCSVファイル')
    p3.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
