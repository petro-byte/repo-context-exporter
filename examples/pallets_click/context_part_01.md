# Repository Context Part 1/9

Generated for LLM prompt context.

## .devcontainer/devcontainer.json

```json
{
  "name": "pallets/click",
  "image": "mcr.microsoft.com/devcontainers/python:3",
  "customizations": {
    "vscode": {
      "settings": {
        "python.defaultInterpreterPath": "${workspaceFolder}/.venv",
        "python.terminal.activateEnvInCurrentTerminal": true,
        "python.terminal.launchArgs": [
          "-X",
          "dev"
        ]
      }
    }
  },
  "onCreateCommand": ".devcontainer/on-create-command.sh"
}

```
---

## .devcontainer/on-create-command.sh

```bash
#!/bin/bash
set -e
python3 -m venv --upgrade-deps .venv
. .venv/bin/activate
pip install -r requirements/dev.txt
pip install -e .
pre-commit install --install-hooks

```
---

## .editorconfig

```text
root = true

[*]
indent_style = space
indent_size = 4
insert_final_newline = true
trim_trailing_whitespace = true
end_of_line = lf
charset = utf-8
max_line_length = 88

[*.{css,html,js,json,jsx,scss,ts,tsx,yaml,yml}]
indent_size = 2

```
---

## .github/ISSUE_TEMPLATE/bug-report.md

```markdown
---
name: Bug report
about: Report a bug in Click (not other projects which depend on Click)
---

<!--
This issue tracker is a tool to address bugs in Click itself. Please use
GitHub Discussions or the Pallets Discord for questions about your own code.

Replace this comment with a clear outline of what the bug is.
-->

<!--
Describe how to replicate the bug.

Include a minimal reproducible example that demonstrates the bug.
Include the full traceback if there was an exception.
-->

<!--
Describe the expected behavior that should have happened but didn't.
-->

Environment:

- Python version:
- Click version:

```
---

## .github/ISSUE_TEMPLATE/config.yml

```yaml
blank_issues_enabled: false
contact_links:
  - name: Questions on Discussions
    url: https://github.com/pallets/click/discussions/
    about: Ask questions about your own code on the Discussions tab.
  - name: Questions on Chat
    url: https://discord.gg/pallets
    about: Ask questions about your own code on our Discord chat.

```
---

## .github/ISSUE_TEMPLATE/feature-request.md

```markdown
---
name: Feature request
about: Suggest a new feature for Click
---

<!--
Replace this comment with a description of what the feature should do.
Include details such as links to relevant specs or previous discussions.
-->

<!--
Replace this comment with an example of the problem which this feature
would resolve. Is this problem solvable without changes to Click, such
as by subclassing or using an extension?
-->

```
---

## .github/pull_request_template.md

```markdown
<!--
Before opening a PR, open a ticket describing the issue or feature the
PR will address. An issue is not required for fixing typos in
documentation, or other simple non-code changes.

Replace this comment with a description of the change. Describe how it
addresses the linked ticket.
-->

<!--
Link to relevant issues or previous PRs, one per line. Use "fixes" to
automatically close an issue.

fixes #<issue number>
-->

<!--
Ensure each step in CONTRIBUTING.rst is complete, especially the following:

- Add tests that demonstrate the correct behavior of the change. Tests
  should fail without the change.
- Add or update relevant docs, in the docs folder and in code.
- Add an entry in CHANGES.rst summarizing the change and linking to the issue.
- Add `.. versionchanged::` entries in any relevant code docs.
-->

```
---

## .github/workflows/lock.yaml

```yaml
name: Lock inactive closed issues
# Lock closed issues that have not received any further activity for two weeks.
# This does not close open issues, only humans may do that. It is easier to
# respond to new issues with fresh examples rather than continuing discussions
# on old issues.

on:
  schedule:
    - cron: '0 0 * * *'
permissions:
  issues: write
  pull-requests: write
  discussions: write
concurrency:
  group: lock
jobs:
  lock:
    runs-on: ubuntu-latest
    steps:
      - uses: dessant/lock-threads@1bf7ec25051fe7c00bdd17e6a7cf3d7bfb7dc771 # v5.0.1
        with:
          issue-inactive-days: 14
          pr-inactive-days: 14
          discussion-inactive-days: 14

```
---

## .github/workflows/pre-commit.yaml

```yaml
name: pre-commit
on:
  pull_request:
  push:
    branches: [main, stable]
jobs:
  main:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5.0.1
      - uses: astral-sh/setup-uv@5a7eac68fb9809dea845d802897dc5c723910fa3 # v7.1.3
        with:
          enable-cache: true
          prune-cache: false
      - uses: actions/setup-python@e797f83bcb11b83ae66e0230d6156d7c80228e7c # v6.0.0
        id: setup-python
        with:
          python-version-file: pyproject.toml
      - uses: actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830 # v4.3.0
        with:
          path: ~/.cache/pre-commit
          key: pre-commit|${{ hashFiles('pyproject.toml', '.pre-commit-config.yaml') }}
      - run: uv run --locked --group pre-commit pre-commit run --show-diff-on-failure --color=always --all-files
      - uses: pre-commit-ci/lite-action@5d6cc0eb514c891a40562a58a8e71576c5c7fb43 # v1.1.0
        if: ${{ !cancelled() }}

```
---

## .github/workflows/publish.yaml

```yaml
name: Publish
on:
  push:
    tags: ['*']
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5.0.1
      - uses: astral-sh/setup-uv@5a7eac68fb9809dea845d802897dc5c723910fa3 # v7.1.3
        with:
          enable-cache: true
          prune-cache: false
      - uses: actions/setup-python@e797f83bcb11b83ae66e0230d6156d7c80228e7c # v6.0.0
        with:
          python-version-file: pyproject.toml
      - run: echo "SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)" >> $GITHUB_ENV
      - run: uv build
      - uses: actions/upload-artifact@330a01c490aca151604b8cf639adc76d48f6c5d4 # v5.0.0
        with:
          path: ./dist
  create-release:
    needs: [build]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@018cc2cf5baa6db3ef3c5f8a56943fffe632ef53 # v6.0.0
      - name: create release
        run: gh release create --draft --repo ${{ github.repository }} ${{ github.ref_name }} artifact/*
        env:
          GH_TOKEN: ${{ github.token }}
  publish-pypi:
    needs: [build]
    environment:
      name: publish
      url: https://pypi.org/project/click/${{ github.ref_name }}
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@018cc2cf5baa6db3ef3c5f8a56943fffe632ef53 # v6.0.0
      - uses: pypa/gh-action-pypi-publish@ed0c53931b1dc9bd32cbe73a98c7f6766f8a527e # v1.13.0
        with:
          packages-dir: artifact/

```
---

## .github/workflows/test-flask.yaml

```yaml
name: Test Flask Main
on:
  pull_request:
    paths-ignore: ['docs/**', 'README.md']
  push:
    branches: [main, stable]
    paths-ignore: ['docs/**', 'README.md']
jobs:
  flask-tests:
    name: flask-tests
    runs-on: ubuntu-latest
    steps:
      - uses: astral-sh/setup-uv@5a7eac68fb9809dea845d802897dc5c723910fa3 # v7.1.3
        with:
          enable-cache: true
          prune-cache: false
      - run: git clone https://github.com/pallets/flask
      - run: uv venv --python 3.14
        working-directory: ./flask
      - run: source .venv/bin/activate
        working-directory: ./flask
      - run: uv sync --all-extras
        working-directory: ./flask
      - run: uv run --with "git+https://github.com/pallets/click.git@main" -- pytest
        working-directory: ./flask

```
---

## .github/workflows/tests.yaml

```yaml
name: Tests
on:
  pull_request:
    paths-ignore: ['docs/**', 'README.md']
  push:
    branches: [main, stable]
    paths-ignore: ['docs/**', 'README.md']
jobs:
  tests:
    name: ${{ matrix.name || matrix.python }}
    runs-on: ${{ matrix.os || 'ubuntu-latest' }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - {python: '3.14'}
          - {name: free-threaded-latest, python: '3.14t'}
          - {python: '3.13'}
          - {name: Windows, python: '3.13', os: windows-latest}
          - {name: Mac, python: '3.13', os: macos-latest}
          - {python: '3.12'}
          - {python: '3.11'}
          - {python: '3.10'}
          - {name: PyPy, python: 'pypy-3.11', tox: pypy3.11}
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5.0.1
      - uses: astral-sh/setup-uv@5a7eac68fb9809dea845d802897dc5c723910fa3 # v7.1.3
        with:
          enable-cache: true
          prune-cache: false
      - uses: actions/setup-python@e797f83bcb11b83ae66e0230d6156d7c80228e7c # v6.0.0
        with:
          python-version: ${{ matrix.python }}
      - run: uv run --locked tox run -e ${{ matrix.tox || format('py{0}', matrix.python) }}
  typing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5.0.1
      - uses: astral-sh/setup-uv@5a7eac68fb9809dea845d802897dc5c723910fa3 # v7.1.3
        with:
          enable-cache: true
          prune-cache: false
      - uses: actions/setup-python@e797f83bcb11b83ae66e0230d6156d7c80228e7c # v6.0.0
        with:
          python-version-file: pyproject.toml
      - name: cache mypy
        uses: actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830 # v4.3.0
        with:
          path: ./.mypy_cache
          key: mypy|${{ hashFiles('pyproject.toml') }}
      - run: uv run --locked tox run -e typing

```
---

## .gitignore

```gitignore
.idea/
.vscode/
__pycache__/
dist/
.coverage*
htmlcov/
.tox/
docs/_build/

```
---

## .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: 488940d9de1b658fac229e34c521d75a6ea476f2  # frozen: v0.14.5
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: b6675a113e27a9b18f3d60c05794d62ca80c7ab5  # frozen: 0.9.9
    hooks:
      - id: uv-lock
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: 3e8a8703264a2f4a69428a0aa4dcb512790b2c8c  # frozen: v6.0.0
    hooks:
      - id: check-merge-conflict
      - id: debug-statements
      - id: fix-byte-order-marker
      - id: trailing-whitespace
      - id: end-of-file-fixer

```
---

## .readthedocs.yaml

```yaml
version: 2
# Do not specify sphinx key here to be in full control of build steps.
# https://docs.readthedocs.com/platform/stable/build-customization.html#extend-or-override-the-build-process

build:
  os: ubuntu-24.04
  tools:
    python: '3.13'
  jobs:
    install:
      - echo "Installing dependencies"
      - asdf plugin add uv
      - asdf install uv latest
      - asdf global uv latest
    build:
      html:
        - uv run --group docs sphinx-build -W -b dirhtml docs $READTHEDOCS_OUTPUT/html

```
---

## CHANGES.rst

```text
.. currentmodule:: click

Unreleased

-   Fix handling of ``flag_value`` when ``is_flag=False`` to allow such options to be
    used without an explicit value. :issue:`3084`

Version 8.3.1
--------------

Released 2025-11-15

-   Don't discard pager arguments by correctly using ``subprocess.Popen``. :issue:`3039`
    :pr:`3055`
-   Replace ``Sentinel.UNSET`` default values by ``None`` as they're passed through
    the ``Context.invoke()`` method. :issue:`3066` :issue:`3065` :pr:`3068`
-   Fix conversion of ``Sentinel.UNSET`` happening too early, which caused incorrect
    behavior for multiple parameters using the same name. :issue:`3071` :pr:`3079`
-   Hide ``Sentinel.UNSET`` values as ``None`` when looking up for other parameters
    through the context inside parameter callbacks. :issue:`3136` :pr:`3137`
-   Fix rendering when ``prompt`` and ``confirm`` parameter ``prompt_suffix`` is
    empty. :issue:`3019` :pr:`3021`
-   When ``Sentinel.UNSET`` is found during parsing, it will skip calls to
    ``type_cast_value``. :issue:`3069` :pr:`3090`

Version 8.3.0
--------------

Released 2025-09-17

-   **Improved flag option handling**: Reworked the relationship between ``flag_value``
    and ``default`` parameters for better consistency:

    * The ``default`` parameter value is now preserved as-is and passed directly
      to CLI functions (no more unexpected transformations)
    * Exception: flag options with ``default=True`` maintain backward compatibility
      by defaulting to their ``flag_value``
    * The ``default`` parameter can now be any type (``bool``, ``None``, etc.)
    * Fixes inconsistencies reported in: :issue:`1992` :issue:`2514` :issue:`2610`
      :issue:`3024` :pr:`3030`
