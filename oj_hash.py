#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from glob import glob
from pathlib import Path

from clang import cindex
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

CACHE_VERSION = 1
DEFAULT_CLANG_ARGS = ["-std=c++17", "-x", "c++"]


def _find_libclang_file() -> Path | None:
    env = os.getenv("LIBCLANG_PATH")
    if env:
        p = Path(env)
        if p.is_file():
            return p
        if p.is_dir():
            matches = sorted(p.glob("libclang*.so*"))
            if matches:
                return matches[0]

    candidates = []
    for pattern in (
        "/usr/lib/llvm-*/lib/libclang*.so*",
        "/usr/lib/x86_64-linux-gnu/libclang*.so*",
        "/usr/lib/libclang*.so*",
    ):
        candidates.extend(Path(p) for p in glob(pattern))
    candidates = sorted({c for c in candidates if c.is_file()})
    return candidates[0] if candidates else None


def _configure_libclang(console: Console) -> None:
    if getattr(cindex.Config, "loaded", False):
        return

    env = os.getenv("LIBCLANG_PATH")
    if env:
        p = Path(env)
        if p.is_dir():
            cindex.Config.set_library_path(str(p))
        elif p.is_file():
            cindex.Config.set_library_file(str(p))
    else:
        libclang = _find_libclang_file()
        if libclang:
            cindex.Config.set_library_file(str(libclang))

    try:
        _ = cindex.Index.create()
    except Exception as exc:  # pragma: no cover - runtime check
        console.print(
            Panel(
                Text(
                    "libclang not found. Install clang/libclang and/or set LIBCLANG_PATH.",
                    style="bold red",
                ),
                title="Error",
                border_style="red",
            )
        )
        raise SystemExit(2) from exc


