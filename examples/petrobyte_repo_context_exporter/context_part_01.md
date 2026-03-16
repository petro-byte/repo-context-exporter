# Repository Context Part 1/1

Generated for LLM prompt context.

## README.md

```markdown
# Repository Context Exporter

A Python utility for exporting source repositories into compact Markdown context files for LLM prompting.

The tool is designed for workflows where large codebases cannot be pasted into a prompt directly, but a structured and representative context export is still useful. It scans a repository, filters files using built-in ignore patterns, generates a directory tree, and writes the selected source files into a small number of Markdown bundles.

## Why this exists

When working with LLMs on non-trivial software projects, raw prompting quickly runs into context and upload limits. This script helps create a cleaner project snapshot by packaging the most relevant textual source files into prompt-friendly Markdown files.

## Features

- recursively scans a repository
- exports source files into Markdown bundles
- generates a separate directory tree file
- uses built-in gitignore-like ignore patterns
- skips common binary files and lockfiles
- keeps source files intact instead of splitting them across outputs
- balances content across a limited number of output files
- designed for practical LLM prompting workflows

## Typical Usage

```bash
python repo_context_exporter.py .
python repo_context_exporter.py /path/to/repo --output-dir llm-context
```

## Output

The script generates:
- one Markdown file containing the directory tree
- multiple Markdown files containing source code blocks
- a compact context package intended for LLM prompting

## How it works

The exporter:
- scans the repository recursively
- filters files based on ignore patterns
- excludes common binary assets and generated artifacts
- emits a Markdown directory tree
- writes source files into balanced Markdown bundles

## Use Case

This tool is especially useful when you want to:
- give an LLM a better overview of a repository
- preserve project structure in prompts
- avoid manually copy-pasting many files
- create reusable prompt context snapshots

## Example Output

An example export generated from the open-source project **pallets/click** can be found at [examples/pallets_click](examples/pallets_click).

## Notes

This project is intended as a lightweight developer utility and workflow helper.
It prioritizes practical usefulness and portability over full repository serialization.

## Author

Luka Petrovic
```
---

## repo_context_exporter.py