-   Allow ``default`` to be set on ``Argument`` for ``nargs = -1``. :issue:`2164`
    :pr:`3030`
-   Show correct auto complete value for ``nargs`` option in combination with flag
    option :issue:`2813`
-   Fix handling of quoted and escaped parameters in Fish autocompletion. :issue:`2995` :pr:`3013`
-   Lazily import ``shutil``. :pr:`3023`
-   Properly forward exception information to resources registered with
    ``click.core.Context.with_resource()``. :issue:`2447` :pr:`3058`
-   Fix regression related to EOF handling in ``CliRunner``. :issue:`2939` :pr:`2940`

Version 8.2.2
-------------

Released 2025-07-31

-   Fix reconciliation of ``default``, ``flag_value`` and ``type`` parameters for
    flag options, as well as parsing and normalization of environment variables.
    :issue:`2952` :pr:`2956`
-   Fix typing issue in ``BadParameter`` and ``MissingParameter`` exceptions for the
    parameter ``param_hint`` that did not allow for a sequence of string where the
    underlying function ``_join_param_hints`` allows for it. :issue:`2777` :pr:`2990`
-   Use the value of ``Enum`` choices to render their default value in help
    screen. Refs :issue:`2911` :pr:`3004`
-   Fix completion for the Z shell (``zsh``) for completion items containing
    colons. :issue:`2703` :pr:`2846`
-   Don't include envvar in error hint when not configured. :issue:`2971` :pr:`2972`
-   Fix a rare race in ``click.testing.StreamMixer``'s finalization that manifested
    as a ``ValueError`` on close in a multi-threaded test session.
    :issue:`2993` :pr:`2991`

Version 8.2.1
-------------

Released 2025-05-20

-   Fix flag value handling for flag options with a provided type. :issue:`2894`
    :issue:`2897` :pr:`2930`
-   Fix shell completion for nested groups. :issue:`2906` :pr:`2907`
-   Flush ``sys.stderr`` at the end of ``CliRunner.invoke``. :issue:`2682`
-   Fix EOF handling for stdin input in CliRunner. :issue:`2787`

Version 8.2.0
-------------

Released 2025-05-10

-   Drop support for Python 3.7, 3.8, and 3.9. :pr:`2588` :pr:`2893`
-   Use modern packaging metadata with ``pyproject.toml`` instead of ``setup.cfg``.
    :pr:`2438`
-   Use ``flit_core`` instead of ``setuptools`` as build backend. :pr:`2543`
-   Deprecate the ``__version__`` attribute. Use feature detection, or
    ``importlib.metadata.version("click")``, instead. :issue:`2598`
-   ``BaseCommand`` is deprecated. ``Command`` is the base class for all
    commands. :issue:`2589`
-   ``MultiCommand`` is deprecated. ``Group`` is the base class for all group
    commands. :issue:`2590`
-   The current parser and related classes and methods, are deprecated.
    :issue:`2205`

    -   ``OptionParser`` and the ``parser`` module, which is a modified copy of
        ``optparse`` in the standard library.
    -   ``Context.protected_args`` is unneeded. ``Context.args`` contains any
        remaining arguments while parsing.
    -   ``Parameter.add_to_parser`` (on both ``Argument`` and ``Option``) is
        unneeded. Parsing works directly without building a separate parser.
    -   ``split_arg_string`` is moved from ``parser`` to ``shell_completion``.

-   Enable deferred evaluation of annotations with
    ``from __future__ import annotations``. :pr:`2270`
-   When generating a command's name from a decorated function's name, the
    suffixes ``_command``, ``_cmd``, ``_group``, and ``_grp`` are removed.
    :issue:`2322`
-   Show the ``types.ParamType.name`` for ``types.Choice`` options within
    ``--help`` message if ``show_choices=False`` is specified.
    :issue:`2356`
-   Do not display default values in prompts when ``Option.show_default`` is
    ``False``. :pr:`2509`
-   Add ``get_help_extra`` method on ``Option`` to fetch the generated extra
    items used in ``get_help_record`` to render help text. :issue:`2516`
    :pr:`2517`
-   Keep stdout and stderr streams independent in ``CliRunner``. Always
    collect stderr output and never raise an exception. Add a new
    output stream to simulate what the user sees in its terminal. Removes
    the ``mix_stderr`` parameter in ``CliRunner``. :issue:`2522` :pr:`2523`
-   ``Option.show_envvar`` now also shows environment variable in error messages.
    :issue:`2695` :pr:`2696`
-   ``Context.close`` will be called on exit. This results in all
    ``Context.call_on_close`` callbacks and context managers added via
    ``Context.with_resource`` to be closed on exit as well. :pr:`2680`
-   Add ``ProgressBar(hidden: bool)`` to allow hiding the progressbar. :issue:`2609`
-   A ``UserWarning`` will be shown when multiple parameters attempt to use the
    same name. :issue:`2396`
-   When using ``Option.envvar`` with ``Option.flag_value``, the ``flag_value``
    will always be used instead of the value of the environment variable.
    :issue:`2746` :pr:`2788`
-   Add ``Choice.get_invalid_choice_message`` method for customizing the
    invalid choice message. :issue:`2621` :pr:`2622`
-   If help is shown because ``no_args_is_help`` is enabled (defaults to ``True``
    for groups, ``False`` for commands), the exit code is 2 instead of 0.
    :issue:`1489` :pr:`1489`
-   Contexts created during shell completion are closed properly, fixing
    a ``ResourceWarning`` when using ``click.File``. :issue:`2644` :pr:`2800`
    :pr:`2767`
-   ``click.edit(filename)`` now supports passing an iterable of filenames in
    case the editor supports editing multiple files at once. Its return type
    is now also typed: ``AnyStr`` if ``text`` is passed, otherwise ``None``.
    :issue:`2067` :pr:`2068`
-   Specialized typing of ``progressbar(length=...)`` as ``ProgressBar[int]``.
    :pr:`2630`
-   Improve ``echo_via_pager`` behaviour in face of errors.
    :issue:`2674`

    -   Terminate the pager in case a generator passed to ``echo_via_pager``
        raises an exception.
    -   Ensure to always close the pipe to the pager process and wait for it
        to terminate.
    -   ``echo_via_pager`` will not ignore ``KeyboardInterrupt`` anymore. This
        allows the user to search for future output of the generator when
        using less and then aborting the program using ctrl-c.

-   ``deprecated: bool | str`` can now be used on options and arguments. This
    previously was only available for ``Command``. The message can now also be
    customised by using a ``str`` instead of a ``bool``. :issue:`2263` :pr:`2271`

    -   ``Command.deprecated`` formatting in ``--help`` changed from
        ``(Deprecated) help`` to ``help (DEPRECATED)``.
    -   Parameters cannot be required nor prompted or an error is raised.
    -   A warning will be printed when something deprecated is used.

-   Add a ``catch_exceptions`` parameter to ``CliRunner``. If
    ``catch_exceptions`` is not passed to ``CliRunner.invoke``, the value
    from ``CliRunner`` is used. :issue:`2817` :pr:`2818`
-   ``Option.flag_value`` will no longer have a default value set based on
    ``Option.default`` if ``Option.is_flag`` is ``False``. This results in
    ``Option.default`` not needing to implement `__bool__`. :pr:`2829`
-   Incorrect ``click.edit`` typing has been corrected. :pr:`2804`
-   ``Choice`` is now generic and supports any iterable value.
    This allows you to use enums and other non-``str`` values. :pr:`2796`
    :issue:`605`
-   Fix setup of help option's defaults when using a custom class on its
    decorator. Removes ``HelpOption``. :issue:`2832` :pr:`2840`

Version 8.1.8
-------------

Released 2024-12-19

-   Fix an issue with type hints for ``click.open_file()``. :issue:`2717`
-   Fix issue where error message for invalid ``click.Path`` displays on
    multiple lines. :issue:`2697`
-   Fixed issue that prevented a default value of ``""`` from being displayed in
    the help for an option. :issue:`2500`
-   The test runner handles stripping color consistently on Windows.
    :issue:`2705`
-   Show correct value for flag default when using ``default_map``.
    :issue:`2632`
-   Fix ``click.echo(color=...)`` passing ``color`` to coloroma so it can be
    forced on Windows. :issue:`2606`.
-   More robust bash version check, fixing problem on Windows with git-bash.
    :issue:`2638`
-   Cache the help option generated by the ``help_option_names`` setting to
    respect its eagerness. :pr:`2811`
-   Replace uses of ``os.system`` with ``subprocess.Popen``. :issue:`1476`
-   Exceptions generated during a command will use the context's ``color``
    setting when being displayed. :issue:`2193`
-   Error message when defining option with invalid name is more descriptive.
    :issue:`2452`
-   Refactor code generating default ``--help`` option to deduplicate code.
    :pr:`2563`
-   Test ``CLIRunner`` resets patched ``_compat.should_strip_ansi``.
    :issue:`2732`


Version 8.1.7
-------------

Released 2023-08-17

-   Fix issue with regex flags in shell completion. :issue:`2581`
-   Bash version detection issues a warning instead of an error. :issue:`2574`
-   Fix issue with completion script for Fish shell. :issue:`2567`


Version 8.1.6
-------------

Released 2023-07-18

-   Fix an issue with type hints for ``@click.group()``. :issue:`2558`


Version 8.1.5
-------------

Released 2023-07-13

-   Fix an issue with type hints for ``@click.command()``, ``@click.option()``, and
    other decorators. Introduce typing tests. :issue:`2558`


Version 8.1.4
-------------

Released 2023-07-06

-   Replace all ``typing.Dict`` occurrences to ``typing.MutableMapping`` for
    parameter hints. :issue:`2255`
-   Improve type hinting for decorators and give all generic types parameters.
    :issue:`2398`
-   Fix return value and type signature of `shell_completion.add_completion_class`
    function. :pr:`2421`
-   Bash version detection doesn't fail on Windows. :issue:`2461`
-   Completion works if there is a dot (``.``) in the program name. :issue:`2166`
-   Improve type annotations for pyright type checker. :issue:`2268`
-   Improve responsiveness of ``click.clear()``. :issue:`2284`
-   Improve command name detection when using Shiv or PEX. :issue:`2332`
-   Avoid showing empty lines if command help text is empty. :issue:`2368`
-   ZSH completion script works when loaded from ``fpath``. :issue:`2344`.
-   ``EOFError`` and ``KeyboardInterrupt`` tracebacks are not suppressed when
    ``standalone_mode`` is disabled. :issue:`2380`
-   ``@group.command`` does not fail if the group was created with a custom
    ``command_class``. :issue:`2416`
-   ``multiple=True`` is allowed for flag options again and does not require
    setting ``default=()``. :issue:`2246, 2292, 2295`
-   Make the decorators returned by ``@argument()`` and ``@option()`` reusable when the
    ``cls`` parameter is used. :issue:`2294`
-   Don't fail when writing filenames to streams with strict errors. Replace invalid
    bytes with the replacement character (``�``). :issue:`2395`
-   Remove unnecessary attempt to detect MSYS2 environment. :issue:`2355`
-   Remove outdated and unnecessary detection of App Engine environment. :pr:`2554`
-   ``echo()`` does not fail when no streams are attached, such as with ``pythonw`` on
    Windows. :issue:`2415`
-   Argument with ``expose_value=False`` do not cause completion to fail. :issue:`2336`


Version 8.1.3
-------------

Released 2022-04-28

-   Use verbose form of ``typing.Callable`` for ``@command`` and
    ``@group``. :issue:`2255`
-   Show error when attempting to create an option with
    ``multiple=True, is_flag=True``. Use ``count`` instead.
    :issue:`2246`


Version 8.1.2
-------------

Released 2022-03-31

-   Fix error message for readable path check that was mixed up with the
    executable check. :pr:`2236`
-   Restore parameter order for ``Path``, placing the ``executable``
    parameter at the end. It is recommended to use keyword arguments
    instead of positional arguments. :issue:`2235`


Version 8.1.1
-------------

Released 2022-03-30

-   Fix an issue with decorator typing that caused type checking to
    report that a command was not callable. :issue:`2227`


Version 8.1.0
-------------

Released 2022-03-28

-   Drop support for Python 3.6. :pr:`2129`
-   Remove previously deprecated code. :pr:`2130`

    -   ``Group.resultcallback`` is renamed to ``result_callback``.
    -   ``autocompletion`` parameter to ``Command`` is renamed to
        ``shell_complete``.
    -   ``get_terminal_size`` is removed, use
        ``shutil.get_terminal_size`` instead.
    -   ``get_os_args`` is removed, use ``sys.argv[1:]`` instead.

