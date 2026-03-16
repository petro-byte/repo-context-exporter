#!/usr/bin/env python3
"""
Export a repository into markdown context files for LLM prompting.

Features
- Recursively collects files from a repository.
- Uses gitignore-like inline pattern lists (no external ignore file required).
- Writes source code into markdown files with path headers and fenced code blocks.
- Emits a separate markdown file with the directory tree.
- Keeps source files whole; never splits one file across multiple output files.
- Uses a soft line threshold per markdown file.
- If the repository is too large for MAX_OUTPUT_FILES * TARGET_LINES_PER_OUTPUT,
  it rebalances content across exactly MAX_OUTPUT_FILES files as evenly as possible.

Typical usage
    python repo_context_exporter.py .
    python repo_context_exporter.py /path/to/repo --output-dir llm-context
"""

from __future__ import annotations

import argparse
import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable
import shutil


# ============================================================
# Configuration
# ============================================================

MAX_OUTPUT_FILES = 9
TARGET_LINES_PER_OUTPUT = 1200
OUTPUT_DIR_NAME = "llm-context"
TREE_FILE_NAME = "00_DIRECTORY_TREE.md"
OUTPUT_FILE_PREFIX = "context_part_"
READ_FILE_ENCODING = "utf-8"
READ_FILE_ERRORS = "replace"

# Gitignore-like patterns for files that should NOT be included in code exports.
# Examples:
#   "node_modules/"
#   "dist/"
#   "*.log"
#   ".env*"
#   "coverage/"
#   "*.min.js"
#   "/build/"
#   "**/__pycache__/"
EXPORT_IGNORE_PATTERNS = [
    "repo_context_exporter.py",
    ".git/",
    ".idea/",
    ".vscode/",
    ".gitignore"
    ".gitkeep"
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
    "*.js",
    OUTPUT_DIR_NAME + "/",
]

# Separate ignore patterns for the directory tree export.
TREE_IGNORE_PATTERNS = [
    "repo_context_exporter.py",
    ".git/",
    "node_modules/",
    "dist/",
    "build/",
    "coverage/",
    "__pycache__/",
    ".DS_Store",
    OUTPUT_DIR_NAME + "/",
]

# Files that are usually not helpful as prompt context.
# Add/remove as needed.
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
    lines: int


# ============================================================
# Ignore matching
# ============================================================

class IgnoreMatcher:
    """
    Small gitignore-like matcher implemented with stdlib only.

    Supported patterns:
    - *.ext
    - foo/bar
    - foo/bar/
    - **/something
    - /anchored/from/root
    - !negation

    Notes
    - This is intentionally lightweight and close to gitignore behavior,
      but not a byte-for-byte reimplementation of Git's matcher.
    - For the common repo cleanup patterns used here, it behaves well.
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
            # Directory-only pattern still needs to match descendants.
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


def count_lines(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines())


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
        lines=count_lines(block),
    )


def collect_files(root: Path, ignore_patterns: list[str]) -> list[Path]:
    matcher = IgnoreMatcher(ignore_patterns)
    collected: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)

        # Prune ignored directories in-place so os.walk does not descend into them.
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

def partition_by_soft_threshold(blocks: list[FileBlock], max_files: int, target_lines: int) -> list[list[FileBlock]]:
    if not blocks:
        return []

    total_lines = sum(block.lines for block in blocks)
    capacity = max_files * target_lines

    if total_lines <= capacity:
        groups: list[list[FileBlock]] = []
        current_group: list[FileBlock] = []
        current_lines = 0

        for block in blocks:
            would_exceed = current_group and (current_lines + block.lines > target_lines)
            still_can_open_new_group = len(groups) < max_files - 1

            if would_exceed and still_can_open_new_group:
                groups.append(current_group)
                current_group = [block]
                current_lines = block.lines
            else:
                current_group.append(block)
                current_lines += block.lines

        if current_group:
            groups.append(current_group)

        return groups

    # Too much content for the soft threshold budget.
    # Rebalance across exactly max_files files as evenly as possible,
    # while keeping file blocks whole and preserving order.
    return partition_evenly_sequential(blocks, max_files)


def partition_evenly_sequential(blocks: list[FileBlock], parts: int) -> list[list[FileBlock]]:
    if parts <= 0:
        raise ValueError("parts must be > 0")
    if not blocks:
        return []

    total_lines = sum(block.lines for block in blocks)
    groups: list[list[FileBlock]] = []
    start = 0
    consumed_lines = 0

    for part_index in range(parts):
        remaining_parts = parts - part_index
        remaining_blocks = len(blocks) - start

        if remaining_blocks <= 0:
            break

        if remaining_parts == 1:
            groups.append(blocks[start:])
            break

        target_for_this_part = max(1, round((total_lines - consumed_lines) / remaining_parts))

        current: list[FileBlock] = []
        current_lines = 0

        while start < len(blocks):
            block = blocks[start]

            must_leave_one_per_remaining_part = (len(blocks) - (start + 1)) >= (remaining_parts - 1)
            if not current:
                current.append(block)
                current_lines += block.lines
                start += 1
                continue

            # Decide whether adding the next block moves us farther away from the target.
            current_diff = abs(target_for_this_part - current_lines)
            next_diff = abs(target_for_this_part - (current_lines + block.lines))

            if must_leave_one_per_remaining_part and next_diff <= current_diff:
                current.append(block)
                current_lines += block.lines
                start += 1
            else:
                break

        groups.append(current)
        consumed_lines += current_lines

    # Merge accidental empties if any occurred.
    groups = [g for g in groups if g]
    return groups


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
        line_count = sum(block.lines for block in group)
        print(f"  - part {index}: {len(group)} files, ~{line_count} lines")
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

    # Delete existing export directory to avoid stale files
    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    files = collect_files(root, EXPORT_IGNORE_PATTERNS)
    blocks = [make_file_block(root, path) for path in files]
    groups = partition_by_soft_threshold(blocks, MAX_OUTPUT_FILES, TARGET_LINES_PER_OUTPUT)
    tree_lines = build_tree_lines(root, TREE_IGNORE_PATTERNS)

    write_tree_file(output_dir, tree_lines)
    write_context_files(output_dir, groups)
    print_summary(output_dir, files, groups)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