```python
#!/usr/bin/env python3
"""
Export a repository into markdown context files for LLM prompting.

Features
- Recursively collects files from a repository.
- Uses gitignore-like inline pattern lists (no external ignore file required).
- Writes source code into markdown files with path headers and fenced code blocks.
- Emits a separate markdown file with the directory tree.
- Keeps source files whole; never splits one file across multiple output files.
- Uses a soft file size threshold per markdown file (in KB).
- If the repository is too large for MAX_OUTPUT_FILES * MAX_OUTPUT_FILE_SIZE_KB,
  it rebalances content across exactly MAX_OUTPUT_FILES files as evenly as possible.

Typical usage
    python repo_context_exporter.py .
    python repo_context_exporter.py /path/to/repo --output-dir llm-context
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


# ============================================================
# Configuration
# ============================================================

# Maximum number of output markdown files.
MAX_OUTPUT_FILES = 8

# Optional maximum size per output markdown file in KB.
# Set to -1 to disable the threshold and always distribute evenly.
MAX_OUTPUT_FILE_SIZE_KB = 200

OUTPUT_DIR_NAME = "llm-context"
TREE_FILE_NAME = "00_DIRECTORY_TREE.md"
OUTPUT_FILE_PREFIX = "context_part_"
READ_FILE_ENCODING = "utf-8"
READ_FILE_ERRORS = "replace"

# Gitignore-like patterns for files that should NOT be included in code exports.
EXPORT_IGNORE_PATTERNS = [
    ".git/",
    ".idea/",
    ".vscode/",
    ".gitignore",
    ".gitkeep",
    "node_modules/",
    "dist/",
    "build/",
    "coverage/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.log",
    "*.sqlite",
    "*.sqlite3",
    "*.lock",
    "examples/",
    OUTPUT_DIR_NAME + "/",
]

# Separate ignore patterns for the directory tree export.
TREE_IGNORE_PATTERNS = [
    ".git/",
    "node_modules/",
    "dist/",
    "build/",
    "coverage/",
    "__pycache__/",
    ".DS_Store",
    "examples/",
    OUTPUT_DIR_NAME + "/",
]

# Files that are usually not helpful as prompt context.
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".mp3", ".wav", ".ogg", ".flac", ".mp4", ".mov", ".avi", ".mkv",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".class",
    ".jar", ".pyc", ".pyo",
}

# Optional extra file names to skip completely.
BINARY_FILENAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}


# ============================================================
# Language mapping for fenced code blocks
# ============================================================

EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".php": "php",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".ps1": "powershell",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".xml": "xml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".md": "markdown",
    ".dockerfile": "dockerfile",
    ".tf": "hcl",
    ".vue": "vue",
    ".svelte": "svelte",
    ".graphql": "graphql",
    ".gql": "graphql",
}

SPECIAL_FILENAMES_TO_LANGUAGE = {
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
    "CMakeLists.txt": "cmake",
    ".gitignore": "gitignore",
    ".env": "dotenv",
}


# ============================================================
# Data structures
# ============================================================

@dataclass(slots=True)
class FileBlock:
    rel_path: str
    markdown: str
    bytes: int


# ============================================================
# Ignore matching
# ============================================================

class IgnoreMatcher:
    """
    Small gitignore-like matcher implemented with stdlib only.
    """

    def __init__(self, patterns: Iterable[str]):
        self.patterns = [p.strip() for p in patterns if p.strip() and not p.strip().startswith("#")]

    def matches(self, rel_path: str, is_dir: bool) -> bool:
        rel_posix = rel_path.replace(os.sep, "/").strip("/")
        path_obj = PurePosixPath(rel_posix)
        included = True
        ignored = False

        for raw_pattern in self.patterns:
            negate = raw_pattern.startswith("!")
            pattern = raw_pattern[1:] if negate else raw_pattern
            if not pattern:
                continue

            if self._match_pattern(path_obj, pattern, is_dir):
                if negate:
                    ignored = False
                    included = True
                else:
                    ignored = True
                    included = False

        return ignored and not included

    def _match_pattern(self, path_obj: PurePosixPath, pattern: str, is_dir: bool) -> bool:
        path_str = str(path_obj)
        anchored = pattern.startswith("/")
        dir_only = pattern.endswith("/")

        normalized = pattern.strip("/")
        if not normalized:
            return False

        if dir_only and not is_dir:
            if path_str == normalized or path_str.startswith(normalized + "/"):
                return True

        if dir_only and is_dir:
            if path_str == normalized or path_str.startswith(normalized + "/"):
                return True

        candidate_patterns: list[str] = []

        if anchored:
            candidate_patterns.append(normalized)
        else:
            candidate_patterns.append(normalized)
            candidate_patterns.append(f"**/{normalized}")

        for candidate in candidate_patterns:
            if self._pure_match(path_obj, candidate):
                return True
            if fnmatch.fnmatch(path_str, candidate):
                return True

        return False

    @staticmethod
    def _pure_match(path_obj: PurePosixPath, pattern: str) -> bool:
        try:
            return path_obj.match(pattern)
        except Exception:
            return False


# ============================================================
# File selection and formatting
# ============================================================

def detect_language(path: Path) -> str:
    if path.name in SPECIAL_FILENAMES_TO_LANGUAGE:
        return SPECIAL_FILENAMES_TO_LANGUAGE[path.name]

    suffix = path.suffix.lower()
    if suffix in EXTENSION_TO_LANGUAGE:
        return EXTENSION_TO_LANGUAGE[suffix]

    if path.name.lower().endswith("dockerfile"):
        return "dockerfile"

    return "text"


def looks_binary(path: Path) -> bool:
    if path.name in BINARY_FILENAMES:
        return True

    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    try:
        with path.open("rb") as fh:
            chunk = fh.read(4096)
        if b"\x00" in chunk:
            return True
    except OSError:
        return True

    return False


def read_text_file(path: Path) -> str:
    return path.read_text(encoding=READ_FILE_ENCODING, errors=READ_FILE_ERRORS)


def make_file_block(root: Path, path: Path) -> FileBlock:
    rel_path = path.relative_to(root).as_posix()
    language = detect_language(path)
    content = read_text_file(path)

    block = (
        f"## {rel_path}\n\n"
        f"```{language}\n"
        f"{content}"
        f"\n```\n"
    )

    return FileBlock(
        rel_path=rel_path,
        markdown=block,
        bytes=len(block.encode("utf-8")),
    )