-   Rely on :pep:`538` and :pep:`540` to handle selecting UTF-8 encoding
    instead of ASCII. Click's locale encoding detection is removed.
    :issue:`2198`
-   Single options boolean flags with ``show_default=True`` only show
    the default if it is ``True``. :issue:`1971`
-   The ``command`` and ``group`` decorators can be applied with or
    without parentheses. :issue:`1359`
-   The ``Path`` type can check whether the target is executable.
    :issue:`1961`
-   ``Command.show_default`` overrides ``Context.show_default``, instead
    of the other way around. :issue:`1963`
-   Parameter decorators and ``@group`` handles ``cls=None`` the same as
    not passing ``cls``. ``@option`` handles ``help=None`` the same as
    not passing ``help``. :issue:`#1959`
-   A flag option with ``required=True`` requires that the flag is
    passed instead of choosing the implicit default value. :issue:`1978`
-   Indentation in help text passed to ``Option`` and ``Command`` is
    cleaned the same as using the ``@option`` and ``@command``
    decorators does. A command's ``epilog`` and ``short_help`` are also
    processed. :issue:`1985`
-   Store unprocessed ``Command.help``, ``epilog`` and ``short_help``
    strings. Processing is only done when formatting help text for
    output. :issue:`2149`
-   Allow empty str input for ``prompt()`` when
    ``confirmation_prompt=True`` and ``default=""``. :issue:`2157`
-   Windows glob pattern expansion doesn't fail if a value is an invalid
    pattern. :issue:`2195`
-   It's possible to pass a list of ``params`` to ``@command``. Any
    params defined with decorators are appended to the passed params.
    :issue:`2131`.
-   ``@command`` decorator is annotated as returning the correct type if
    a ``cls`` argument is used. :issue:`2211`
-   A ``Group`` with ``invoke_without_command=True`` and ``chain=False``
    will invoke its result callback with the group function's return
    value. :issue:`2124`
-   ``to_info_dict`` will not fail if a ``ParamType`` doesn't define a
    ``name``. :issue:`2168`
-   Shell completion prioritizes option values with option prefixes over
    new options. :issue:`2040`
-   Options that get an environment variable value using
    ``autoenvvar_prefix`` treat an empty value as ``None``, consistent
    with a direct ``envvar``. :issue:`2146`


Version 8.0.4
-------------

Released 2022-02-18

-   ``open_file`` recognizes ``Path("-")`` as a standard stream, the
    same as the string ``"-"``. :issue:`2106`
-   The ``option`` and ``argument`` decorators preserve the type
    annotation of the decorated function. :pr:`2155`
-   A callable default value can customize its help text by overriding
    ``__str__`` instead of always showing ``(dynamic)``. :issue:`2099`
-   Fix a typo in the Bash completion script that affected file and
    directory completion. If this script was generated by a previous
    version, it should be regenerated. :issue:`2163`
-   Fix typing for ``echo`` and ``secho`` file argument.
    :issue:`2174, 2185`


Version 8.0.3
-------------

Released 2021-10-10

-   Fix issue with ``Path(resolve_path=True)`` type creating invalid
    paths. :issue:`2088`
-   Importing ``readline`` does not cause the ``confirm()`` prompt to
    disappear when pressing backspace. :issue:`2092`
-   Any default values injected by ``invoke()`` are cast to the
    corresponding parameter's type. :issue:`2089, 2090`


Version 8.0.2
-------------

Released 2021-10-08

-   ``is_bool_flag`` is not set to ``True`` if ``is_flag`` is ``False``.
    :issue:`1925`
-   Bash version detection is locale independent. :issue:`1940`
-   Empty ``default`` value is not shown for ``multiple=True``.
    :issue:`1969`
-   Fix shell completion for arguments that start with a forward slash
    such as absolute file paths. :issue:`1929`
-   ``Path`` type with ``resolve_path=True`` resolves relative symlinks
    to be relative to the containing directory. :issue:`1921`
-   Completion does not skip Python's resource cleanup when exiting,
    avoiding some unexpected warning output. :issue:`1738, 2017`
-   Fix type annotation for ``type`` argument in ``prompt`` function.
    :issue:`2062`
-   Fix overline and italic styles, which were incorrectly added when
    adding underline. :pr:`2058`
-   An option with ``count=True`` will not show "[x>=0]" in help text.
    :issue:`2072`
-   Default values are not cast to the parameter type twice during
    processing. :issue:`2085`
-   Options with ``multiple`` and ``flag_value`` use the flag value
    instead of leaving an internal placeholder. :issue:`2001`


Version 8.0.1
-------------

Released 2021-05-19

-   Mark top-level names as exported so type checking understand imports
    in user projects. :issue:`1879`
-   Annotate ``Context.obj`` as ``Any`` so type checking allows all
    operations on the arbitrary object. :issue:`1885`
-   Fix some types that weren't available in Python 3.6.0. :issue:`1882`
-   Fix type checking for iterating over ``ProgressBar`` object.
    :issue:`1892`
-   The ``importlib_metadata`` backport package is installed on Python <
    3.8. :issue:`1889`
-   Arguments with ``nargs=-1`` only use env var value if no command
    line values are given. :issue:`1903`
-   Flag options guess their type from ``flag_value`` if given, like
    regular options do from ``default``. :issue:`1886`
-   Added documentation that custom parameter types may be passed
    already valid values in addition to strings. :issue:`1898`
-   Resolving commands returns the name that was given, not
    ``command.name``, fixing an unintended change to help text and
    ``default_map`` lookups. When using patterns like ``AliasedGroup``,
    override ``resolve_command`` to change the name that is returned if
    needed. :issue:`1895`
-   If a default value is invalid, it does not prevent showing help
    text. :issue:`1889`
-   Pass ``windows_expand_args=False`` when calling the main command to
    disable pattern expansion on Windows. There is no way to escape
    patterns in CMD, so if the program needs to pass them on as-is then
    expansion must be disabled. :issue:`1901`


Version 8.0.0
-------------

Released 2021-05-11

-   Drop support for Python 2 and 3.5.
-   Colorama is always installed on Windows in order to provide style
    and color support. :pr:`1784`
-   Adds a repr to Command, showing the command name for friendlier
    debugging. :issue:`1267`, :pr:`1295`
-   Add support for distinguishing the source of a command line
    parameter. :issue:`1264`, :pr:`1329`
-   Add an optional parameter to ``ProgressBar.update`` to set the
    ``current_item``. :issue:`1226`, :pr:`1332`
-   ``version_option`` uses ``importlib.metadata`` (or the
    ``importlib_metadata`` backport) instead of ``pkg_resources``. The
    version is detected based on the package name, not the entry point
    name. The Python package name must match the installed package
    name, or be passed with ``package_name=``. :issue:`1582`
-   If validation fails for a prompt with ``hide_input=True``, the value
    is not shown in the error message. :issue:`1460`
-   An ``IntRange`` or ``FloatRange`` option shows the accepted range in
    its help text. :issue:`1525`, :pr:`1303`
-   ``IntRange`` and ``FloatRange`` bounds can be open (``<``) instead
    of closed (``<=``) by setting ``min_open`` and ``max_open``. Error
    messages have changed to reflect this. :issue:`1100`
-   An option defined with duplicate flag names (``"--foo/--foo"``)
    raises a ``ValueError``. :issue:`1465`
-   ``echo()`` will not fail when using pytest's ``capsys`` fixture on
    Windows. :issue:`1590`
-   Resolving commands returns the canonical command name instead of the
    matched name. This makes behavior such as help text and
    ``Context.invoked_subcommand`` consistent when using patterns like
    ``AliasedGroup``. :issue:`1422`
-   The ``BOOL`` type accepts the values "on" and "off". :issue:`1629`
-   A ``Group`` with ``invoke_without_command=True`` will always invoke
    its result callback. :issue:`1178`
-   ``nargs == -1`` and ``nargs > 1`` is parsed and validated for
    values from environment variables and defaults. :issue:`729`
-   Detect the program name when executing a module or package with
    ``python -m name``. :issue:`1603`
-   Include required parent arguments in help synopsis of subcommands.
    :issue:`1475`
-   Help for boolean flags with ``show_default=True`` shows the flag
    name instead of ``True`` or ``False``. :issue:`1538`
-   Non-string objects passed to ``style()`` and ``secho()`` will be
    converted to string. :pr:`1146`
-   ``edit(require_save=True)`` will detect saves for editors that exit
    very fast on filesystems with 1 second resolution. :pr:`1050`
-   New class attributes make it easier to use custom core objects
    throughout an entire application. :pr:`938`

    -   ``Command.context_class`` controls the context created when
        running the command.
    -   ``Context.invoke`` creates new contexts of the same type, so a
        custom type will persist to invoked subcommands.
    -   ``Context.formatter_class`` controls the formatter used to
        generate help and usage.
    -   ``Group.command_class`` changes the default type for
        subcommands with ``@group.command()``.
    -   ``Group.group_class`` changes the default type for subgroups
        with ``@group.group()``. Setting it to ``type`` will create
        subgroups of the same type as the group itself.
    -   Core objects use ``super()`` consistently for better support of
        subclassing.

-   Use ``Context.with_resource()`` to manage resources that would
    normally be used in a ``with`` statement, allowing them to be used
    across subcommands and callbacks, then cleaned up when the context
    ends. :pr:`1191`
-   The result object returned by the test runner's ``invoke()`` method
    has a ``return_value`` attribute with the value returned by the
    invoked command. :pr:`1312`
-   Required arguments with the ``Choice`` type show the choices in
    curly braces to indicate that one is required (``{a|b|c}``).
    :issue:`1272`
-   If only a name is passed to ``option()``, Click suggests renaming it
    to ``--name``. :pr:`1355`
-   A context's ``show_default`` parameter defaults to the value from
    the parent context. :issue:`1565`
-   ``click.style()`` can output 256 and RGB color codes. Most modern
    terminals support these codes. :pr:`1429`
-   When using ``CliRunner.invoke()``, the replaced ``stdin`` file has
    ``name`` and ``mode`` attributes. This lets ``File`` options with
    the ``-`` value match non-testing behavior. :issue:`1064`
-   When creating a ``Group``, allow passing a list of commands instead
    of a dict. :issue:`1339`
-   When a long option name isn't valid, use ``difflib`` to make better
    suggestions for possible corrections. :issue:`1446`
-   Core objects have a ``to_info_dict()`` method. This gathers
    information about the object's structure that could be useful for a
    tool generating user-facing documentation. To get the structure of
    an entire CLI, use ``Context(cli).to_info_dict()``. :issue:`461`
-   Redesign the shell completion system. :issue:`1484`, :pr:`1622`

    -   Support Bash >= 4.4, Zsh, and Fish, with the ability for
        extensions to add support for other shells.
    -   Allow commands, groups, parameters, and types to override their
        completions suggestions.
    -   Groups complete the names commands were registered with, which
        can differ from the name they were created with.
    -   The ``autocompletion`` parameter for options and arguments is
        renamed to ``shell_complete``. The function must take
        ``ctx, param, incomplete``, must do matching rather than return
        all values, and must return a list of strings or a list of
        ``CompletionItem``. The old name and behavior is deprecated and
        will be removed in 8.1.
    -   The env var values used to start completion have changed order.
        The shell now comes first, such as ``{shell}_source`` rather
        than ``source_{shell}``, and is always required.

-   Completion correctly parses command line strings with incomplete
    quoting or escape sequences. :issue:`1708`
-   Extra context settings (``obj=...``, etc.) are passed on to the
    completion system. :issue:`942`
-   Include ``--help`` option in completion. :pr:`1504`
-   ``ParameterSource`` is an ``enum.Enum`` subclass. :issue:`1530`
-   Boolean and UUID types strip surrounding space before converting.
    :issue:`1605`
-   Adjusted error message from parameter type validation to be more
    consistent. Quotes are used to distinguish the invalid value.
    :issue:`1605`
-   The default value for a parameter with ``nargs`` > 1 and
    ``multiple=True`` must be a list of tuples. :issue:`1649`
-   When getting the value for a parameter, the default is tried in the
    same section as other sources to ensure consistent processing.
    :issue:`1649`
-   All parameter types accept a value that is already the correct type.
    :issue:`1649`
-   For shell completion, an argument is considered incomplete if its
    value did not come from the command line args. :issue:`1649`
-   Added ``ParameterSource.PROMPT`` to track parameter values that were
    prompted for. :issue:`1649`
