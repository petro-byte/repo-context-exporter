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