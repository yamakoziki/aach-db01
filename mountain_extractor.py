#!/usr/bin/env python3
import csv
import argparse
import sys
from typing import List, Dict

def extract_member_records(csv_file: str, member_name: str, output_file: str = None) -> List[Dict]:
    """
    CSVファイルからメンバー名を含む登山記録を抽出
    
    Args:
        csv_file: 登山データCSVファイルパス
        member_name: 抽出対象のメンバー名
        output_file: 出力CSVファイルパス（指定なしの場合は標準出力）
    
    Returns:
        抽出されたレコードのリスト
    """
    extracted_records = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if member_name in row.get('メンバー', ''):
                    extracted_records.append(row)
    
    except FileNotFoundError:
        print(f"エラー: ファイル '{csv_file}' が見つかりません。", file=sys.stderr)
        return []
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        return []
    
    if output_file:
        save_to_csv(extracted_records, output_file)
    else:
        print_records(extracted_records)
    
    return extracted_records

def save_to_csv(records: List[Dict], output_file: str):
    """抽出されたレコードをCSVファイルに保存"""
    if not records:
        print("抽出されたレコードがありません。")
        return
    
    fieldnames = ['年度', '暦年', '開始日', '終了日', '行動', '停滞', 'メンバー', '山域', 'シーズン', 'ルート・特記事項', '出典']
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records:
                filtered_record = {key: record.get(key, '') for key in fieldnames}
                writer.writerow(filtered_record)
        
        print(f"{len(records)}件のレコードを '{output_file}' に保存しました。")
    
    except Exception as e:
        print(f"ファイル保存エラー: {e}", file=sys.stderr)

def print_records(records: List[Dict]):
    """抽出されたレコードを標準出力に表示"""
    if not records:
        print("該当するレコードが見つかりませんでした。")
        return
    
    print(f"抽出されたレコード数: {len(records)}")
    print("-" * 50)
    
    for i, record in enumerate(records, 1):
        print(f"[{i}] {record.get('年度', '')} {record.get('開始日', '')} - {record.get('終了日', '')} - {record.get('山域', '')}")
        print(f"    メンバー: {record.get('メンバー', '')}")
        print(f"    ルート: {record.get('ルート・特記事項', '')}")
        print(f"    出典: {record.get('出典', '')}")
        print()

def main():
    parser = argparse.ArgumentParser(description='登山データからメンバーの記録を抽出')
    parser.add_argument('csv_file', help='登山データCSVファイルパス')
    parser.add_argument('member_name', help='抽出対象のメンバー名')
    parser.add_argument('-o', '--output', help='出力CSVファイルパス')
    
    args = parser.parse_args()
    
    extract_member_records(args.csv_file, args.member_name, args.output)

if __name__ == '__main__':
    main()