-   Options with ``nargs`` > 1 no longer raise an error if a default is
    not given. Parameters with ``nargs`` > 1 default to ``None``, and
    parameters with ``multiple=True`` or ``nargs=-1`` default to an
    empty tuple. :issue:`472`
-   Handle empty env vars as though the option were not passed. This
    extends the change introduced in 7.1 to be consistent in more cases.
    :issue:`1285`
-   ``Parameter.get_default()`` checks ``Context.default_map`` to
    handle overrides consistently in help text, ``invoke()``, and
    prompts. :issue:`1548`
-   Add ``prompt_required`` param to ``Option``. When set to ``False``,
    the user will only be prompted for an input if no value was passed.
    :issue:`736`
-   Providing the value to an option can be made optional through
    ``is_flag=False``, and the value can instead be prompted for or
    passed in as a default value.
    :issue:`549, 736, 764, 921, 1015, 1618`
-   Fix formatting when ``Command.options_metavar`` is empty. :pr:`1551`
-   Revert adding space between option help text that wraps.
    :issue:`1831`
-   The default value passed to ``prompt`` will be cast to the correct
    type like an input value would be. :pr:`1517`
-   Automatically generated short help messages will stop at the first
    ending of a phrase or double linebreak. :issue:`1082`
-   Skip progress bar render steps for efficiency with very fast
    iterators by setting ``update_min_steps``. :issue:`676`
-   Respect ``case_sensitive=False`` when doing shell completion for
    ``Choice`` :issue:`1692`
-   Use ``mkstemp()`` instead of ``mktemp()`` in pager implementation.
    :issue:`1752`
-   If ``Option.show_default`` is a string, it is displayed even if
    ``default`` is ``None``. :issue:`1732`
-   ``click.get_terminal_size()`` is deprecated and will be removed in
    8.1. Use :func:`shutil.get_terminal_size` instead. :issue:`1736`
-   Control the location of the temporary directory created by
    ``CLIRunner.isolated_filesystem`` by passing ``temp_dir``. A custom
    directory will not be removed automatically. :issue:`395`
-   ``click.confirm()`` will prompt until input is given if called with
    ``default=None``. :issue:`1381`
-   Option prompts validate the value with the option's callback in
    addition to its type. :issue:`457`
-   ``confirmation_prompt`` can be set to a custom string. :issue:`723`
-   Allow styled output in Jupyter on Windows. :issue:`1271`
-   ``style()`` supports the ``strikethrough``, ``italic``, and
    ``overline`` styles. :issue:`805, 1821`
-   Multiline marker is removed from short help text. :issue:`1597`
-   Restore progress bar behavior of echoing only the label if the file
    is not a TTY. :issue:`1138`
-   Progress bar output is shown even if execution time is less than 0.5
    seconds. :issue:`1648`
-   Progress bar ``item_show_func`` shows the current item, not the
    previous item. :issue:`1353`
-   The ``Path`` param type can be passed ``path_type=pathlib.Path`` to
    return a path object instead of a string. :issue:`405`
-   ``TypeError`` is raised when parameter with ``multiple=True`` or
    ``nargs > 1`` has non-iterable default. :issue:`1749`
-   Add a ``pass_meta_key`` decorator for passing a key from
    ``Context.meta``. This is useful for extensions using ``meta`` to
    store information. :issue:`1739`
-   ``Path`` ``resolve_path`` resolves symlinks on Windows Python < 3.8.
    :issue:`1813`
-   Command deprecation notice appears at the start of the help text, as
    well as in the short help. The notice is not in all caps.
    :issue:`1791`
-   When taking arguments from ``sys.argv`` on Windows, glob patterns,
    user dir, and env vars are expanded. :issue:`1096`
-   Marked messages shown by the CLI with ``gettext()`` to allow
    applications to translate Click's built-in strings. :issue:`303`
-   Writing invalid characters  to ``stderr`` when using the test runner
    does not raise a ``UnicodeEncodeError``. :issue:`848`
-   Fix an issue where ``readline`` would clear the entire ``prompt()``
    line instead of only the input when pressing backspace. :issue:`665`
-   Add all kwargs passed to ``Context.invoke()`` to ``ctx.params``.
    Fixes an inconsistency when nesting ``Context.forward()`` calls.
    :issue:`1568`
-   The ``MultiCommand.resultcallback`` decorator is renamed to
    ``result_callback``. The old name is deprecated. :issue:`1160`
-   Fix issues with ``CliRunner`` output when using ``echo_stdin=True``.
    :issue:`1101`
-   Fix a bug of ``click.utils.make_default_short_help`` for which the
    returned string could be as long as ``max_width + 3``. :issue:`1849`
-   When defining a parameter, ``default`` is validated with
    ``multiple`` and ``nargs``. More validation is done for values being
    processed as well. :issue:`1806`
-   ``HelpFormatter.write_text`` uses the full line width when wrapping
    text. :issue:`1871`


Version 7.1.2
-------------

Released 2020-04-27

-   Revert applying shell quoting to commands for ``echo_with_pager``
    and ``edit``. This was intended to allows spaces in commands, but
    caused issues if the string was actually a command and arguments, or
    on Windows. Instead, the string must be quoted manually as it should
    appear on the command line. :issue:`1514`


Version 7.1.1
-------------

Released 2020-03-09

-   Fix ``ClickException`` output going to stdout instead of stderr.
    :issue:`1495`


Version 7.1
-----------

Released 2020-03-09

-   Fix PyPI package name, "click" is lowercase again.
-   Fix link in ``unicode_literals`` error message. :pr:`1151`
-   Add support for colored output on UNIX Jupyter notebooks.
    :issue:`1185`
-   Operations that strip ANSI controls will strip the cursor hide/show
    sequences. :issue:`1216`
-   Remove unused compat shim for ``bytes``. :pr:`1195`
-   Expand testing around termui, especially getchar on Windows.
    :issue:`1116`
-   Fix output on Windows Python 2.7 built with MSVC 14. :pr:`1342`
-   Fix ``OSError`` when running in MSYS2. :issue:`1338`
-   Fix ``OSError`` when redirecting to ``NUL`` stream on Windows.
    :issue:`1065`
-   Fix memory leak when parsing Unicode arguments on Windows.
    :issue:`1136`
-   Fix error in new AppEngine environments. :issue:`1462`
-   Always return one of the passed choices for ``click.Choice``
    :issue:`1277`, :pr:`1318`
-   Add ``no_args_is_help`` option to ``click.Command``, defaults to
    False :pr:`1167`
-   Add ``show_default`` parameter to ``Context`` to enable showing
    defaults globally. :issue:`1018`
-   Handle ``env MYPATH=''`` as though the option were not passed.
    :issue:`1196`
-   It is once again possible to call ``next(bar)`` on an active
    progress bar instance. :issue:`1125`
-   ``open_file`` with ``atomic=True`` retains permissions of existing
    files and respects the current umask for new files. :issue:`1376`
-   When using the test ``CliRunner`` with ``mix_stderr=False``, if
    ``result.stderr`` is empty it will not raise a ``ValueError``.
    :issue:`1193`
-   Remove the unused ``mix_stderr`` parameter from
    ``CliRunner.invoke``. :issue:`1435`
-   Fix ``TypeError`` raised when using bool flags and specifying
    ``type=bool``. :issue:`1287`
-   Newlines in option help text are replaced with spaces before
    re-wrapping to avoid uneven line breaks. :issue:`834`
-   ``MissingParameter`` exceptions are printable in the Python
    interpreter. :issue:`1139`
-   Fix how default values for file-type options are shown during
    prompts. :issue:`914`
-   Fix environment variable automatic generation for commands
    containing ``-``. :issue:`1253`
-   Option help text replaces newlines with spaces when rewrapping, but
    preserves paragraph breaks, fixing multiline formatting.
    :issue:`834, 1066, 1397`
-   Option help text that is wrapped adds an extra newline at the end to
    distinguish it from the next option. :issue:`1075`
-   Consider ``sensible-editor`` when determining the editor to use for
    ``click.edit()``. :pr:`1469`
-   Arguments to system calls such as the executable path passed to
    ``click.edit`` can contains spaces. :pr:`1470`
-   Add ZSH completion autoloading and error handling. :issue:`1348`
-   Add a repr to ``Command``, ``Group``, ``Option``, and ``Argument``,
    showing the name for friendlier debugging. :issue:`1267`
-   Completion doesn't consider option names if a value starts with
    ``-`` after the ``--`` separator. :issue:`1247`
-   ZSH completion escapes special characters in values. :pr:`1418`
-   Add completion support for Fish shell. :pr:`1423`
-   Decoding bytes option values falls back to UTF-8 in more cases.
    :pr:`1468`
-   Make the warning about old 2-arg parameter callbacks a deprecation
    warning, to be removed in 8.0. This has been a warning since Click
    2.0. :pr:`1492`
-   Adjust error messages to standardize the types of quotes used so
    they match error messages from Python.


Version 7.0
-----------

Released 2018-09-25

-   Drop support for Python 2.6 and 3.3. :pr:`967, 976`
-   Wrap ``click.Choice``'s missing message. :issue:`202`, :pr:`1000`
-   Add native ZSH autocompletion support. :issue:`323`, :pr:`865`
-   Document that ANSI color info isn't parsed from bytearrays in Python
    2. :issue:`334`
-   Document byte-stripping behavior of ``CliRunner``. :issue:`334`,
    :pr:`1010`
-   Usage errors now hint at the ``--help`` option. :issue:`393`,
    :pr:`557`
-   Implement streaming pager. :issue:`409`, :pr:`889`
-   Extract bar formatting to its own method. :pr:`414`
-   Add ``DateTime`` type for converting input in given date time
    formats. :pr:`423`
-   ``secho``'s first argument can now be ``None``, like in ``echo``.
    :pr:`424`
-   Fixes a ``ZeroDivisionError`` in ``ProgressBar.make_step``, when the
    arg passed to the first call of ``ProgressBar.update`` is 0.
    :issue:`447`, :pr:`1012`
-   Show progressbar only if total execution time is visible. :pr:`487`
-   Added the ability to hide commands and options from help. :pr:`500`
-   Document that options can be ``required=True``. :issue:`514`,
    :pr:`1022`
-   Non-standalone calls to ``Context.exit`` return the exit code,
    rather than calling ``sys.exit``. :issue:`667`, :pr:`533, 1098`
-   ``click.getchar()`` returns Unicode in Python 3 on Windows,
    consistent with other platforms. :issue:`537, 821, 822, 1088`,
    :pr:`1108`
-   Added ``FloatRange`` type. :pr:`538, 553`
-   Added support for bash completion of ``type=click.Choice`` for
    ``Options`` and ``Arguments``. :issue:`535`, :pr:`681`
-   Only allow one positional arg for ``Argument`` parameter
    declaration. :issue:`568, 574`, :pr:`1014`
-   Add ``case_sensitive=False`` as an option to Choice. :issue:`569`
-   ``click.getchar()`` correctly raises ``KeyboardInterrupt`` on "^C"
    and ``EOFError`` on "^D" on Linux. :issue:`583`, :pr:`1115`
-   Fix encoding issue with ``click.getchar(echo=True)`` on Linux.
    :pr:`1115`
-   ``param_hint`` in errors now derived from param itself.
    :issue:`598, 704`, :pr:`709`
-   Add a test that ensures that when an argument is formatted into a
    usage error, its metavar is used, not its name. :pr:`612`
-   Allow setting ``prog_name`` as extra in ``CliRunner.invoke``.
    :issue:`616`, :pr:`999`
-   Help text taken from docstrings truncates at the ``\f`` form feed
    character, useful for hiding Sphinx-style parameter documentation.
    :pr:`629, 1091`
-   ``launch`` now works properly under Cygwin. :pr:`650`
-   Update progress after iteration. :issue:`651`, :pr:`706`
-   ``CliRunner.invoke`` now may receive ``args`` as a string
    representing a Unix shell command. :pr:`664`
-   Make ``Argument.make_metavar()`` default to type metavar. :pr:`675`
-   Add documentation for ``ignore_unknown_options``. :pr:`684`
-   Add bright colors support for ``click.style`` and fix the reset
    option for parameters ``fg`` and ``bg``. :issue:`703`, :pr:`809`
-   Add ``show_envvar`` for showing environment variables in help.
    :pr:`710`
-   Avoid ``BrokenPipeError`` during interpreter shutdown when stdout or
    stderr is a closed pipe. :issue:`712`, :pr:`1106`
