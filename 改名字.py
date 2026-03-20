#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_DIR = Path("./resource/pipeline")
FALLBACK_DIR = Path("./assets/resource/pipeline")
DEFAULT_OLD_NAME = "胡天驰"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="批量替换 pipeline JSON 中的人名。"
    )
    parser.add_argument("new_name", help="要替换成的新名字")
    parser.add_argument(
        "-o",
        "--old-name",
        default=DEFAULT_OLD_NAME,
        help=f"要被替换的旧名字，默认是 {DEFAULT_OLD_NAME}",
    )
    parser.add_argument(
        "-d",
        "--dir",
        type=Path,
        default=DEFAULT_DIR,
        help=f"pipeline JSON 所在目录，默认是 {DEFAULT_DIR}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示将要修改的内容，不写回文件",
    )
    return parser.parse_args()


def resolve_directory(directory: Path) -> Path:
    if directory.exists():
        return directory
    if directory == DEFAULT_DIR and FALLBACK_DIR.exists():
        return FALLBACK_DIR
    raise FileNotFoundError(f"目录不存在: {directory}")


def replace_in_data(data: Any, old_name: str, new_name: str) -> tuple[Any, int]:
    if isinstance(data, dict):
        replaced = {}
        total = 0
        for key, value in data.items():
            new_key, key_count = replace_in_data(key, old_name, new_name)
            new_value, value_count = replace_in_data(value, old_name, new_name)
            if new_key in replaced and new_key != key:
                raise ValueError(f"键名替换后冲突: {key} -> {new_key}")
            replaced[new_key] = new_value
            total += key_count + value_count
        return replaced, total

    if isinstance(data, list):
        replaced_list = []
        total = 0
        for item in data:
            new_item, item_count = replace_in_data(item, old_name, new_name)
            replaced_list.append(new_item)
            total += item_count
        return replaced_list, total

    if isinstance(data, str):
        count = data.count(old_name)
        if count == 0:
            return data, 0
        return data.replace(old_name, new_name), count

    return data, 0


def process_file(file_path: Path, old_name: str, new_name: str, dry_run: bool) -> int:
    with file_path.open("r", encoding="utf-8") as file:
        content = json.load(file)

    updated_content, replace_count = replace_in_data(content, old_name, new_name)
    if replace_count == 0:
        return 0

    if not dry_run:
        with file_path.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(updated_content, file, ensure_ascii=False, separators=(",", ":"))

    return replace_count


def main() -> int:
    args = parse_args()

    if args.old_name == args.new_name:
        print("旧名字和新名字相同，无需修改。")
        return 0

    try:
        directory = resolve_directory(args.dir)
    except FileNotFoundError as exc:
        print(exc)
        return 1

    json_files = sorted(directory.glob("*.json"))
    if not json_files:
        print(f"目录中没有找到 JSON 文件: {directory}")
        return 1

    total_replacements = 0
    changed_files = 0

    for file_path in json_files:
        replace_count = process_file(
            file_path=file_path,
            old_name=args.old_name,
            new_name=args.new_name,
            dry_run=args.dry_run,
        )
        if replace_count == 0:
            continue
        changed_files += 1
        total_replacements += replace_count
        action = "将修改" if args.dry_run else "已修改"
        print(f"{action} {file_path}: {replace_count} 处")

    if changed_files == 0:
        print(f"没有找到包含“{args.old_name}”的内容。")
        return 0

    summary_action = "预计修改" if args.dry_run else "共修改"
    print(f"{summary_action} {changed_files} 个文件，替换 {total_replacements} 处。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