def collect_files(root: Path, ignore_patterns: list[str]) -> list[Path]:
    matcher = IgnoreMatcher(ignore_patterns)
    collected: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)

        kept_dirnames: list[str] = []
        for dirname in sorted(dirnames):
            full_dir = current_dir / dirname
            rel_dir = full_dir.relative_to(root).as_posix()
            if matcher.matches(rel_dir, is_dir=True):
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for filename in sorted(filenames):
            full_file = current_dir / filename
            rel_file = full_file.relative_to(root).as_posix()

            if matcher.matches(rel_file, is_dir=False):
                continue
            if not full_file.is_file():
                continue
            if looks_binary(full_file):
                continue

            collected.append(full_file)

    collected.sort(key=lambda p: p.relative_to(root).as_posix())
    return collected


# ============================================================
# Partitioning
# ============================================================

def partition_by_soft_threshold(
    blocks: list[FileBlock],
    max_files: int,
    max_kb: int,
) -> list[list[FileBlock]]:
    if not blocks:
        return []

    if max_files <= 0:
        raise ValueError("max_files must be > 0")

    max_bytes = None if max_kb < 0 else max_kb * 1024

    # If threshold is disabled, always distribute evenly.
    if max_bytes is None:
        return partition_evenly_sequential(blocks, max_files)

    total_bytes = sum(block.bytes for block in blocks)
    capacity = max_files * max_bytes

    # If total content does not exceed total threshold capacity, do threshold-based packing.
    if total_bytes <= capacity:
        groups: list[list[FileBlock]] = []
        current_group: list[FileBlock] = []
        current_bytes = 0

        for block in blocks:
            would_exceed = current_group and (current_bytes + block.bytes > max_bytes)
            still_can_open_new_group = len(groups) < max_files - 1

            if would_exceed and still_can_open_new_group:
                groups.append(current_group)
                current_group = [block]
                current_bytes = block.bytes
            else:
                current_group.append(block)
                current_bytes += block.bytes

        if current_group:
            groups.append(current_group)

        return groups

    # Otherwise distribute evenly across exactly max_files outputs.
    return partition_evenly_sequential(blocks, max_files)


def partition_evenly_sequential(
    blocks: list[FileBlock],
    parts: int,
) -> list[list[FileBlock]]:
    if parts <= 0:
        raise ValueError("parts must be > 0")
    if not blocks:
        return []

    total_bytes = sum(block.bytes for block in blocks)
    groups: list[list[FileBlock]] = []
    start = 0
    consumed_bytes = 0

    for part_index in range(parts):
        remaining_parts = parts - part_index
        remaining_blocks = len(blocks) - start

        if remaining_blocks <= 0:
            break

        if remaining_parts == 1:
            groups.append(blocks[start:])
            break

        target_for_this_part = max(1, round((total_bytes - consumed_bytes) / remaining_parts))

        current: list[FileBlock] = []
        current_bytes = 0

        while start < len(blocks):
            block = blocks[start]

            must_leave_one_per_remaining_part = (len(blocks) - (start + 1)) >= (remaining_parts - 1)

            if not current:
                current.append(block)
                current_bytes += block.bytes
                start += 1
                continue

            current_diff = abs(target_for_this_part - current_bytes)
            next_diff = abs(target_for_this_part - (current_bytes + block.bytes))

            if must_leave_one_per_remaining_part and next_diff <= current_diff:
                current.append(block)
                current_bytes += block.bytes
                start += 1
            else:
                break

        groups.append(current)
        consumed_bytes += current_bytes

    return [g for g in groups if g]