-   Document customizing option names. :issue:`725`, :pr:`1016`
-   Disable ``sys._getframes()`` on Python interpreters that don't
    support it. :pr:`728`
-   Fix bug in test runner when calling ``sys.exit`` with ``None``.
    :pr:`739`
-   Clarify documentation on command line options. :issue:`741`,
    :pr:`1003`
-   Fix crash on Windows console. :issue:`744`
-   Fix bug that caused bash completion to give improper completions on
    chained commands. :issue:`754`, :pr:`774`
-   Added support for dynamic bash completion from a user-supplied
    callback. :pr:`755`
-   Added support for bash completions containing spaces. :pr:`773`
-   Allow autocompletion function to determine whether or not to return
    completions that start with the incomplete argument. :issue:`790`,
    :pr:`806`
-   Fix option naming routine to match documentation and be
    deterministic. :issue:`793`, :pr:`794`
-   Fix path validation bug. :issue:`795`, :pr:`1020`
-   Add test and documentation for ``Option`` naming: functionality.
    :pr:`799`
-   Update doc to match arg name for ``path_type``. :pr:`801`
-   Raw strings added so correct escaping occurs. :pr:`807`
-   Fix 16k character limit of ``click.echo`` on Windows. :issue:`816`,
    :pr:`819`
-   Overcome 64k character limit when writing to binary stream on
    Windows 7. :issue:`825`, :pr:`830`
-   Add bool conversion for "t" and "f". :pr:`842`
-   ``NoSuchOption`` errors take ``ctx`` so that ``--help`` hint gets
    printed in error output. :pr:`860`
-   Fixed the behavior of Click error messages with regards to Unicode
    on 2.x and 3.x. Message is now always Unicode and the str and
    Unicode special methods work as you expect on that platform.
    :issue:`862`
-   Progress bar now uses stderr by default. :pr:`863`
-   Add support for auto-completion documentation. :issue:`866`,
    :pr:`869`
-   Allow ``CliRunner`` to separate stdout and stderr. :pr:`868`
-   Fix variable precedence. :issue:`873`, :pr:`874`
-   Fix invalid escape sequences. :pr:`877`
-   Fix ``ResourceWarning`` that occurs during some tests. :pr:`878`
-   When detecting a misconfigured locale, don't fail if the ``locale``
    command fails. :pr:`880`
-   Add ``case_sensitive=False`` as an option to ``Choice`` types.
    :pr:`887`
-   Force stdout/stderr writable. This works around issues with badly
    patched standard streams like those from Jupyter. :pr:`918`
-   Fix completion of subcommand options after last argument
    :issue:`919`, :pr:`930`
-   ``_AtomicFile`` now uses the ``realpath`` of the original filename
    so that changing the working directory does not affect it. :pr:`920`
-   Fix incorrect completions when defaults are present :issue:`925`,
    :pr:`930`
-   Add copy option attrs so that custom classes can be re-used.
    :issue:`926`, :pr:`994`
-   "x" and "a" file modes now use stdout when file is ``"-"``.
    :pr:`929`
-   Fix missing comma in ``__all__`` list. :pr:`935`
-   Clarify how parameters are named. :issue:`949`, :pr:`1009`
-   Stdout is now automatically set to non blocking. :pr:`954`
-   Do not set options twice. :pr:`962`
-   Move ``fcntl`` import. :pr:`965`
-   Fix Google App Engine ``ImportError``. :pr:`995`
-   Better handling of help text for dynamic default option values.
    :pr:`996`
-   Fix ``get_winter_size()`` so it correctly returns ``(0,0)``.
    :pr:`997`
-   Add test case checking for custom param type. :pr:`1001`
-   Allow short width to address cmd formatting. :pr:`1002`
-   Add details about Python version support. :pr:`1004`
-   Added deprecation flag to commands. :pr:`1005`
-   Fixed issues where ``fd`` was undefined. :pr:`1007`
-   Fix formatting for short help. :pr:`1008`
-   Document how ``auto_envvar_prefix`` works with command groups.
    :pr:`1011`
-   Don't add newlines by default for progress bars. :pr:`1013`
-   Use Python sorting order for ZSH completions. :issue:`1047`,
    :pr:`1059`
-   Document that parameter names are converted to lowercase by default.
    :pr:`1055`
-   Subcommands that are named by the function now automatically have
    the underscore replaced with a dash. If you register a function
    named ``my_command`` it becomes ``my-command`` in the command line
    interface.
-   Hide hidden commands and options from completion. :issue:`1058`,
    :pr:`1061`
-   Fix absolute import blocking Click from being vendored into a
    project on Windows. :issue:`1068`, :pr:`1069`
-   Fix issue where a lowercase ``auto_envvar_prefix`` would not be
    converted to uppercase. :pr:`1105`


Version 6.7
-----------

Released 2017-01-06

-   Make ``click.progressbar`` work with ``codecs.open`` files.
    :pr:`637`
-   Fix bug in bash completion with nested subcommands. :pr:`639`
-   Fix test runner not saving caller env correctly. :pr:`644`
-   Fix handling of SIGPIPE. :pr:`62`
-   Deal with broken Windows environments such as Google App Engine's.
    :issue:`711`


Version 6.6
-----------

Released 2016-04-04

-   Fix bug in ``click.Path`` where it would crash when passed a ``-``.
    :issue:`551`


Version 6.4
-----------

Released 2016-03-24

-   Fix bug in bash completion where click would discard one or more
    trailing arguments. :issue:`471`


Version 6.3
-----------

Released 2016-02-22

-   Fix argument checks for interpreter invoke with ``-m`` and ``-c`` on
    Windows.
-   Fixed a bug that cased locale detection to error out on Python 3.


Version 6.2
-----------

Released 2015-11-27

-   Correct fix for hidden progress bars.


Version 6.1
-----------

Released 2015-11-27

-   Resolved an issue with invisible progress bars no longer rendering.
-   Disable chain commands with subcommands as they were inherently
    broken.
-   Fix ``MissingParameter`` not working without parameters passed.


Version 6.0
-----------

Released 2015-11-24, codename "pow pow"

-   Optimized the progressbar rendering to not render when it did not
    actually change.
-   Explicitly disallow ``nargs=-1`` with a set default.
-   The context is now closed before it's popped from the stack.
-   Added support for short aliases for the false flag on toggles.
-   Click will now attempt to aid you with debugging locale errors
    better by listing with the help of the OS what locales are
    available.
-   Click used to return byte strings on Python 2 in some unit-testing
    situations. This has been fixed to correctly return unicode strings
    now.
-   For Windows users on Python 2, Click will now handle Unicode more
    correctly handle Unicode coming in from the system. This also has
    the disappointing side effect that filenames will now be always
    unicode by default in the ``Path`` type which means that this can
    introduce small bugs for code not aware of this.
-   Added a ``type`` parameter to ``Path`` to force a specific string
    type on the value.
-   For users running Python on Windows the ``echo`` and ``prompt``
    functions now work with full unicode functionality in the Python
    windows console by emulating an output stream. This also applies to
    getting the virtual output and input streams via
    ``click.get_text_stream(...)``.
-   Unittests now always force a certain virtual terminal width.
-   Added support for allowing dashes to indicate standard streams to
    the ``Path`` type.
-   Multi commands in chain mode no longer propagate arguments left over
    from parsing to the callbacks. It's also now disallowed through an
    exception when optional arguments are attached to multi commands if
    chain mode is enabled.
-   Relaxed restriction that disallowed chained commands to have other
    chained commands as child commands.
-   Arguments with positive nargs can now have defaults implemented.
    Previously this configuration would often result in slightly
    unexpected values be returned.


Version 5.1
-----------

Released 2015-08-17

-   Fix a bug in ``pass_obj`` that would accidentally pass the context
    too.


Version 5.0
-----------

Released 2015-08-16, codename "tok tok"

-   Removed various deprecated functionality.
-   Atomic files now only accept the ``w`` mode.
-   Change the usage part of help output for very long commands to wrap
    their arguments onto the next line, indented by 4 spaces.
-   Fix a bug where return code and error messages were incorrect when
    using ``CliRunner``.
-   Added ``get_current_context``.
-   Added a ``meta`` dictionary to the context which is shared across
    the linked list of contexts to allow click utilities to place state
    there.
-   Introduced ``Context.scope``.
-   The ``echo`` function is now threadsafe: It calls the ``write``
    method of the underlying object only once.
-   ``prompt(hide_input=True)`` now prints a newline on ``^C``.
-   Click will now warn if users are using ``unicode_literals``.
-   Click will now ignore the ``PAGER`` environment variable if it is
    empty or contains only whitespace.
-   The ``click-contrib`` GitHub organization was created.


Version 4.1
-----------

Released 2015-07-14

-   Fix a bug where error messages would include a trailing ``None``
    string.
-   Fix a bug where Click would crash on docstrings with trailing
    newlines.
-   Support streams with encoding set to ``None`` on Python 3 by barfing
    with a better error.
-   Handle ^C in less-pager properly.
-   Handle return value of ``None`` from ``sys.getfilesystemencoding``
-   Fix crash when writing to unicode files with ``click.echo``.
-   Fix type inference with multiple options.


Version 4.0
-----------

Released 2015-03-31, codename "zoom zoom"

-   Added ``color`` parameters to lots of interfaces that directly or
    indirectly call into echoing. This previously was always
    autodetection (with the exception of the ``echo_via_pager``
    function). Now you can forcefully enable or disable it, overriding
    the auto detection of Click.
-   Added an ``UNPROCESSED`` type which does not perform any type
    changes which simplifies text handling on 2.x / 3.x in some special
    advanced usecases.
-   Added ``NoSuchOption`` and ``BadOptionUsage`` exceptions for more
    generic handling of errors.
-   Added support for handling of unprocessed options which can be
    useful in situations where arguments are forwarded to underlying
    tools.
-   Added ``max_content_width`` parameter to the context which can be
    used to change the maximum width of help output. By default Click
    will not format content for more than 80 characters width.
-   Added support for writing prompts to stderr.
-   Fix a bug when showing the default for multiple arguments.
-   Added support for custom subclasses to ``option`` and ``argument``.
-   Fix bug in ``clear()`` on Windows when colorama is installed.
-   Reject ``nargs=-1`` for options properly. Options cannot be
    variadic.
-   Fixed an issue with bash completion not working properly for
    commands with non ASCII characters or dashes.
-   Added a way to manually update the progressbar.
-   Changed the formatting of missing arguments. Previously the internal
    argument name was shown in error messages, now the metavar is shown
    if passed. In case an automated metavar is selected, it's stripped
    of extra formatting first.


Version 3.3
-----------

Released 2014-09-08

-   Fixed an issue with error reporting on Python 3 for invalid
    forwarding of commands.


Version 3.2
-----------

Released 2014-08-22

-   Added missing ``err`` parameter forwarding to the ``secho``
    function.
-   Fixed default parameters not being handled properly by the context
    invoke method. This is a backwards incompatible change if the
    function was used improperly.
-   Removed the ``invoked_subcommands`` attribute largely. It is not
    possible to provide it to work error free due to how the parsing
    works so this API has been deprecated.
-   Restored the functionality of ``invoked_subcommand`` which was
    broken as a regression in 3.1.


Version 3.1
-----------

Released 2014-08-13

-   Fixed a regression that caused contexts of subcommands to be created
    before the parent command was invoked which was a regression from
    earlier Click versions.


Version 3.0
-----------

Released 2014-08-12, codename "clonk clonk"

-   Formatter now no longer attempts to accommodate for terminals
    smaller than 50 characters. If that happens it just assumes a
    minimal width.
-   Added a way to not swallow exceptions in the test system.
-   Added better support for colors with pagers and ways to override the
    autodetection.
-   The CLI runner's result object now has a traceback attached.
-   Improved automatic short help detection to work better with dots
    that do not terminate sentences.
-   When defining options without actual valid option strings now,
    Click will give an error message instead of silently passing. This
    should catch situations where users wanted to created arguments
    instead of options.
-   Restructured Click internally to support vendoring.
-   Added support for multi command chaining.
-   Added support for defaults on options with ``multiple`` and options
    and arguments with ``nargs != 1``.
-   Label passed to ``progressbar`` is no longer rendered with
    whitespace stripped.
-   Added a way to disable the standalone mode of the ``main`` method on
    a Click command to be able to handle errors better.
-   Added support for returning values from command callbacks.
-   Added simplifications for printing to stderr from ``echo``.
-   Added result callbacks for groups.
-   Entering a context multiple times defers the cleanup until the last
    exit occurs.
-   Added ``open_file``.


