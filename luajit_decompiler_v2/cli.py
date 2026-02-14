from __future__ import annotations

import argparse
from pathlib import Path

from .bytecode import Bytecode, ParseError
from .decompiler import Decompiler


def _iter_inputs(path: Path, extension: str | None):
    if path.is_file():
        yield path
        return
    for item in path.rglob("*"):
        if item.is_file() and (extension is None or item.suffix.lower() == extension):
            yield item


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="luajit-decompiler-v2-py")
    parser.add_argument("input_path")
    parser.add_argument("-o", "--output", dest="output_path", default="output")
    parser.add_argument("-e", "--extension", dest="extension_filter")
    parser.add_argument("-s", "--silent_assertions", action="store_true")
    parser.add_argument("-f", "--force_overwrite", action="store_true")
    parser.add_argument("-i", "--ignore_debug_info", action="store_true")
    parser.add_argument("-m", "--minimize_diffs", action="store_true")
    parser.add_argument("-u", "--unrestricted_ascii", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input_path)
    out_root = Path(args.output_path)
    extension = args.extension_filter
    if extension and not extension.startswith("."):
        extension = f".{extension}"
    if extension:
        extension = extension.lower()

    files = list(_iter_inputs(input_path, extension))
    if not files:
        print("No matching files found")
        return 1

    out_root.mkdir(parents=True, exist_ok=True)
    failures = 0
    for src in files:
        relative = Path(src.name) if input_path.is_file() else src.relative_to(input_path)
        dst = out_root / relative.with_suffix(".lua")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and not args.force_overwrite:
            print(f"Skipping existing: {dst}")
            continue
        try:
            bc = Bytecode(str(src))
            bc.parse()
            decompiler = Decompiler(bc, ignore_debug_info=args.ignore_debug_info, minimize_diffs=args.minimize_diffs)
            dst.write_text(decompiler.decompile(), encoding="utf-8" if not args.unrestricted_ascii else "latin1")
            print(f"Decompiled: {src} -> {dst}")
        except (ParseError, OSError) as exc:
            failures += 1
            print(f"Failed: {src}: {exc}")
            if not args.silent_assertions:
                return 1
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