# ============================================================
# Tree generation
# ============================================================

def build_tree_lines(root: Path, ignore_patterns: list[str]) -> list[str]:
    matcher = IgnoreMatcher(ignore_patterns)
    lines = [f"{root.name}/"]
    lines.extend(_build_tree_lines_recursive(root, root, matcher, prefix=""))
    return lines


def _build_tree_lines_recursive(root: Path, current: Path, matcher: IgnoreMatcher, prefix: str) -> list[str]:
    children = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

    visible_children: list[Path] = []
    for child in children:
        rel = child.relative_to(root).as_posix()
        if matcher.matches(rel, is_dir=child.is_dir()):
            continue
        visible_children.append(child)

    lines: list[str] = []
    for index, child in enumerate(visible_children):
        is_last = index == len(visible_children) - 1
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "
        name = child.name + ("/" if child.is_dir() else "")
        lines.append(prefix + connector + name)

        if child.is_dir():
            lines.extend(_build_tree_lines_recursive(root, child, matcher, prefix + extension))

    return lines


# ============================================================
# Writing output
# ============================================================

def write_tree_file(output_dir: Path, tree_lines: list[str]) -> None:
    content = "# Directory Tree\n\n```text\n" + "\n".join(tree_lines) + "\n```\n"
    (output_dir / TREE_FILE_NAME).write_text(content, encoding="utf-8")


def write_context_files(output_dir: Path, groups: list[list[FileBlock]]) -> None:
    width = max(2, len(str(len(groups))))

    for index, group in enumerate(groups, start=1):
        joined = "\n---\n\n".join(block.markdown.rstrip() for block in group).rstrip() + "\n"
        header = (
            f"# Repository Context Part {index}/{len(groups)}\n\n"
            f"Generated for LLM prompt context.\n\n"
        )
        filename = f"{OUTPUT_FILE_PREFIX}{index:0{width}d}.md"
        (output_dir / filename).write_text(header + joined, encoding="utf-8")


def print_summary(output_dir: Path, files: list[Path], groups: list[list[FileBlock]]) -> None:
    print(f"Export completed: {output_dir}")
    print(f"Included source files: {len(files)}")
    print(f"Context markdown files: {len(groups)}")
    for index, group in enumerate(groups, start=1):
        size_kb = sum(block.bytes for block in group) / 1024
        print(f"  - part {index}: {len(group)} files, {size_kb:.1f} KB")
    print(f"Tree file: {TREE_FILE_NAME}")


# ============================================================
# Main
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export repository code into markdown context files.")
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository root to scan. Defaults to current directory.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=f"Output directory. Defaults to <root>/{OUTPUT_DIR_NAME}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()

    if not root.exists() or not root.is_dir():
        print(f"Error: root path is not a directory: {root}")
        return 1

    output_dir = Path(args.output_dir).resolve() if args.output_dir else root / OUTPUT_DIR_NAME

    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    files = collect_files(root, EXPORT_IGNORE_PATTERNS)
    blocks = [make_file_block(root, path) for path in files]

    groups = partition_by_soft_threshold(
        blocks,
        MAX_OUTPUT_FILES,
        MAX_OUTPUT_FILE_SIZE_KB,
    )

    tree_lines = build_tree_lines(root, TREE_IGNORE_PATTERNS)

    write_tree_file(output_dir, tree_lines)
    write_context_files(output_dir, groups)
    print_summary(output_dir, files, groups)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