Version 2.6
-----------

Released 2014-08-11

-   Fixed an issue where the wrapped streams on Python 3 would be
    reporting incorrect values for seekable.


Version 2.5
-----------

Released 2014-07-28

-   Fixed a bug with text wrapping on Python 3.


Version 2.4
-----------

Released 2014-07-04

-   Corrected a bug in the change of the help option in 2.3.


Version 2.3
-----------

Released 2014-07-03

-   Fixed an incorrectly formatted help record for count options.
-   Add support for ansi code stripping on Windows if colorama is not
    available.
-   Restored the Click 1.0 handling of the help parameter for certain
    edge cases.


Version 2.2
-----------

Released 2014-06-26

-   Fixed tty detection on PyPy.
-   Fixed an issue that progress bars were not rendered when the context
    manager was entered.


Version 2.1
-----------

Released 2014-06-14

-   Fixed the :func:`launch` function on windows.
-   Improved the colorama support on windows to try hard to not screw up
    the console if the application is interrupted.
-   Fixed windows terminals incorrectly being reported to be 80
    characters wide instead of 79
-   Use colorama win32 bindings if available to get the correct
    dimensions of a windows terminal.
-   Fixed an issue with custom function types on Python 3.
-   Fixed an issue with unknown options being incorrectly reported in
    error messages.


Version 2.0
-----------

Released 2014-06-06, codename "tap tap tap"

-   Added support for opening stdin/stdout on Windows in binary mode
    correctly.
-   Added support for atomic writes to files by going through a
    temporary file.
-   Introduced :exc:`BadParameter` which can be used to easily perform
    custom validation with the same error messages as in the type
    system.
-   Added :func:`progressbar`; a function to show progress bars.
-   Added :func:`get_app_dir`; a function to calculate the home folder
    for configs.
-   Added transparent handling for ANSI codes into the :func:`echo`
    function through ``colorama``.
-   Added :func:`clear` function.
-   Breaking change: parameter callbacks now get the parameter object
    passed as second argument. There is legacy support for old callbacks
    which will warn but still execute the script.
-   Added :func:`style`, :func:`unstyle` and :func:`secho` for ANSI
    styles.
-   Added an :func:`edit` function that invokes the default editor.
-   Added an :func:`launch` function that launches browsers and
    applications.
-   Nargs of -1 for arguments can now be forced to be a single item
    through the required flag. It defaults to not required.
-   Setting a default for arguments now implicitly makes it non
    required.
-   Changed "yN" / "Yn" to "y/N" and "Y/n" in confirmation prompts.
-   Added basic support for bash completion.
-   Added :func:`getchar` to fetch a single character from the terminal.
-   Errors now go to stderr as intended.
-   Fixed various issues with more exotic parameter formats like
    DOS/Windows style arguments.
-   Added :func:`pause` which works similar to the Windows ``pause`` cmd
    built-in but becomes an automatic noop if the application is not run
    through a terminal.
-   Added a bit of extra information about missing choice parameters.
-   Changed how the help function is implemented to allow global
    overriding of the help option.
-   Added support for token normalization to implement case insensitive
    handling.
-   Added support for providing defaults for context settings.


Version 1.1
-----------

Released 2014-05-23

-   Fixed a bug that caused text files in Python 2 to not accept native
    strings.


Version 1.0
-----------

Released 2014-05-21

-   Initial release.

```
---

## LICENSE.txt

```text
Copyright 2014 Pallets

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1.  Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

2.  Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

3.  Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

```
---

## README.md

```markdown
<div align="center"><img src="https://raw.githubusercontent.com/pallets/click/refs/heads/stable/docs/_static/click-name.svg" alt="" height="150"></div>

# Click

Click is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary. It's the "Command
Line Interface Creation Kit". It's highly configurable but comes with
sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun
while also preventing any frustration caused by the inability to
implement an intended CLI API.

Click in three points:

-   Arbitrary nesting of commands
-   Automatic help page generation
-   Supports lazy loading of subcommands at runtime


## A Simple Example

```python
import click

@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")

if __name__ == '__main__':
    hello()
```

```
$ python hello.py --count=3
Your name: Click
Hello, Click!
Hello, Click!
Hello, Click!
```


## Donate

The Pallets organization develops and supports Click and other popular
packages. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, [please
donate today][].

[please donate today]: https://palletsprojects.com/donate

## Contributing

See our [detailed contributing documentation][contrib] for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.

[contrib]: https://palletsprojects.com/contributing/

```
---

## docs/advanced.md

```markdown
# Advanced Patterns

```{currentmodule} click
```

In addition to common functionality, Click offers some advanced features.

```{contents}
:depth: 1
:local: true
```

## Callbacks and Eager Options

Sometimes, you want a parameter to completely change the execution flow.
For instance, this is the case when you want to have a `--version`
parameter that prints out the version and then exits the application.

Note: an actual implementation of a `--version` parameter that is
reusable is available in Click as {func}`click.version_option`. The code
here is merely an example of how to implement such a flag.

In such cases, you need two concepts: eager parameters and a callback. An
eager parameter is a parameter handled before others, and a
callback is what executes after the parameter is handled. The eagerness
is necessary so that an earlier required parameter does not produce an
error message. For instance, if `--version` was not eager and a
parameter `--foo` was required and defined before, you would need to
specify it for `--version` to work. For more information, see
{ref}`callback-evaluation-order`.

A callback is a function invoked with three parameters: the
current {class}`Context`, the current {class}`Parameter`, and the value.
The context provides some useful features such as quitting the
application and gives access to other already processed parameters.

Here's an example for a `--version` flag:

```{eval-rst}
.. click:example::

    def print_version(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return
        click.echo('Version 1.0')
        ctx.exit()

    @click.command()
    @click.option('--version', is_flag=True, callback=print_version,
                  expose_value=False, is_eager=True)
    def hello():
        click.echo('Hello World!')


What it looks like:


.. click:run::

    invoke(hello)
    invoke(hello, args=['--version'])
```
The `expose_value` parameter prevents the pretty pointless `version`
parameter from being passed to the callback. If that was not specified, a
boolean would be passed to the `hello` script. The `resilient_parsing`
flag is applied to the context if Click wants to parse the command line
without any destructive behavior that would change the execution flow. In
this case, because we would exit the program, we instead do nothing.

## Callbacks for Validation

```{versionchanged} 2.0
```

If you want to apply custom validation logic, you can do this in the
parameter callbacks. These callbacks can both modify values and
raise errors if the validation does not work. The callback runs after
type conversion. It is called for all sources, including prompts.

In Click 1.0, you can only raise the {exc}`UsageError` but starting with
Click 2.0, you can also raise the {exc}`BadParameter` error, which has the
added advantage that it will automatically format the error message to
also contain the parameter name.

```{eval-rst}
.. click:example::

    def validate_rolls(ctx, param, value):
        if isinstance(value, tuple):
            return value

        try:
            rolls, _, dice = value.partition("d")
            return int(dice), int(rolls)
        except ValueError:
            raise click.BadParameter("format must be 'NdM'")

    @click.command()
    @click.option(
        "--rolls", type=click.UNPROCESSED, callback=validate_rolls,
        default="1d6", prompt=True,
    )
    def roll(rolls):
        sides, times = rolls
        click.echo(f"Rolling a {sides}-sided dice {times} time(s)")

.. click:run::

    invoke(roll, args=["--rolls=42"])
    println()
    invoke(roll, args=["--rolls=2d12"])
    println()
    invoke(roll, input=["42", "2d12"])
```

## Parameter Modifications

Parameters (options and arguments) are forwarded to the command callbacks,
as you have seen. One common way to prevent a parameter from being passed
to the callback is the `expose_value` argument to a parameter which hides
the parameter entirely. The way this works is that the {class}`Context`
object has a {attr}`~Context.params` attribute which is a dictionary of
all parameters. Whatever is in that dictionary is being passed to the
callbacks.

This can be used to make up additional parameters. Generally, this pattern
is not recommended, but in some cases it can be useful. At the very least,
it's good to know that the system works this way.

```{eval-rst}
.. click:example::

    import urllib

    def open_url(ctx, param, value):
        if value is not None:
            ctx.params['fp'] = urllib.urlopen(value)
            return value

    @click.command()
    @click.option('--url', callback=open_url)
    def cli(url, fp=None):
        if fp is not None:
            click.echo(f"{url}: {fp.code}")

In this case the callback returns the URL unchanged but also passes a
second `fp` value to the callback. What's more recommended is to pass
the information in a wrapper, however:

.. click:example::

    import urllib

    class URL(object):

        def __init__(self, url, fp):
            self.url = url
            self.fp = fp

    def open_url(ctx, param, value):
        if value is not None:
            return URL(value, urllib.urlopen(value))

    @click.command()
    @click.option('--url', callback=open_url)
    def cli(url):
        if url is not None:
            click.echo(f"{url.url}: {url.fp.code}")

```

## Token Normalization

```{versionadded} 2.0
```

Starting with Click 2.0, it's possible to provide a function used
for normalizing tokens. Tokens are option names, choice values, or command
values. This can be used to implement case-insensitive options, for
instance.

To use this feature, the context needs to be passed a function that
performs the normalization of the token. Such as a function that converts the
token to lowercase:

```{eval-rst}
.. click:example::

    CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())

    @click.command(context_settings=CONTEXT_SETTINGS)
    @click.option('--name', default='Pete')
    def cli(name):
        click.echo(f"Name: {name}")

# And how it works on the command line:

.. click:run::

    invoke(cli, prog_name='cli', args=['--NAME=Pete'])
```

## Invoking Other Commands

Sometimes, it might be interesting to invoke one command from another
command. This is a pattern generally discouraged with Click, but
possible nonetheless. For this, you can use the {func}`Context.invoke`
or {func}`Context.forward` methods.

They work similarly, but the difference is that {func}`Context.invoke` merely
invokes another command with the arguments you provide as a caller,
whereas {func}`Context.forward` fills in the arguments from the current
command. Both accept the command as the first argument, and everything else
is passed onwards as you would expect.

Example:

```{eval-rst}
.. click:example::

    cli = click.Group()

    @cli.command()
    @click.option('--count', default=1)
    def test(count):
        click.echo(f'Count: {count}')

    @cli.command()
    @click.option('--count', default=1)
    @click.pass_context
    def dist(ctx, count):
        ctx.forward(test)
        ctx.invoke(test, count=42)

And what it looks like:

.. click:run::

    invoke(cli, prog_name='cli', args=['dist'])
```

(forwarding-unknown-options)=

## Forwarding Unknown Options

In some situations, it is interesting to be able to accept all unknown
options for further manual processing. Click can generally do that as of
Click 4.0, but it has some limitations that lie in the nature of the
problem. The support for this is provided through a parser flag called
`ignore_unknown_options` which will instruct the parser to collect all
unknown options and to put them to the leftover argument instead of
triggering a parsing error.

This can generally be activated in two different ways:

1. It can be enabled on custom {class}`Command` subclasses by changing
   the {attr}`~Command.ignore_unknown_options` attribute.
2. It can be enabled by changing the attribute of the same name on the
   context class ({attr}`Context.ignore_unknown_options`). This is best
   changed through the `context_settings` dictionary on the command.

For most situations, the easiest solution is the second. Once the behavior
is changed, something needs to pick up those leftover options (which at
this point are considered arguments). For this again, you have two
options:

1. You can use {func}`pass_context` to get the context passed. This will
   only work if in addition to {attr}`~Context.ignore_unknown_options`
   you also set {attr}`~Context.allow_extra_args` as otherwise the
   command will abort with an error that there are leftover arguments.
   If you go with this solution, the extra arguments will be collected in
   {attr}`Context.args`.
2. You can attach an {func}`argument` with `nargs` set to `-1` which
   will eat up all leftover arguments. In this case it's recommended to
   set the `type` to {data}`UNPROCESSED` to avoid any string processing
   on those arguments as otherwise they are forced into Unicode strings
   automatically which is often not what you want.

In the end, the result looks something like this:

```{eval-rst}
.. click:example::

    import sys
    from subprocess import call

    @click.command(context_settings=dict(
        ignore_unknown_options=True,
    ))
    @click.option('-v', '--verbose', is_flag=True, help='Enables verbose mode')
    @click.argument('timeit_args', nargs=-1, type=click.UNPROCESSED)
    def cli(verbose, timeit_args):
        """A fake wrapper around Python's timeit."""
        cmdline = ['echo', 'python', '-mtimeit'] + list(timeit_args)
        if verbose:
            click.echo(f"Invoking: {' '.join(cmdline)}")
        call(cmdline)


And the final output resembles the following:

.. click:run::

    invoke(cli, prog_name='cli', args=['--help'])
    println()
    invoke(cli, prog_name='cli', args=['-n', '100', 'a = 1; b = 2; a * b'])
    println()
    invoke(cli, prog_name='cli', args=['-v', 'a = 1; b = 2; a * b'])
```