def _hash_file_content(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _iter_files(program_dir: Path, extensions: set[str] | None, recursive: bool) -> list[Path]:
    files: list[Path] = []
    if recursive:
        for root, dirs, filenames in os.walk(program_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in filenames:
                if name.startswith("."):
                    continue
                path = Path(root) / name
                if not path.is_file() or path.is_symlink():
                    continue
                if extensions and path.suffix.lower() not in extensions:
                    continue
                files.append(path)
    else:
        for path in program_dir.iterdir():
            if path.name.startswith("."):
                continue
            if not path.is_file() or path.is_symlink():
                continue
            if extensions and path.suffix.lower() not in extensions:
                continue
            files.append(path)
    return sorted(files)


def _token_hash(path: Path, index: cindex.Index, clang_args: list[str]) -> tuple[str, int, int]:
    options = (
        cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
        | cindex.TranslationUnit.PARSE_INCOMPLETE
    )
    tu = index.parse(str(path), args=clang_args, options=options)

    path_resolved = path.resolve()
    hasher = hashlib.sha256()
    token_count = 0

    for token in tu.get_tokens(extent=tu.cursor.extent):
        if token.kind == cindex.TokenKind.COMMENT:
            continue
        loc = token.location
        if not loc.file:
            continue
        try:
            token_path = Path(loc.file.name).resolve()
        except FileNotFoundError:
            token_path = Path(loc.file.name)
        if token_path != path_resolved:
            continue

        kind = token.kind.name
        spelling = token.spelling
        hasher.update(kind.encode("utf-8", "surrogatepass"))
        hasher.update(b"\0")
        hasher.update(spelling.encode("utf-8", "surrogatepass"))
        hasher.update(b"\0")
        token_count += 1

    error_count = sum(1 for d in tu.diagnostics if d.severity >= cindex.Diagnostic.Error)
    return hasher.hexdigest(), token_count, error_count


def _load_cache(path: Path, reset: bool) -> dict:
    if reset or not path.exists():
        return {"version": CACHE_VERSION, "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": CACHE_VERSION, "entries": {}}
    if data.get("version") != CACHE_VERSION:
        return {"version": CACHE_VERSION, "entries": {}}
    if not isinstance(data.get("entries"), dict):
        return {"version": CACHE_VERSION, "entries": {}}
    return data


def _save_cache(path: Path, data: dict) -> None:
    data["version"] = CACHE_VERSION
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def _build_summary_table(total: int, unique: int, dup_groups: int, dup_files: int, cache_hits: int) -> Table:
    table = Table.grid(padding=(0, 1))
    table.add_column(justify="right", style="cyan")
    table.add_column()
    table.add_row("Files", str(total))
    table.add_row("Unique programs", str(unique))
    table.add_row("Duplicate groups", str(dup_groups))
    table.add_row("Files in duplicates", str(dup_files))
    table.add_row("Cache hits", str(cache_hits))
    return table


def _print_groups(console: Console, groups: dict[str, list[str]]) -> None:
    table = Table(
        title="Normalized Hash Groups",
        box=box.ROUNDED,
        header_style="bold white",
        show_lines=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Count", justify="right")
    table.add_column("Hash", style="magenta")
    table.add_column("Files")

    sorted_groups = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for idx, (hash_value, files) in enumerate(sorted_groups, start=1):
        short_hash = f"{hash_value[:12]}...{hash_value[-6:]}"
        style = "dim" if len(files) == 1 else ""
        table.add_row(str(idx), str(len(files)), short_hash, "\n".join(files), style=style)

    console.print(table)


def main() -> int:
    parser = argparse.ArgumentParser(description="C++ normalized hash checker using libclang tokens.")
    parser.add_argument("--program-dir", default="program", help="Directory containing programs")
    parser.add_argument("--cache-file", default="cache.json", help="Cache file (JSON)")
    parser.add_argument(
        "--reset-cache",
        action="store_true",
        help="Ignore existing cache and rebuild (cache is overwritten each run anyway)",
    )
    parser.add_argument(
        "--extensions",
        default="",
        help="Comma-separated extensions to include (empty = all files)",
    )
    parser.add_argument("--no-recursive", action="store_true", help="Only scan top-level directory")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    args = parser.parse_args()

    console = Console(color_system=None if args.no_color else "auto")
    program_dir = Path(args.program_dir)
    cache_path = Path(args.cache_file)

    if not program_dir.exists():
        console.print(
            Panel(
                Text(f"Program directory not found: {program_dir}", style="bold red"),
                title="Error",
                border_style="red",
            )
        )
        return 2

    extensions = None
    if args.extensions.strip():
        extensions = {ext.strip().lower() for ext in args.extensions.split(",") if ext.strip()}
        extensions = {ext if ext.startswith(".") else f".{ext}" for ext in extensions}

    _configure_libclang(console)

    files = _iter_files(program_dir, extensions, recursive=not args.no_recursive)
    if not files:
        console.print(
            Panel(
                Text("No files found to analyze.", style="yellow"),
                title="Notice",
                border_style="yellow",
            )
        )
        return 0

    cache = _load_cache(cache_path, reset=args.reset_cache)
    prev_entries = cache.get("entries", {})
    new_entries: dict[str, dict] = {}

    header = Panel.fit(
        Text("OJ Program Normalized Hash", style="bold white"),
        subtitle="libclang token stream -> SHA-256",
        border_style="bright_blue",
    )
    console.print(header)

    cache_hits = 0
    error_files: dict[str, int] = {}
    clang_args = DEFAULT_CLANG_ARGS + [f"-I{program_dir}"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Hashing"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("hash", total=len(files))
        index = cindex.Index.create()
        for path in files:
            rel = path.relative_to(program_dir).as_posix()
            stat = path.stat()
            entry = prev_entries.get(rel)
            if (
                entry
                and entry.get("mtime_ns") == stat.st_mtime_ns
                and entry.get("size") == stat.st_size
                and entry.get("normalized_hash")
                and entry.get("content_sha256")
            ):
                new_entries[rel] = entry
                cache_hits += 1
                progress.advance(task_id)
                continue

            content_sha = _hash_file_content(path)
            norm_hash, token_count, error_count = _token_hash(
                path,
                index,
                clang_args=clang_args,
            )
            if error_count:
                error_files[rel] = error_count

            new_entries[rel] = {
                "mtime_ns": stat.st_mtime_ns,
                "size": stat.st_size,
                "content_sha256": content_sha,
                "normalized_hash": norm_hash,
                "token_count": token_count,
            }
            progress.advance(task_id)

    cache["entries"] = new_entries
    _save_cache(cache_path, cache)

    groups: dict[str, list[str]] = defaultdict(list)
    for rel, entry in new_entries.items():
        groups[entry["normalized_hash"]].append(rel)

    total_files = len(files)
    unique_groups = len(groups)
    dup_groups = sum(1 for g in groups.values() if len(g) > 1)
    dup_files = sum(len(g) for g in groups.values() if len(g) > 1)

    summary_table = _build_summary_table(
        total=total_files,
        unique=unique_groups,
        dup_groups=dup_groups,
        dup_files=dup_files,
        cache_hits=cache_hits,
    )
    console.print(Panel(summary_table, title="Summary", border_style="blue"))
    _print_groups(console, groups)

    if error_files:
        err_table = Table(title="Diagnostics", box=box.SIMPLE, show_header=True)
        err_table.add_column("File")
        err_table.add_column("Errors", justify="right", style="red")
        for rel, count in sorted(error_files.items()):
            err_table.add_row(rel, str(count))
        console.print(Panel(err_table, title="Parse Errors", border_style="red"))

    console.print(
        Text(
            "Hash-only comparison. If you suspect collisions, compare source manually.",
            style="dim",
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