As you can see, Click handles the verbosity flag and everything else
ends up in the `timeit_args` variable for further processing, which then
for instance, allows invoking a subprocess. There are a few things that
are important to know about how this ignoring of unhandled flag happens:

- Unknown long options are generally ignored and not processed at all.
  So for instance if `--foo=bar` or `--foo bar` are passed they
  generally end up like that. Note that because the parser cannot know
  if an option will accept an argument or not, the `bar` part might be
  handled as an argument.
- Unknown short options might be partially handled and reassembled if
  necessary. For instance in the above example there is an option
  called `-v` which enables verbose mode. If the command would be
  ignored with `-va` then the `-v` part would be handled by Click
  (as it is known) and `-a` would end up in the leftover parameters
  for further processing.
- Depending on what you plan on doing you might have some success by
  disabling interspersed arguments
  ({attr}`~Context.allow_interspersed_args`) which instructs the parser
  to not allow arguments and options to be mixed. Depending on your
   situation, this might improve your results.

Generally, combining the handling of options and arguments from your own
commands with those from another application is discouraged, and you
should avoid it if possible. It's a much better idea to have
everything below a subcommand be forwarded to another application than to
handle some arguments yourself.

## Managing Resources

It can be useful to open a resource in a group, to be made available to
subcommands. Many types of resources need to be closed or otherwise
cleaned up after use. The standard way to do this in Python is by using
a context manager with the `with` statement.

For example, the `Repo` class from {doc}`complex` might actually be
defined as a context manager:

```python
class Repo:
    def __init__(self, home=None):
        self.home = os.path.abspath(home or ".")
        self.db = None

    def __enter__(self):
        path = os.path.join(self.home, "repo.db")
        self.db = open_database(path)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.db.close()
```

Ordinarily, it would be used with the `with` statement:

```python
with Repo() as repo:
    repo.db.query(...)
```

However, a `with` block in a group would exit and close the database
before it could be used by a subcommand.

Instead, use the context's {meth}`~click.Context.with_resource` method
to enter the context manager and return the resource. When the group and
any subcommands finish, the context's resources are cleaned up.

```python
@click.group()
@click.option("--repo-home", default=".repo")
@click.pass_context
def cli(ctx, repo_home):
    ctx.obj = ctx.with_resource(Repo(repo_home))

@cli.command()
@click.pass_obj
def log(obj):
    # obj is the repo opened in the cli group
    for entry in obj.db.query(...):
        click.echo(entry)
```

If the resource isn't a context manager, usually it can be wrapped in
one using something from {mod}`contextlib`. If that's not possible, use
the context's {meth}`~click.Context.call_on_close` method to register a
cleanup function.

```python
@click.group()
@click.option("--name", default="repo.db")
@click.pass_context
def cli(ctx, repo_home):
    ctx.obj = db = open_db(repo_home)

    @ctx.call_on_close
    def close_db():
        db.record_use()
        db.save()
        db.close()
```

```{versionchanged} 8.2
`Context.call_on_close` and context managers registered via `Context.with_resource`
will be closed when the CLI exits. These were previously not called on exit.
```

```
---

## docs/api.md

```markdown
# API

```{currentmodule} click
```

This part of the documentation lists the full API reference of all public
classes and functions.

```{contents}
:depth: 1
:local: true
```

## Decorators

```{eval-rst}
.. autofunction:: command
```

```{eval-rst}
.. autofunction:: group
```

```{eval-rst}
.. autofunction:: argument
```

```{eval-rst}
.. autofunction:: option
```

```{eval-rst}
.. autofunction:: password_option
```

```{eval-rst}
.. autofunction:: confirmation_option
```

```{eval-rst}
.. autofunction:: version_option
```

```{eval-rst}
.. autofunction:: help_option
```

```{eval-rst}
.. autofunction:: pass_context
```

```{eval-rst}
.. autofunction:: pass_obj
```

```{eval-rst}
.. autofunction:: make_pass_decorator
```

```{eval-rst}
.. autofunction:: click.decorators.pass_meta_key

```

## Utilities

```{eval-rst}
.. autofunction:: echo
```

```{eval-rst}
.. autofunction:: echo_via_pager
```

```{eval-rst}
.. autofunction:: prompt
```

```{eval-rst}
.. autofunction:: confirm
```

```{eval-rst}
.. autofunction:: progressbar
```

```{eval-rst}
.. autofunction:: clear
```

```{eval-rst}
.. autofunction:: style
```

```{eval-rst}
.. autofunction:: unstyle
```

```{eval-rst}
.. autofunction:: secho
```

```{eval-rst}
.. autofunction:: edit
```

```{eval-rst}
.. autofunction:: launch
```

```{eval-rst}
.. autofunction:: getchar
```

```{eval-rst}
.. autofunction:: pause
```

```{eval-rst}
.. autofunction:: get_binary_stream
```

```{eval-rst}
.. autofunction:: get_text_stream
```

```{eval-rst}
.. autofunction:: open_file
```

```{eval-rst}
.. autofunction:: get_app_dir
```

```{eval-rst}
.. autofunction:: format_filename
```

## Commands

```{eval-rst}
.. autoclass:: BaseCommand
   :members:
```

```{eval-rst}
.. autoclass:: Command
   :members:
```

```{eval-rst}
.. autoclass:: MultiCommand
   :members:
```

```{eval-rst}
.. autoclass:: Group
   :members:
```

```{eval-rst}
.. autoclass:: CommandCollection
   :members:
```

## Parameters

```{eval-rst}
.. autoclass:: Parameter
   :members:
```

```{eval-rst}
.. autoclass:: Option
```

```{eval-rst}
.. autoclass:: Argument
```

## Context

```{eval-rst}
.. autoclass:: Context
   :members:
```

```{eval-rst}
.. autofunction:: get_current_context
```

```{eval-rst}
.. autoclass:: click.core.ParameterSource
    :members:
    :member-order: bysource
```

(click-api-types)=

## Types

```{eval-rst}
.. autodata:: STRING
```

```{eval-rst}
.. autodata:: INT
```

```{eval-rst}
.. autodata:: FLOAT
```

```{eval-rst}
.. autodata:: BOOL
```

```{eval-rst}
.. autodata:: UUID
```

```{eval-rst}
.. autodata:: UNPROCESSED
```

```{eval-rst}
.. autoclass:: File
```

```{eval-rst}
.. autoclass:: Path
```

```{eval-rst}
.. autoclass:: Choice
   :members:
```

```{eval-rst}
.. autoclass:: IntRange
```

```{eval-rst}
.. autoclass:: FloatRange
```

```{eval-rst}
.. autoclass:: DateTime
```

```{eval-rst}
.. autoclass:: Tuple
```

```{eval-rst}
.. autoclass:: ParamType
   :members:
```

## Exceptions

```{eval-rst}
.. autoexception:: ClickException
```

```{eval-rst}
.. autoexception:: Abort
```

```{eval-rst}
.. autoexception:: UsageError
```

```{eval-rst}
.. autoexception:: BadParameter
```

```{eval-rst}
.. autoexception:: FileError
```

```{eval-rst}
.. autoexception:: NoSuchOption
```

```{eval-rst}
.. autoexception:: BadOptionUsage
```

```{eval-rst}
.. autoexception:: BadArgumentUsage
```

## Formatting

```{eval-rst}
.. autoclass:: HelpFormatter
   :members:
```

```{eval-rst}
.. autofunction:: wrap_text
```

## Parsing

```{eval-rst}
.. autoclass:: OptionParser
   :members:

```

## Shell Completion

See {doc}`/shell-completion` for information about enabling and
customizing Click's shell completion system.

```{eval-rst}
.. currentmodule:: click.shell_completion
```

```{eval-rst}
.. autoclass:: CompletionItem
```

```{eval-rst}
.. autoclass:: ShellComplete
    :members:
    :member-order: bysource
```

```{eval-rst}
.. autofunction:: add_completion_class

```

(testing)=

## Testing

```{eval-rst}
.. currentmodule:: click.testing
```

```{eval-rst}
.. autoclass:: CliRunner
   :members:
```

```{eval-rst}
.. autoclass:: Result
   :members:
```

```
---

## docs/arguments.rst

```text
.. _arguments:

Arguments
=========

.. currentmodule:: click

Arguments are:

*   Are positional in nature.
*   Similar to a limited version of :ref:`options <options>` that can take an arbitrary number of inputs
*   :ref:`Documented manually <documenting-arguments>`.

Useful and often used kwargs are:

*   ``default``: Passes a default.
*   ``nargs``: Sets the number of arguments. Set to -1 to take an arbitrary number.

Basic Arguments
---------------

A minimal :class:`click.Argument` solely takes one string argument: the name of the argument. This will assume the argument is required, has no default, and is of the type ``str``.

Example:

.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename: str):
        """Print FILENAME."""
        click.echo(filename)

And from the command line:

.. click:run::

    invoke(touch, args=['foo.txt'])


An argument may be assigned a :ref:`parameter type <parameter-types>`. If no type is provided, the type of the default value is used. If no default value is provided, the type is assumed to be :data:`STRING`.

.. admonition:: Note on Required Arguments

   It is possible to make an argument required by setting ``required=True``.  It is not recommended since we think command line tools should gracefully degrade into becoming no ops.  We think this because command line tools are often invoked with wildcard inputs and they should not error out if the wildcard is empty.

Multiple Arguments
-----------------------------------

To set the number of argument use the ``nargs`` kwarg. It can be set to any positive integer and -1. Setting it to -1, makes the number of arguments arbitrary (which is called variadic) and can only be used once. The arguments are then packed as a tuple and passed to the function.

.. click:example::

    @click.command()
    @click.argument('src', nargs=1)
    @click.argument('dsts', nargs=-1)
    def copy(src: str, dsts: tuple[str, ...]):
        """Move file SRC to DST."""
        for destination in dsts:
            click.echo(f"Copy {src} to folder {destination}")

And from the command line:

.. click:run::

    invoke(copy, args=['foo.txt', 'usr/david/foo.txt', 'usr/mitsuko/foo.txt'])

.. admonition:: Note on Handling Files

    This is not how you should handle files and files paths. This merely used as a simple example. See :ref:`handling-files` to learn more about how to handle files in parameters.

Argument Escape Sequences
---------------------------

If you want to process arguments that look like options, like a file named ``-foo.txt`` or ``--foo.txt`` , you must pass the ``--`` separator first. After you pass the ``--``, you may only pass arguments. This is a common feature for POSIX command line tools.

Example usage:

.. click:example::

    @click.command()
    @click.argument('files', nargs=-1, type=click.Path())
    def touch(files):
        """Print all FILES file names."""
        for filename in files:
            click.echo(filename)

And from the command line:

.. click:run::

    invoke(touch, ['--', '-foo.txt', 'bar.txt'])

If you don't like the ``--`` marker, you can set ignore_unknown_options to True to avoid checking unknown options:

.. click:example::

    @click.command(context_settings={"ignore_unknown_options": True})
    @click.argument('files', nargs=-1, type=click.Path())
    def touch(files):
        """Print all FILES file names."""
        for filename in files:
            click.echo(filename)

And from the command line:

.. click:run::

    invoke(touch, ['-foo.txt', 'bar.txt'])


.. _environment-variables:

Environment Variables
---------------------

Arguments can use environment variables. To do so, pass the name(s) of the environment variable(s) via `envvar` in ``click.argument``.

Checking one environment variable:

.. click:example::

    @click.command()
    @click.argument('src', envvar='SRC', type=click.File('r'))
    def echo(src):
        """Print value of SRC environment variable."""
        click.echo(src.read())

And from the command line:

.. click:run::

    with isolated_filesystem():
        # Writing the file in the filesystem.
        with open('hello.txt', 'w') as f:
            f.write('Hello World!')
        invoke(echo, env={'SRC': 'hello.txt'})


Checking multiple environment variables:

.. click:example::

    @click.command()
    @click.argument('src', envvar=['SRC', 'SRC_2'], type=click.File('r'))
    def echo(src):
        """Print value of SRC environment variable."""
        click.echo(src.read())

And from the command line:

.. click:run::

    with isolated_filesystem():
        # Writing the file in the filesystem.
        with open('hello.txt', 'w') as f:
            f.write('Hello World from second variable!')
        invoke(echo, env={'SRC_2': 'hello.txt'})

```
---

## docs/changes.rst

```text
Changes
=======

.. include:: ../CHANGES.rst

```
---

## docs/click-concepts.rst

```text
Click Concepts
================

This section covers concepts about Click's design.

.. contents::
    :depth: 1
    :local:

.. _callback-evaluation-order:

Callback Evaluation Order
-------------------------

Click works a bit differently than some other command line parsers in that
it attempts to reconcile the order of arguments as defined by the
programmer with the order of arguments as defined by the user before
invoking any callbacks.

This is an important concept to understand when porting complex
patterns to Click from optparse or other systems.  A parameter
callback invocation in optparse happens as part of the parsing step,
whereas a callback invocation in Click happens after the parsing.

The main difference is that in optparse, callbacks are invoked with the raw
value as it happens, whereas a callback in Click is invoked after the
value has been fully converted.

Generally, the order of invocation is driven by the order in which the user
provides the arguments to the script; if there is an option called ``--foo``
and an option called ``--bar`` and the user calls it as ``--bar
--foo``, then the callback for ``bar`` will fire before the one for ``foo``.

There are three exceptions to this rule which are important to know:

Eagerness:
    An option can be set to be "eager".  All eager parameters are
    evaluated before all non-eager parameters, but again in the order as
    they were provided on the command line by the user.

    This is important for parameters that execute and exit like ``--help``
    and ``--version``.  Both are eager parameters, but whatever parameter
    comes first on the command line will win and exit the program.

Repeated parameters:
    If an option or argument is split up on the command line into multiple
    places because it is repeated -- for instance, ``--exclude foo --include
    baz --exclude bar`` -- the callback will fire based on the position of
    the first option.  In this case, the callback will fire for
    ``exclude`` and it will be passed both options (``foo`` and
    ``bar``), then the callback for ``include`` will fire with ``baz``
    only.

    Note that even if a parameter does not allow multiple versions, Click
    will still accept the position of the first, but it will ignore every
    value except the last.  The reason for this is to allow composability
    through shell aliases that set defaults.

Missing parameters:
    If a parameter is not defined on the command line, the callback will
    still fire.  This is different from how it works in optparse where
    undefined values do not fire the callback.  Missing parameters fire
    their callbacks at the very end which makes it possible for them to
    default to values from a parameter that came before.

Most of the time you do not need to be concerned about any of this,
but it is important to know how it works for some advanced cases.

```
---

## docs/command-line-reference.md

```markdown
# General Command Line Topics

```{currentmodule} click
```

```{contents}
---
depth: 1
local: true
---
```

(exit-codes)=
## Exit Codes

When a command is executed from the command line, then an exit code is return. The exit code, also called exit status or exit status code, is a positive integer that tells you whether the command executed with or without errors.

| Exit Code | Meaning                                         |
|-----------|-------------------------------------------------|
| 0         | Success — the command completed without errors. |
| > 0       | Executed with errors                            |

Exit codes greater than zero mean are specific to the Operating System, Shell, and/or command.

To access the exit code, execute the command, then do the following depending:

```{eval-rst}
.. tabs::

    .. group-tab:: Powershell

        .. code-block:: powershell

           > echo $LASTEXITCODE

    .. group-tab:: Bash

        .. code-block:: bash

            $ echo $?

    .. group-tab:: Command Prompt


        .. code-block:: text

            > echo %ERRORLEVEL%
```

For Click specific behavior on exit codes, see {ref}`exception-handling-exit-codes`.

```
---

## docs/commands-and-groups.rst

```text
Basic Commands, Groups, Context
================================

.. currentmodule:: click

Commands and Groups are the building blocks for Click applications. :class:`Command` wraps a function to make it into a cli command. :class:`Group` wraps Commands and Groups to make them into applications. :class:`Context` is how groups and commands communicate.

.. contents::
   :depth: 2
   :local:

Commands
--------------------

Basic Command Example
^^^^^^^^^^^^^^^^^^^^^^^
A simple command decorator takes no arguments.

.. click:example::
    @click.command()
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

.. click:run::
    invoke(hello, args=['--count', '2',])

Renaming Commands
^^^^^^^^^^^^^^^^^^^
By default the command is the function name with underscores replaced by dashes. To change this pass the  desired name into the first positional argument.

.. click:example::
    @click.command('say-hello')
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

.. click:run::
    invoke(hello, args=['--count', '2',])

Deprecating Commands
^^^^^^^^^^^^^^^^^^^^^^
To mark a command as deprecated pass in ``deprecated=True``

.. click:example::
    @click.command('say-hello', deprecated=True)
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

.. click:run::
    invoke(hello, args=['--count', '2',])

Groups
------------

Basic Group Example
^^^^^^^^^^^^^^^^^^^^^
A group wraps one or more commands. After being wrapped, the commands are nested under that group. You can see that on the help pages and in the execution. By default, invoking the group with no command shows the help page.

.. click:example::
    @click.group()
    def greeting():
        click.echo('Starting greeting ...')

    @greeting.command('say-hello')
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

At the top level:

.. click:run::

    invoke(greeting)

At the command level:

.. click:run::

    invoke(greeting, args=['say-hello'])
    invoke(greeting, args=['say-hello', '--help'])

As you can see from the above example, the function wrapped by the group decorator executes unless it is interrupted (for example by calling the help).

Renaming Groups
^^^^^^^^^^^^^^^^^
To have a name other than the decorated function name as the group name, pass it in as the first positional argument.

.. click:example::
    @click.group('greet-someone')
    def greeting():
        click.echo('Starting greeting ...')

    @greeting.command('say-hello')
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

.. click:run::

    invoke(greeting, args=['say-hello'])

Group Invocation Without Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, if a group is passed without a command, the group is not invoked and a command automatically passes ``--help``. To change this, pass ``invoke_without_command=True`` to the group. The context object also includes information about whether or not the group invocation would go to a command nested under it.

.. click:example::

    @click.group(invoke_without_command=True)
    @click.pass_context
    def cli(ctx):
        if ctx.invoked_subcommand is None:
            click.echo('I was invoked without subcommand')
        else:
            click.echo(f"I am about to invoke {ctx.invoked_subcommand}")

    @cli.command()
    def sync():
        click.echo('The subcommand')

.. click:run::

    invoke(cli, prog_name='tool', args=[])
    invoke(cli, prog_name='tool', args=['sync'])



Group Separation
^^^^^^^^^^^^^^^^^^^
Command :ref:`parameters` attached to a command belong only to that command.

.. click:example::
    @click.group()
    def greeting():
        pass

    @greeting.command()
    @click.option('--count', default=1)
    def hello(count):
        for x in range(count):
            click.echo("Hello!")

    @greeting.command()
    @click.option('--count', default=1)
    def goodbye(count):
        for x in range(count):
            click.echo("Goodbye!")

.. click:run::

    invoke(greeting, args=['hello', '--count', '2'])
    invoke(greeting, args=['goodbye', '--count', '2'])
    invoke(greeting)

Additionally parameters for a given group belong only to that group and not to the commands under it. What this means is that options and arguments for a specific command have to be specified *after* the command name itself, but *before* any other command names.

This behavior is observable with the ``--help`` option. Suppose we have a group called ``tool`` containing a command called ``sub``.

- ``tool --help`` returns the help for the whole program (listing subcommands).
- ``tool sub --help`` returns the help for the ``sub`` subcommand.
- But ``tool --help sub`` treats ``--help`` as an argument for the main program. Click then invokes the callback for ``--help``, which prints the help and aborts the program before click can process the subcommand.

Arbitrary Nesting
^^^^^^^^^^^^^^^^^^^
:class:`Commands <Command>` are attached to a :class:`Group`. Multiple groups can be attached to another group. Groups containing multiple groups can be attached to a group, and so on. To invoke a command nested under multiple groups, all the groups under which it is nested must be invoked.

.. click:example::

    @click.group()
    def cli():
        pass

    # Not @click so that the group is registered now.
    @cli.group()
    def session():
        click.echo('Starting session')

    @session.command()
    def initdb():
        click.echo('Initialized the database')

    @session.command()
    def dropdb():
        click.echo('Dropped the database')

.. click:run::

    invoke(cli, args=['session', 'initdb'])

Lazily Attaching Commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Most examples so far have attached the commands to a group immediately, but commands may be registered later. This could be used to split commands into multiple Python modules. Regardless of how they are attached, the commands are invoked identically.

.. click:example::

    @click.group()
    def cli():
        pass

    @cli.command()
    def initdb():
        click.echo('Initialized the database')

    @click.command()
    def dropdb():
        click.echo('Dropped the database')

    cli.add_command(dropdb)

.. click:run::

    invoke(cli, args=['initdb'])
    invoke(cli, args=['dropdb'])

Context Object
-------------------
The :class:`Context` object is how commands and groups communicate.

Auto Envvar Prefix
^^^^^^^^^^^^^^^^^^^^
Automatically built environment variables are supported for options only. To enable this feature, the ``auto_envvar_prefix`` parameter needs to be passed to the script that is invoked.  Each command and parameter is then added as an uppercase underscore-separated variable.  If you have a subcommand
called ``run`` taking an option called ``reload`` and the prefix is ``WEB``, then the variable is ``WEB_RUN_RELOAD``.

Example usage:

.. click:example::

    @click.command()
    @click.option('--username')
    def greet(username):
        click.echo(f'Hello {username}!')

    if __name__ == '__main__':
        greet(auto_envvar_prefix='GREETER')

And from the command line:

.. click:run::

    invoke(greet, env={'GREETER_USERNAME': 'john'},
           auto_envvar_prefix='GREETER')

When using ``auto_envvar_prefix`` with command groups, the command name
needs to be included in the environment variable, between the prefix and
the parameter name, *i.e.* ``PREFIX_COMMAND_VARIABLE``. If you have a
subcommand called ``run-server`` taking an option called ``host`` and
the prefix is ``WEB``, then the variable is ``WEB_RUN_SERVER_HOST``.

.. click:example::

   @click.group()
   @click.option('--debug/--no-debug')
   def cli(debug):
       click.echo(f"Debug mode is {'on' if debug else 'off'}")

   @cli.command()
   @click.option('--username')
   def greet(username):
       click.echo(f"Hello {username}!")

   if __name__ == '__main__':
       cli(auto_envvar_prefix='GREETER')

.. click:run::

   invoke(cli, args=['greet',],
          env={'GREETER_GREET_USERNAME': 'John', 'GREETER_DEBUG': 'false'},
          auto_envvar_prefix='GREETER')

Global Context Access
^^^^^^^^^^^^^^^^^^^^^^

.. versionadded:: 5.0

Starting with Click 5.0 it is possible to access the current context from
anywhere within the same thread through the use of the
:func:`get_current_context` function which returns it.  This is primarily
useful for accessing the context bound object as well as some flags that
are stored on it to customize the runtime behavior.  For instance the
:func:`echo` function does this to infer the default value of the `color`
flag.

Example usage::

    def get_current_command_name():
        return click.get_current_context().info_name

It should be noted that this only works within the current thread.  If you
spawn additional threads then those threads will not have the ability to
refer to the current context.  If you want to give another thread the
ability to refer to this context you need to use the context within the
thread as a context manager::

    def spawn_thread(ctx, func):
        def wrapper():
            with ctx:
                func()
        t = threading.Thread(target=wrapper)
        t.start()
        return t

Now the thread function can access the context like the main thread would
do.  However if you do use this for threading you need to be very careful
as the vast majority of the context is not thread safe!  You are only
allowed to read from the context, but not to perform any modifications on
it.


Detecting the Source of a Parameter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some situations it's helpful to understand whether or not an option
or parameter came from the command line, the environment, the default
value, or :attr:`Context.default_map`. The
:meth:`Context.get_parameter_source` method can be used to find this
out. It will return a member of the :class:`~click.core.ParameterSource`
enum.

.. click:example::

    @click.command()
    @click.argument('port', nargs=1, default=8080, envvar="PORT")
    @click.pass_context
    def cli(ctx, port):
        source = ctx.get_parameter_source("port")
        click.echo(f"Port came from {source.name}")

.. click:run::

    invoke(cli, prog_name='cli', args=['8080'])
    println()
    invoke(cli, prog_name='cli', args=[], env={"PORT": "8080"})
    println()
    invoke(cli, prog_name='cli', args=[])
    println()

```
