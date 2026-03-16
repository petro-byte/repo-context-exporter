# Repository Context Part 1/6

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
---

## docs/commands.rst

```text
Advanced Groups and Context
=============================

.. currentmodule:: click

In addition to the capabilities covered in the previous section, Groups have more advanced capabilities that leverage the Context.

.. contents::
   :depth: 1
   :local:

Callback Invocation
-------------------

For a regular command, the callback is executed whenever the command runs.
If the script is the only command, it will always fire (unless a parameter
callback prevents it.  This for instance happens if someone passes
``--help`` to the script).

For groups, the situation looks different. In this case, the callback fires
whenever a subcommand fires.  What this means in practice is that an outer
command runs when an inner command runs:

.. click:example::

    @click.group()
    @click.option('--debug/--no-debug', default=False)
    def cli(debug):
        click.echo(f"Debug mode is {'on' if debug else 'off'}")

    @cli.command()  # @cli, not @click!
    def sync():
        click.echo('Syncing')

Here is what this looks like:

.. click:run::

    invoke(cli, prog_name='tool.py')
    println()
    invoke(cli, prog_name='tool.py', args=['--debug', 'sync'])

Nested Handling and Contexts
----------------------------

As you can see from the earlier example, the basic command group accepts a
debug argument which is passed to its callback, but not to the sync
command itself.  The sync command only accepts its own arguments.

This allows tools to act completely independent of each other, but how
does one command talk to a nested one?  The answer to this is the
:class:`Context`.

Each time a command is invoked, a new context is created and linked with the
parent context.  Normally, you can't see these contexts, but they are
there.  Contexts are passed to parameter callbacks together with the
value automatically.  Commands can also ask for the context to be passed
by marking themselves with the :func:`pass_context` decorator.  In that
case, the context is passed as first argument.

The context can also carry a program specified object that can be
used for the program's purposes.  What this means is that you can build a
script like this:

.. click:example::

    @click.group()
    @click.option('--debug/--no-debug', default=False)
    @click.pass_context
    def cli(ctx, debug):
        # ensure that ctx.obj exists and is a dict (in case `cli()` is called
        # by means other than the `if` block below)
        ctx.ensure_object(dict)

        ctx.obj['DEBUG'] = debug

    @cli.command()
    @click.pass_context
    def sync(ctx):
        click.echo(f"Debug is {'on' if ctx.obj['DEBUG'] else 'off'}")

    if __name__ == '__main__':
        cli(obj={})

If the object is provided, each context will pass the object onwards to
its children, but at any level a context's object can be overridden.  To
reach to a parent, ``context.parent`` can be used.

In addition to that, instead of passing an object down, nothing stops the
application from modifying global state.  For instance, you could just flip
a global ``DEBUG`` variable and be done with it.

Decorating Commands
-------------------

As you have seen in the earlier example, a decorator can change how a
command is invoked.  What actually happens behind the scenes is that
callbacks are always invoked through the :meth:`Context.invoke` method
which automatically invokes a command correctly (by either passing the
context or not).

This is very useful when you want to write custom decorators.  For
instance, a common pattern would be to configure an object representing
state and then storing it on the context and then to use a custom
decorator to find the most recent object of this sort and pass it as first
argument.

For instance, the :func:`pass_obj` decorator can be implemented like this:

.. click:example::

    from functools import update_wrapper

    def pass_obj(f):
        @click.pass_context
        def new_func(ctx, *args, **kwargs):
            return ctx.invoke(f, ctx.obj, *args, **kwargs)
        return update_wrapper(new_func, f)

The :meth:`Context.invoke` command will automatically invoke the function
in the correct way, so the function will either be called with ``f(ctx,
obj)`` or ``f(obj)`` depending on whether or not it itself is decorated with
:func:`pass_context`.

This is a very powerful concept that can be used to build very complex
nested applications; see :ref:`complex-guide` for more information.

.. _command-chaining:

Command Chaining
----------------

It is useful to invoke more than one subcommand in one call. For example,
``my-app validate build upload`` would invoke ``validate``, then ``build``, then
``upload``. To implement this, pass ``chain=True`` when creating a group.

.. click:example::

    @click.group(chain=True)
    def cli():
        pass

    @cli.command('validate')
    def validate():
        click.echo('validate')

    @cli.command('build')
    def build():
        click.echo('build')

You can invoke it like this:

.. click:run::

    invoke(cli, prog_name='my-app', args=['validate', 'build'])

When using chaining, there are a few restrictions:

-   Only the last command may use ``nargs=-1`` on an argument, otherwise the
    parser will not be able to find further commands.
-   It is not possible to nest groups below a chain group.
-   On the command line, options must be specified before arguments for each
    command in the chain.
-   The :attr:`Context.invoked_subcommand` attribute will be ``'*'`` because the
    parser doesn't know the full list of commands that will run yet.

.. _command-pipelines:

Command Pipelines
------------------

When using chaining, a common pattern is to have each command process the
result of the previous command.

A straightforward way to do this is to use :func:`make_pass_decorator` to pass
a context object to each command, and store and read the data on that object.

.. click:example::

    pass_ns = click.make_pass_decorator(dict, ensure=True)

    @click.group(chain=True)
    @click.argument("name")
    @pass_ns
    def cli(ns, name):
        ns["name"] = name

    @cli.command
    @pass_ns
    def lower(ns):
        ns["name"] = ns["name"].lower()

    @cli.command
    @pass_ns
    def show(ns):
        click.echo(ns["name"])

.. click:run::

    invoke(cli, prog_name="process", args=["Click", "show", "lower", "show"])

Another way to do this is to collect data returned by each command, then process
it at the end of the chain. Use the group's :meth:`~Group.result_callback`
decorator to register a function that is called after the chain is finished. It
is passed the list of return values as well as any parameters registered on the
group.

A command can return anything, including a function. Here's an example of that,
where each subcommand creates a function that processes the input, then the
result callback calls each function. The command takes a file, processes each
line, then outputs it. If no subcommands are given, it outputs the contents
of the file unchanged.

.. code-block:: python

    @click.group(chain=True, invoke_without_command=True)
    @click.argument("fin", type=click.File("r"))
    def cli(fin):
        pass

    @cli.result_callback()
    def process_pipeline(processors, fin):
        iterator = (x.rstrip("\r\n") for x in input)

        for processor in processors:
            iterator = processor(iterator)

        for item in iterator:
            click.echo(item)

    @cli.command("upper")
    def make_uppercase():
        def processor(iterator):
            for line in iterator:
                yield line.upper()
        return processor

    @cli.command("lower")
    def make_lowercase():
        def processor(iterator):
            for line in iterator:
                yield line.lower()
        return processor

    @cli.command("strip")
    def make_strip():
        def processor(iterator):
            for line in iterator:
                yield line.strip()
        return processor

That's a lot in one go, so let's go through it step by step.

1.  The first thing is to make a :func:`group` that is chainable.  In
    addition to that we also instruct Click to invoke even if no
    subcommand is defined.  If this would not be done, then invoking an
    empty pipeline would produce the help page instead of running the
    result callbacks.
2.  The next thing we do is to register a result callback on our group.
    This callback will be invoked with an argument which is the list of
    all return values of all subcommands and then the same keyword
    parameters as our group itself.  This means we can access the input
    file easily there without having to use the context object.
3.  In this result callback we create an iterator of all the lines in the
    input file and then pass this iterator through all the returned
    callbacks from all subcommands and finally we print all lines to
    stdout.

After that point we can register as many subcommands as we want and each
subcommand can return a processor function to modify the stream of lines.

One important thing of note is that Click shuts down the context after
each callback has been run.  This means that for instance file types
cannot be accessed in the `processor` functions as the files will already
be closed there.  This limitation is unlikely to change because it would
make resource handling much more complicated.  For such it's recommended
to not use the file type and manually open the file through
:func:`open_file`.

For a more complex example that also improves upon handling of the pipelines,
see the `imagepipe example`_ in the Click repository. It implements a
pipeline based image editing tool that has a nice internal structure.

.. _imagepipe example: https://github.com/pallets/click/tree/main/examples/imagepipe


Overriding Defaults
-------------------

By default, the default value for a parameter is pulled from the
``default`` flag that is provided when it's defined, but that's not the
only place defaults can be loaded from.  The other place is the
:attr:`Context.default_map` (a dictionary) on the context.  This allows
defaults to be loaded from a configuration file to override the regular
defaults.

This is useful if you plug in some commands from another package but
you're not satisfied with the defaults.

The default map can be nested arbitrarily for each subcommand:

.. code-block:: python

    default_map = {
        "debug": True,  # default for a top level option
        "runserver": {"port": 5000}  # default for a subcommand
    }

The default map can be provided when the script is invoked, or
overridden at any point by commands. For instance, a top-level command
could load the defaults from a configuration file.

Example usage:

.. click:example::

    import click

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option('--port', default=8000)
    def runserver(port):
        click.echo(f"Serving on http://127.0.0.1:{port}/")

    if __name__ == '__main__':
        cli(default_map={
            'runserver': {
                'port': 5000
            }
        })

And in action:

.. click:run::

    invoke(cli, prog_name='cli', args=['runserver'], default_map={
        'runserver': {
            'port': 5000
        }
    })

Context Defaults
----------------

.. versionadded:: 2.0

Starting with Click 2.0 you can override defaults for contexts not just
when calling your script, but also in the decorator that declares a
command.  For instance given the previous example which defines a custom
``default_map`` this can also be accomplished in the decorator now.

This example does the same as the previous example:

.. click:example::

    import click

    CONTEXT_SETTINGS = dict(
        default_map={'runserver': {'port': 5000}}
    )

    @click.group(context_settings=CONTEXT_SETTINGS)
    def cli():
        pass

    @cli.command()
    @click.option('--port', default=8000)
    def runserver(port):
        click.echo(f"Serving on http://127.0.0.1:{port}/")

    if __name__ == '__main__':
        cli()

And again the example in action:

.. click:run::

    invoke(cli, prog_name='cli', args=['runserver'])


Command Return Values
---------------------

.. versionadded:: 3.0

One of the new introductions in Click 3.0 is the full support for return
values from command callbacks.  This enables a whole range of features
that were previously hard to implement.

In essence any command callback can now return a value.  This return value
is bubbled to certain receivers.  One usecase for this has already been
show in the example of :ref:`command-chaining` where it has been
demonstrated that chained groups can have callbacks that process
all return values.

When working with command return values in Click, this is what you need to
know:

-   The return value of a command callback is generally returned from the
    :meth:`Command.invoke` method.  The exception to this rule has to
    do with :class:`Group`\s:

    *   In a group the return value is generally the return value of the
        subcommand invoked.  The only exception to this rule is that the
        return value is the return value of the group callback if it's
        invoked without arguments and `invoke_without_command` is enabled.
    *   If a group is set up for chaining then the return value is a list
        of all subcommands' results.
    *   Return values of groups can be processed through a
        :attr:`Group.result_callback`.  This is invoked with the
        list of all return values in chain mode, or the single return
        value in case of non chained commands.

-   The return value is bubbled through from the :meth:`Context.invoke`
    and :meth:`Context.forward` methods.  This is useful in situations
    where you internally want to call into another command.

-   Click does not have any hard requirements for the return values and
    does not use them itself.  This allows return values to be used for
    custom decorators or workflows (like in the command chaining
    example).

-   When a Click script is invoked as command line application (through
    :meth:`Command.main`) the return value is ignored unless the
    `standalone_mode` is disabled in which case it's bubbled through.

```
---

## docs/complex.md

```markdown
(complex-guide)=

# Complex Applications

```{currentmodule} click
```

Click is designed to assist with the creation of complex and simple CLI tools
alike.  However, the power of its design is the ability to arbitrarily nest
systems together.  For instance, if you have ever used Django, you will
have realized that it provides a command line utility, but so does Celery.
When using Celery with Django, there are two tools that need to interact with
each other and be cross-configured.

In a theoretical world of two separate Click command line utilities, they
could solve this problem by nesting one inside the other.  For instance, the
web framework could also load the commands for the message queue framework.

```{contents}
---
depth: 1
local: true
---
```

## Basic Concepts

To understand how this works, you need to understand two concepts: contexts
and the calling convention.

### Contexts

Whenever a Click command is executed, a {class}`Context` object is created
which holds state for this particular invocation.  It remembers parsed
parameters, what command created it, which resources need to be cleaned up
at the end of the function, and so forth.  It can also optionally hold an
application-defined object.

Context objects build a linked list until they hit the top one.  Each context
is linked to a parent context.  This allows a command to work below
another command and store its own information there without having to be
afraid of altering up the state of the parent command.

Because the parent data is available, however, it is possible to navigate to
it if needed.

Most of the time, you do not see the context object, but when writing more
complex applications it comes in handy.  This brings us to the next point.

### Calling Convention

When a Click command callback is executed, it's passed all the non-hidden
parameters as keyword arguments.  Notably absent is the context.  However,
a callback can opt into being passed to the context object by marking itself
with {func}`pass_context`.

So how do you invoke a command callback if you don't know if it should
receive the context or not?  The answer is that the context itself
provides a helper function ({meth}`Context.invoke`) which can do this for
you.  It accepts the callback as first argument and then invokes the
function correctly.

## Building a Git Clone

In this example, we want to build a command line tool that resembles a
version control system.  Systems like Git usually provide one
over-arching command that already accepts some parameters and
configuration, and then have extra subcommands that do other things.

### The Root Command

At the top level, we need a group that can hold all our commands.  In this
case, we use the basic {func}`click.group` which allows us to register
other Click commands below it.

For this command, we also want to accept some parameters that configure the
state of our tool:

```{eval-rst}
.. click:example::

    import os
    import click


    class Repo(object):
        def __init__(self, home=None, debug=False):
            self.home = os.path.abspath(home or '.')
            self.debug = debug


    @click.group()
    @click.option('--repo-home', envvar='REPO_HOME', default='.repo')
    @click.option('--debug/--no-debug', default=False,
                  envvar='REPO_DEBUG')
    @click.pass_context
    def cli(ctx, repo_home, debug):
        ctx.obj = Repo(repo_home, debug)
```

Let's understand what this does.  We create a group command which can
have subcommands.  When it is invoked, it will create an instance of a
`Repo` class.  This holds the state for our command line tool.  In this
case, it just remembers some parameters, but at this point it could also
start loading configuration files and so on.

This state object is then remembered by the context as {attr}`~Context.obj`.
This is a special attribute where commands are supposed to remember what
they need to pass on to their children.

In order for this to work, we need to mark our function with
{func}`pass_context`, because otherwise, the context object would be
entirely hidden from us.

### The First Child Command

Let's add our first child command to it, the clone command:

```python
@cli.command()
@click.argument('src')
@click.argument('dest', required=False)
def clone(src, dest):
    pass
```

So now we have a clone command, but how do we get access to the repo?  As
you can imagine, one way is to use the {func}`pass_context` function which
again will make our callback also get the context passed on which we
memorized the repo.  However, there is a second version of this decorator
called {func}`pass_obj` which will just pass the stored object, (in our case
the repo):

```python
@cli.command()
@click.argument('src')
@click.argument('dest', required=False)
@click.pass_obj
def clone(repo, src, dest):
    pass
```

### Interleaved Commands

While not relevant for the particular program we want to build, there is
also quite good support for interleaving systems.  Imagine for instance that
there was a super cool plugin for our version control system that needed a
lot of configuration and wanted to store its own configuration as
{attr}`~Context.obj`.  If we would then attach another command below that,
we would all of a sudden get the plugin configuration instead of our repo
object.

One obvious way to remedy this is to store a reference to the repo in the
plugin, but then a command needs to be aware that it's attached below such a
plugin.

There is a much better system that can be built by taking advantage of the
linked nature of contexts.  We know that the plugin context is linked to the
context that created our repo.  Because of that, we can start a search for
the last level where the object stored by the context was a repo.

Built-in support for this is provided by the {func}`make_pass_decorator`
factory, which will create decorators for us that find objects (it
internally calls into {meth}`Context.find_object`).  In our case, we
know that we want to find the closest `Repo` object, so let's make a
decorator for this:

```python
pass_repo = click.make_pass_decorator(Repo)
```

If we now use `pass_repo` instead of `pass_obj`, we will always get a
repo instead of something else:

```python
@cli.command()
@click.argument('src')
@click.argument('dest', required=False)
@pass_repo
def clone(repo, src, dest):
    pass
```

### Ensuring Object Creation

The above example only works if there was an outer command that created a
`Repo` object and stored it in the context.  For some more advanced use
cases, this might become a problem.  The default behavior of
{func}`make_pass_decorator` is to call {meth}`Context.find_object`
which will find the object.  If it can't find the object,
{meth}`make_pass_decorator` will raise an error.
The alternative behavior is to use {meth}`Context.ensure_object`
which will find the object, and if it cannot find it, will create one and
store it in the innermost context.  This behavior can also be enabled for
{func}`make_pass_decorator` by passing `ensure=True`:

```python
pass_repo = click.make_pass_decorator(Repo, ensure=True)
```

In this case, the innermost context gets an object created if it is
missing.  This might replace objects being placed there earlier.  In this
case, the command stays executable, even if the outer command does not run.
For this to work, the object type needs to have a constructor that accepts
no arguments.

As such it runs standalone:

```python
@click.command()
@pass_repo
def cp(repo):
    click.echo(isinstance(repo, Repo))
```
As you can see:

```console
$ cp
True
```

## Lazily Loading Subcommands

Large CLIs and CLIs with slow imports may benefit from deferring the loading of
subcommands. The interfaces which support this mode of use are
{meth}`Group.list_commands` and {meth}`Group.get_command`. A custom
{class}`Group` subclass can implement a lazy loader by storing extra data such
that {meth}`Group.get_command` is responsible for running imports.

Since the primary case for this is a {class}`Group` which loads its subcommands lazily,
the following example shows a lazy-group implementation.

```{warning}
Lazy loading of python code can result in hard to track down bugs, circular imports
in order-dependent codebases, and other surprising behaviors. It is recommended that
this technique only be used in concert with testing which will at least run the
`--help` on each subcommand. That will guarantee that each subcommand can be loaded
successfully.
```

### Defining the Lazy Group

The following {class}`Group` subclass adds an attribute, `lazy_subcommands`, which
stores a mapping from subcommand names to the information for importing them.


```python
# in lazy_group.py
import importlib
import click

class LazyGroup(click.Group):
    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        # lazy_subcommands is a map of the form:
        #
        #   {command-name} -> {module-name}.{command-object-name}
        #
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        base = super().list_commands(ctx)
        lazy = sorted(self.lazy_subcommands.keys())
        return base + lazy

    def get_command(self, ctx, cmd_name):
        if cmd_name in self.lazy_subcommands:
            return self._lazy_load(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _lazy_load(self, cmd_name):
        # lazily loading a command, first get the module name and attribute name
        import_path = self.lazy_subcommands[cmd_name]
        modname, cmd_object_name = import_path.rsplit(".", 1)
        # do the import
        mod = importlib.import_module(modname)
        # get the Command object from that module
        cmd_object = getattr(mod, cmd_object_name)
        # check the result to make debugging easier
        if not isinstance(cmd_object, click.Command):
            raise ValueError(
                f"Lazy loading of {import_path} failed by returning "
                "a non-command object"
            )
        return cmd_object
```

### Using LazyGroup To Define a CLI

With `LazyGroup` defined, it's now possible to write a group which lazily loads its
subcommands like so:

```python
# in main.py
import click
from lazy_group import LazyGroup

@click.group(
    cls=LazyGroup,
    lazy_subcommands={"foo": "foo.cli", "bar": "bar.cli"},
    help="main CLI command for lazy example",
)
def cli():
    pass
```

```python
# in foo.py
import click

@click.group(help="foo command for lazy example")
def cli():
    pass
```

```python
# in bar.py
import click
from lazy_group import LazyGroup

@click.group(
    cls=LazyGroup,
    lazy_subcommands={"baz": "baz.cli"},
    help="bar command for lazy example",
)
def cli():
    pass
```

```python
# in baz.py
import click

@click.group(help="baz command for lazy example")
def cli():
    pass
```

### What triggers Lazy Loading?

There are several events which may trigger lazy loading by running the
{meth}`Group.get_command` function.
Some are intuititve, and some are less so.

All cases are described with respect to the above example, assuming the main program
name is `cli`.

1. Command resolution. If a user runs `cli bar baz`, this must first resolve `bar`,
   and then resolve `baz`. Each subcommand resolution step does a lazy load.
2. Helptext rendering. In order to get the short help description of subcommands,
   `cli --help` will load `foo` and `bar`. Note that it will still not load
   `baz`.
3. Shell completion. In order to get the subcommands of a lazy command, `cli <TAB>`
   will need to resolve the subcommands of `cli`. This process will trigger the lazy
   loads.

### Further Deferring Imports

It is possible to make the process even lazier, but it is generally more difficult the
more you want to defer work.

For example, subcommands could be represented as a custom {class}`Command` subclass
which defers importing the command until it is invoked, but which provides
{meth}`Command.get_short_help_str` in order to support completions and helptext.
More simply, commands can be constructed whose callback functions defer any actual work
until after an import.

This command definition provides `foo`, but any of the work associated with importing
the "real" callback function is deferred until invocation time:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option("-n", type=int)
    @click.option("-w", type=str)
    def foo(n, w):
        from mylibrary import foo_concrete

        foo_concrete(n, w)
```

Because Click builds helptext and usage info from options, arguments, and command
attributes, it has no awareness that the underlying function is in any way handling a
deferred import. Therefore, all Click-provided utilities and functionality will work
as normal on such a command.

```
---

## docs/conf.py

```python
from pallets_sphinx_themes import get_version
from pallets_sphinx_themes import ProjectLink

# Project --------------------------------------------------------------

project = "Click"
copyright = "2014 Pallets"
author = "Pallets"
release, version = get_version("Click")

# General --------------------------------------------------------------

master_doc = "index"
default_role = "code"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_tabs.tabs",
    "sphinxcontrib.log_cabinet",
    "pallets_sphinx_themes",
    "myst_parser",
]
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_preserve_defaults = True
extlinks = {
    "issue": ("https://github.com/pallets/click/issues/%s", "#%s"),
    "pr": ("https://github.com/pallets/click/pull/%s", "#%s"),
}
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
}

# HTML -----------------------------------------------------------------

html_theme = "click"
html_theme_options = {"index_sidebar_logo": False}
html_context = {
    "project_links": [
        ProjectLink("Donate", "https://palletsprojects.com/donate"),
        ProjectLink("PyPI Releases", "https://pypi.org/project/click/"),
        ProjectLink("Source Code", "https://github.com/pallets/click/"),
        ProjectLink("Issue Tracker", "https://github.com/pallets/click/issues/"),
        ProjectLink("Chat", "https://discord.gg/pallets"),
    ]
}
html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html", "ethicalads.html"],
    "**": ["localtoc.html", "relations.html", "searchbox.html", "ethicalads.html"],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html", "ethicalads.html"]}
html_static_path = ["_static"]
html_favicon = "_static/click-icon.svg"
html_logo = "_static/click-logo.svg"
html_title = f"Click Documentation ({version})"
html_show_sourcelink = False

```
---

## docs/contrib.md

```markdown
(contrib)=

# click-contrib

As the user number of Click grows, more and more major feature requests are
made. To users, it may seem reasonable to include those features with Click;
however, many of them are experimental or aren't practical to support
generically. Maintainers have to choose what is reasonable to maintain in Click
core.

The [click-contrib](https://github.com/click-contrib/) GitHub organization exists as a place to collect third-party
packages that extend Click's features. It is also meant to ease the effort of
searching for such extensions.

Please note that the quality and stability of those packages may be different
from Click itself. While published under a common organization, they are still
separate from Click and the Pallets maintainers.

## Third-party projects

Other projects that extend Click's features are available outside the
[click-contrib](https://github.com/click-contrib/) organization.

Some of the most popular and actively maintained are listed below:

| Project                                                 | Description                                                                          | Popularity                                                                                             | Activity                                                                                                    |
|---------------------------------------------------------|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| [Typer](https://github.com/fastapi/typer)               | Use Python type hints to create CLI apps.                                            | ![GitHub stars](https://img.shields.io/github/stars/fastapi/typer?label=%20&style=flat-square)         | ![Last commit](https://img.shields.io/github/last-commit/fastapi/typer?label=%20&style=flat-square)         |
| [rich-click](https://github.com/ewels/rich-click)       | Format help output with Rich.                                                        | ![GitHub stars](https://img.shields.io/github/stars/ewels/rich-click?label=%20&style=flat-square)      | ![Last commit](https://img.shields.io/github/last-commit/ewels/rich-click?label=%20&style=flat-square)      |
| [click-app](https://github.com/simonw/click-app)        | Cookiecutter template for creating new CLIs.                                         | ![GitHub stars](https://img.shields.io/github/stars/simonw/click-app?label=%20&style=flat-square)      | ![Last commit](https://img.shields.io/github/last-commit/simonw/click-app?label=%20&style=flat-square)      |
| [Cloup](https://github.com/janluke/cloup)               | Adds option groups, constraints, command aliases, help themes, suggestions and more. | ![GitHub stars](https://img.shields.io/github/stars/janluke/cloup?label=%20&style=flat-square)         | ![Last commit](https://img.shields.io/github/last-commit/janluke/cloup?label=%20&style=flat-square)         |
| [Click Extra](https://github.com/kdeldycke/click-extra) | Cloup + colorful `--help`, `--config`, `--show-params`, `--verbosity` options, etc.  | ![GitHub stars](https://img.shields.io/github/stars/kdeldycke/click-extra?label=%20&style=flat-square) | ![Last commit](https://img.shields.io/github/last-commit/kdeldycke/click-extra?label=%20&style=flat-square) |

```{note}
To make it into the list above, a project:

- must be actively maintained (at least one commit in the last year)
- must have a reasonable number of stars (at least 20)

If you have a project that meets these criteria, please open a pull request
to add it to the list.

If a project is no longer maintained or does not meet the criteria above,
please open a pull request to remove it from the list.
```

```
---

## docs/design-opinions.md

```markdown
# CLI Design Opinions

```{currentmodule} click
```
A penny for your thoughts...

```{contents}
:depth: 1
:local: true
```

## Options over arguments
{ref}`Positional arguments <arguments>` should be used sparingly, and if used should be required:
- The more positional arguments there are, the more confusing the CLI invocation becomes to read. (This is true of Python too.)
- Making some arguments optional, or arbitrary length, can make it harder to reason about. The parser handles this consistently by filling left to right, with an error if there is a non-optional unfilled after that. But that's not obvious to a user just looking at a command line.
- A command should be doing one thing, and the arguments should be related directly to that.
    - A group, where the argument is the sub-command name.
    - A command acts on some files.
    - A command looks at a source and acts on a destination.

```
---

## docs/documentation.md

```markdown
# Help Pages

```{currentmodule} click
```

Click makes it very easy to document your command line tools. For most things Click automatically generates help pages for you. By design the text is customizable, but the layout is not.

## Help Texts

Commands and options accept help arguments. For commands, the docstring of the function is automatically used if provided.

Simple example:

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('name')
    @click.option('--count', default=1, help='number of greetings')
    def hello(name: str, count: int):
        """This script prints hello and a name one or more times."""
        for x in range(count):
            if name:
                click.echo(f"Hello {name}!")
            else:
                click.echo("Hello!")

.. click:run::
    invoke(hello, args=['--help'])
```

## Command Short Help

For subcommands, a short help snippet is generated. By default, it's the first sentence of the docstring. If too long, then it will ellipsize what cannot be fit on a single line with `...`. The short help snippet can also be overridden with `short_help`:

```{eval-rst}
.. click:example::

    import click

    @click.group()
    def cli():
        """A simple command line tool."""

    @cli.command('init', short_help='init the repo')
    def init():
        """Initializes the repository."""

.. click:run::
    invoke(cli, args=['--help'])
```

## Command Epilog Help

The help epilog is printed at the end of the help and is useful for showing example command usages or referencing additional help resources.

```{eval-rst}
.. click:example::

    import click

    @click.command(
        epilog='See https://example.com for more details',
        )
    def init():
        """Initializes the repository."""

.. click:run::
    invoke(init, args=['--help'])
```

(documenting-arguments)=

## Documenting Arguments

{class}`click.argument` does not take a `help` parameter. This follows the Unix Command Line Tools convention of using arguments only for necessary things and documenting them in the command help text
by name. This should then be done via the docstring.

A brief example:

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        """Print FILENAME."""
        click.echo(filename)

.. click:run::
    invoke(touch, args=['--help'])
```

Or more explicitly:

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('filename')
    def touch(filename):
        """Print FILENAME.

        FILENAME is the name of the file to check.
        """
        click.echo(filename)

.. click:run::
    invoke(touch, args=['--help'])
```

## Showing Defaults

To control the appearance of defaults pass `show_default`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--n', default=1, show_default=False, help='number of dots')
    def dots(n):
        click.echo('.' * n)

.. click:run::
    invoke(dots, args=['--help'])
```

For single option boolean flags, the default remains hidden if the default value is False, even if show default is set to true.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--n', default=1, show_default=True)
    @click.option("--gr", is_flag=True, show_default=True, default=False, help="Greet the world.")
    @click.option("--br", is_flag=True, show_default=True, default=True, help="Add a thematic break")
    def dots(n, gr, br):
        if gr:
            click.echo('Hello world!')
        click.echo('.' * n)
        if br:
            click.echo('-' * n)

.. click:run::
   invoke(dots, args=['--help'])
```

## Showing Environment Variables

To control the appearance of environment variables pass `show_envvar`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--username', envvar='USERNAME', show_envvar=True)
    def greet(username):
        click.echo(f'Hello {username}!')

.. click:run::
    invoke(greet, args=['--help'])
```

## Click's Wrapping Behavior

Click's default wrapping ignores single new lines and rewraps the text based on the width of the terminal to a maximum of 80 characters by default, but this can be modified with {attr}`~Context.max_content_width`. In the example notice how the second grouping of three lines is rewrapped into a single paragraph.

```{eval-rst}
.. click:example::

    import click

    @click.command()
    def cli():
        """
        This is a very long paragraph and as you
        can see wrapped very early in the source text
        but will be rewrapped to the terminal width in
        the final output.

        This is
        a paragraph
        that is compacted.
        """

.. click:run::
    invoke(cli, args=['--help'])
```

## Escaping Click's Wrapping

Sometimes Click's wrapping can be a problem, such as when showing code examples where new lines are significant. This behavior can be escaped on a per-paragraph basis by adding a line with only `\b` . The `\b` is removed from the rendered help text.

Example:

```{eval-rst}
.. click:example::

    import click

    @click.command()
    def cli():
        """First paragraph.

        \b
        This is
        a paragraph
        without rewrapping.

        And this is a paragraph
        that will be rewrapped again.
        """

.. click:run::
    invoke(cli, args=['--help'])
```

To change the rendering maximum width, pass `max_content_width` when calling the command.

```bash
cli(max_content_width=120)
```

## Truncating Help Texts

Click gets {class}`Command` help text from the docstring. If you do not want to include part of the docstring, add the `\f` escape marker to have Click truncate the help text after the marker.

Example:

```{eval-rst}
.. click:example::

    import click

    @click.command()
    def cli():
        """First paragraph.
        \f

        Words to not be included.
        """

.. click:run::
    invoke(cli, args=['--help'])
```

(doc-meta-variables)=

## Placeholder / Meta Variable

The default placeholder variable ([meta variable](https://en.wikipedia.org/wiki/Metasyntactic_variable#IETF_Requests_for_Comments)) in the help pages is the parameter name in uppercase with underscores. This can be changed for Commands and Parameters with the `options_metavar` and `metavar` kwargs.

```{eval-rst}
.. click:example::

    # This controls entry on the usage line.
    @click.command(options_metavar='[[options]]')
    @click.option('--count', default=1, help='number of greetings',
                  metavar='<int>')
    @click.argument('name', metavar='<name>')
    def hello(name: str, count: int) -> None:
        """This script prints 'hello <name>' a total of <count> times."""
        for x in range(count):
            click.echo(f"Hello {name}!")

# Example usage:

.. click:run::
    invoke(hello, args=['--help'])

```

## Help Parameter Customization

Help parameters are automatically added by Click for any command. The default is `--help` but can be overridden by the context setting {attr}`~Context.help_option_names`. Click also performs automatic conflict resolution on the default help parameter, so if a command itself implements a parameter named `help` then the default help will not be run.

This example changes the default parameters to `-h` and `--help`
instead of just `--help`:

```{eval-rst}
.. click:example::

    import click

    CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

    @click.command(context_settings=CONTEXT_SETTINGS)
    def cli():
        pass

.. click:run::
    invoke(cli, ['-h'])
```

```
---

## docs/entry-points.md

```markdown
# Packaging Entry Points

```{eval-rst}
.. currentmodule:: click
```

It's recommended to write command line utilities as installable packages with
entry points instead of telling users to run ``python hello.py``.

A distribution package is a ``.whl`` file you install with pip or another Python
installer. You use a ``pyproject.toml`` file to describe the project and how it
is built into a package. You might upload this package to PyPI, or distribute it
to your users in another way.

Python installers create executable scripts that will run a specified Python
function. These are known as "entry points". The installer knows how to create
an executable regardless of the operating system, so it will work on Linux,
Windows, MacOS, etc.

## Project Files

To install your app with an entry point, all you need is the script and a
``pyproject.toml`` file. Here's an example project directory:

```text
hello-project/
    src/
        hello/
            __init__.py
            hello.py
    pyproject.toml
```

Contents of ``hello.py``:

```{eval-rst}
.. click:example::
    import click

    @click.command()
    def cli():
        """Prints a greeting."""
        click.echo("Hello, World!")
```

Contents of ``pyproject.toml``:

```toml
[project]
name = "hello"
version = "1.0.0"
description = "Hello CLI"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
]

[project.scripts]
hello = "hello.hello:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"
```

The magic is in the ``project.scripts`` section. Each line identifies one executable
script. The first part before the equals sign (``=``) is the name of the script that
should be generated, the second part is the import path followed by a colon
(``:``) with the function to call (the Click command).

## Installation

When your package is installed, the installer will create an executable script
based on the configuration. During development, you can install in editable
mode using the ``-e`` option. Remember to use a virtual environment!

```console
$ python -m venv .venv
$ . .venv/bin/activate
$ pip install -e .
```

Afterwards, your command should be available:

```console
$ hello
Hello, World!
```

```
---

## docs/exceptions.md

```markdown
(exception-handling-exit-codes)=

# Exception Handling and Exit Codes

```{eval-rst}
.. currentmodule:: click
```

Click internally uses exceptions to signal various error conditions that
the user of the application might have caused. Primarily this is things
like incorrect usage.

```{contents}
:depth: 1
:local:
```

## Where are Errors Handled?

Click's main error handling is happening in {meth}`Command.main`. In
there it handles all subclasses of {exc}`ClickException` as well as the
standard {exc}`EOFError` and {exc}`KeyboardInterrupt` exceptions. The
latter are internally translated into an {exc}`Abort`.

The logic applied is the following:

1. If an {exc}`EOFError` or {exc}`KeyboardInterrupt` happens, reraise it
   as {exc}`Abort`.
2. If a {exc}`ClickException` is raised, invoke the
   {meth}`ClickException.show` method on it to display it and then exit
   the program with {attr}`ClickException.exit_code`.
3. If an {exc}`Abort` exception is raised print the string ``Aborted!``
   to standard error and exit the program with exit code ``1``.
4. If it goes through well, exit the program with exit code ``0``.

## What if I Don't Want That?

Generally you always have the option to invoke the {meth}`Command.invoke`
method yourself. For instance if you have a {class}`Command` you can
invoke it manually like this:

```python
ctx = command.make_context("command-name", ["args", "go", "here"])
with ctx:
    result = command.invoke(ctx)
```

In this case exceptions will not be handled at all and bubbled up as you
would expect.

Starting with Click 3.0 you can also use the {meth}`Command.main` method
but disable the standalone mode which will do two things: disable
exception handling and disable the implicit {func}`sys.exit` at the end.

So you can do something like this:

```python
command.main(
    ["command-name", "args", "go", "here"],
    standalone_mode=False,
)
```

## Which Exceptions Exist?

Click has two exception bases: {exc}`ClickException` which is raised for
all exceptions that Click wants to signal to the user and {exc}`Abort`
which is used to instruct Click to abort the execution.

A {exc}`ClickException` has a {meth}`ClickException.show` method which
can render an error message to stderr or the given file object. If you
want to use the exception yourself for doing something check the API docs
about what else they provide.

The following common subclasses exist:

- {exc}`UsageError` to inform the user that something went wrong.
- {exc}`BadParameter` to inform the user that something went wrong with
  a specific parameter. These are often handled internally in Click and
  augmented with extra information if possible. For instance if those
  are raised from a callback Click will automatically augment it with
  the parameter name if possible.
- {exc}`FileError` this is an error that is raised by the
  {class}`FileType` if Click encounters issues opening the file.

(help-page-exit-codes)=

## Help Pages and Exit Codes

Triggering the a help page intentionally (by passing in ``--help``)
returns exit code 0. If a help page is displayed due to incorrect user
input, the program returns exit code 2. See {ref}`exit-codes` for more
general information.

For clarity, here is an example.

```{eval-rst}
.. click:example::

    @click.group('printer_group')
    def printer_group():
        pass

    @printer_group.command('printer')
    @click.option('--this')
    def printer(this):
        if this:
            click.echo(this)

.. click:run::
    invoke(printer_group, args=['--help'])

The above invocation returns exit code 0.

.. click:run::
    invoke(printer_group, args=[])
```

The above invocation returns exit code 2 since the user invoked the command incorrectly. However, since this is such a common error when first using a command, Click invokes the help page for the user. To see that `printer-group` is an invalid invocation, turn `no_args_is_help` off.

```{eval-rst}
.. click:example::

    @click.group('printer_group', no_args_is_help=False)
    def printer_group():
        pass

    @printer_group.command('printer')
    @click.option('--this')
    def printer(this):
        if this:
            click.echo(this)

.. click:run::
    invoke(printer_group, args=[])
```

```
---

## docs/extending-click.md

```markdown
# Extending Click

```{currentmodule} click
```

In addition to common functionality that is implemented in the library itself, there are countless patterns that can be
implemented by extending Click. This page should give some insight into what can be accomplished.

```{contents}
:depth: 2
:local: true
```

(custom-groups)=

## Custom Groups

You can customize the behavior of a group beyond the arguments it accepts by subclassing {class}`click.Group`.

The most common methods to override are {meth}`~click.Group.get_command` and {meth}`~click.Group.list_commands`.

The following example implements a basic plugin system that loads commands from Python files in a folder. The command is
lazily loaded to avoid slow startup.

```python
import importlib.util
import os
import click

class PluginGroup(click.Group):
    def __init__(self, name=None, plugin_folder="commands", **kwargs):
        super().__init__(name=name, **kwargs)
        self.plugin_folder = plugin_folder

    def list_commands(self, ctx):
        rv = []

        for filename in os.listdir(self.plugin_folder):
            if filename.endswith(".py"):
                rv.append(filename[:-3])

        rv.sort()
        return rv

    def get_command(self, ctx, name):
        path = os.path.join(self.plugin_folder, f"{name}.py")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.cli

cli = PluginGroup(
    plugin_folder=os.path.join(os.path.dirname(__file__), "commands")
)

if __name__ == "__main__":
    cli()
```

Custom classes can also be used with decorators:

```python
@click.group(
    cls=PluginGroup,
    plugin_folder=os.path.join(os.path.dirname(__file__), "commands")
)
def cli():
    pass
```

(aliases)=

## Command Aliases

Many tools support aliases for commands. For example, you can configure `git` to accept `git ci` as alias for
`git commit`. Other tools also support auto-discovery for aliases by automatically shortening them.

It's possible to customize {class}`Group` to provide this functionality. As explained in {ref}`custom-groups`, a group
provides two methods: {meth}`~Group.list_commands` and {meth}`~Group.get_command`. In this particular case, you only
need to override the latter as you generally don't want to enumerate the aliases on the help page in order to avoid
confusion.

The following example implements a subclass of {class}`Group` that accepts a prefix for a command. If there was a
command called `push`, it would accept `pus` as an alias (so long as it was unique):

```{eval-rst}
.. click:example::

    class AliasedGroup(click.Group):
        def get_command(self, ctx, cmd_name):
            rv = super().get_command(ctx, cmd_name)

            if rv is not None:
                return rv

            matches = [
                x for x in self.list_commands(ctx)
                if x.startswith(cmd_name)
            ]

            if not matches:
                return None

            if len(matches) == 1:
                return click.Group.get_command(self, ctx, matches[0])

            ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

        def resolve_command(self, ctx, args):
            # always return the full command name
            _, cmd, args = super().resolve_command(ctx, args)
            return cmd.name, cmd, args
```

It can be used like this:

```python

    @click.group(cls=AliasedGroup)
    def cli():
        pass

    @cli.command
    def push():
        pass

    @cli.command
    def pop():
        pass
```

See the [alias example](https://github.com/pallets/click/tree/main/examples/aliases) in Click's repository for another example.

```
---

## docs/faqs.md

```markdown
# Frequently Asked Questions

```{contents}
:depth: 2
:local: true
```

## General

### Shell Variable Expansion On Windows

I have a simple Click app :

```
import click

@click.command()
@click.argument('message')
def main(message: str):
    click.echo(message)

if __name__ == '__main__':
    main()

```

When you pass an environment variable in the argument, it expands it:

```{code-block} powershell
> Desktop python foo.py '$M0/.viola/2025-01-25-17-20-23-307878'
> M:/home/ramrachum/.viola/2025-01-25-17-20-23-307878
>
```
Note that I used single quotes above, so my shell is not expanding the environment variable, Click does. How do I get Click to not expand it?

#### Answer

If you don't want Click to emulate (as best it can) unix expansion on Windows, pass windows_expand_args=False when calling the CLI.
Windows command line doesn't do any *, ~, or $ENV expansion. It also doesn't distinguish between double quotes and single quotes (where the later means "don't expand here"). Click emulates the expansion so that the app behaves similarly on both platforms, but doesn't receive information about what quotes were used.

```
---

## docs/handling-files.md

```markdown
(handling-files)=

# Handling Files

```{currentmodule} click
```

Click has built in features to support file and file path handling. The examples use arguments but the same principle
applies to options as well.

(file-args)=

## File Arguments

Click supports working with files with the {class}`File` type. Some notable features are:

- Support for `-` to mean a special file that refers to stdin when used for reading, and stdout when used for writing.
  This is a common pattern for POSIX command line utilities.
- Deals with `str` and `bytes` correctly for all versions of Python.

Example:

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('input', type=click.File('rb'))
    @click.argument('output', type=click.File('wb'))
    def inout(input, output):
        """Copy contents of INPUT to OUTPUT."""
        while True:
            chunk = input.read(1024)
            if not chunk:
                break
            output.write(chunk)

And from the command line:

.. click:run::

    with isolated_filesystem():
        invoke(inout, args=['-', 'hello.txt'], input=['hello'],
               terminate_input=True)
        invoke(inout, args=['hello.txt', '-'])
```

## File Path Arguments

For handling paths, the {class}`Path` type is better than a `str`. Some notable features are:

- The `exists` argument will verify whether the path exists.
- `readable`, `writable`, and `executable` can perform permission checks.
- `file_okay` and `dir_okay` allow specifying whether files/directories are accepted.
- Error messages are nicely formatted using {func}`format_filename` so any undecodable bytes will be printed nicely.

See {class}`Path` for all features.

Example:

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('filename', type=click.Path(exists=True))
    def touch(filename):
        """Print FILENAME if the file exists."""
        click.echo(click.format_filename(filename))

And from the command line:

.. click:run::

    with isolated_filesystem():
        with open('hello.txt', 'w') as f:
            f.write('Hello World!\n')
        invoke(touch, args=['hello.txt'])
        println()
        invoke(touch, args=['missing.txt'])
```

## File Opening Behaviors

The {class}`File` type attempts to be "intelligent" about when to open a file. Stdin/stdout and files opened for reading
will be opened immediately. This will give the user direct feedback when a file cannot be opened. Files opened for
writing will only be open on the first IO operation. This is done by automatically wrapping the file in a special
wrapper.

File open behavior can be controlled by the boolean kwarg `lazy`. If a file is opened lazily:

- A failure at first IO operation will happen by raising an {exc}`FileError`.
- It can help minimize resource handling confusion. If a file is opened in lazy mode, it will call
  {meth}`LazyFile.close_intelligently` to help figure out if the file needs closing or not. This is not needed for
  parameters, but is necessary for manually prompting. For manual prompts with the {func}`prompt` function you do not
  know if a stream like stdout was opened (which was already open before) or a real file was opened (that needs
  closing).

Since files opened for writing will typically empty the file, the lazy mode should only be disabled if the developer is
absolutely sure that this is intended behavior.

It is also possible to open files in atomic mode by passing `atomic=True`. In atomic mode, all writes go into a separate
file in the same folder, and upon completion, the file will be moved over to the original location. This is useful if a
file regularly read by other users is modified.

```
---

## docs/index.rst

```text
.. rst-class:: hide-header

Welcome to Click
================

.. image:: _static/click-name.svg
    :align: center
    :height: 200px

Click is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary.  It's the "Command
Line Interface Creation Kit".  It's highly configurable but comes with
sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun
while also preventing any frustration caused by the inability to implement
an intended CLI API.

Click in three points:

-   arbitrary nesting of commands
-   automatic help page generation
-   supports lazy loading of subcommands at runtime

What does it look like?  Here is an example of a simple Click program:

.. click:example::

    import click

    @click.command()
    @click.option('--count', default=1, help='Number of greetings.')
    @click.option('--name', prompt='Your name',
                  help='The person to greet.')
    def hello(count, name):
        """Simple program that greets NAME for a total of COUNT times."""
        for x in range(count):
            click.echo(f"Hello {name}!")

    if __name__ == '__main__':
        hello()

And what it looks like when run:

.. click:run::

    invoke(hello, ['--count=3'], prog_name='python hello.py', input='John\n')

It automatically generates nicely formatted help pages:

.. click:run::

    invoke(hello, ['--help'], prog_name='python hello.py')

You can get the library directly from PyPI::

    pip install click

Documentation
==============

.. toctree::
   :maxdepth: 2

   faqs

Tutorials
------------
.. toctree::
   :maxdepth: 1

   quickstart
   virtualenv

How to Guides
---------------
.. toctree::
   :maxdepth: 1

   entry-points
   setuptools
   upgrade-guides
   support-multiple-versions

Conceptual Guides
-------------------
.. toctree::
   :maxdepth: 1

   design-opinions
   why
   click-concepts

General Reference
--------------------

.. toctree::
   :maxdepth: 1

   parameters
   parameter-types
   options
   option-decorators
   arguments
   commands-and-groups
   commands
   documentation
   prompts
   handling-files
   advanced
   complex
   extending-click
   testing
   utils
   shell-completion
   exceptions
   command-line-reference
   unicode-support
   wincmd

API Reference
-------------------

.. toctree::
   :maxdepth: 2

   api

About Project
===============

* This documentation is structured according to `Diataxis <https://diataxis.fr/>`_ and written with `MyST <https://myst-parser.readthedocs.io/en/latest/>`_

* `Version Policy <https://palletsprojects.com/versions>`_

* `Contributing <https://palletsprojects.com/contributing/>`_

* `Donate <https://palletsprojects.com/donate>`_

.. toctree::
   :maxdepth: 1

   contrib
   license
   changes

```
---

## docs/license.md

```markdown
# BSD-3-Clause License

```{literalinclude} ../LICENSE.txt
---
language: text
---
```

```
---

## docs/option-decorators.md

```markdown
# Options Shortcut Decorators

```{currentmodule} click
```

For convenience commonly used combinations of options arguments are available as their own decorators.

```{contents}
---
depth: 2
local: true
---
```

## Password Option

Click supports hidden prompts and asking for confirmation. This is useful for password input:

```{eval-rst}
.. click:example::

    import codecs

    @click.command()
    @click.option(
        "--password", prompt=True, hide_input=True,
        confirmation_prompt=True
    )
    def encode(password):
        click.echo(f"encoded: {codecs.encode(password, 'rot13')}")

.. click:run::

    invoke(encode, input=['secret', 'secret'])
```

Because this combination of parameters is quite common, this can also be
replaced with the {func}`password_option` decorator:

```python
    @click.command()
    @click.password_option()
    def encrypt(password):
        click.echo(f"encoded: to {codecs.encode(password, 'rot13')}")
```

## Confirmation Option

For dangerous operations, it's very useful to be able to ask a user for confirmation. This can be done by adding a
boolean `--yes` flag and asking for confirmation if the user did not provide it and to fail in a callback:

```{eval-rst}
.. click:example::

    def abort_if_false(ctx, param, value):
        if not value:
            ctx.abort()

    @click.command()
    @click.option('--yes', is_flag=True, callback=abort_if_false,
                  expose_value=False,
                  prompt='Are you sure you want to drop the db?')
    def dropdb():
        click.echo('Dropped all tables!')

And what it looks like on the command line:

.. click:run::

    invoke(dropdb, input=['n'])
    invoke(dropdb, args=['--yes'])

Because this combination of parameters is quite common, this can also be
replaced with the :func:`confirmation_option` decorator:

.. click:example::

    @click.command()
    @click.confirmation_option(prompt='Are you sure you want to drop the db?')
    def dropdb():
        click.echo('Dropped all tables!')
```

## Version Option

{func}`version_option` adds a `--version` option which immediately prints the version number and exits the program.

```
---

## docs/options.md

```markdown
(options)=

# Options

```{eval-rst}
.. currentmodule:: click
```

Adding options to commands can be accomplished with the {func}`option`
decorator. At runtime the decorator invokes the {class}`Option` class. Options in Click are distinct from {ref}`positional arguments <arguments>`.

Useful and often used kwargs are:

- `default`: Passes a default.
- `help`: Sets help message.
- `nargs`: Sets the number of arguments.
- `required`: Makes option required.
- `type`: Sets {ref}`parameter type <parameter-types>`

```{contents}
:depth: 2
:local: true
```

## Option Decorator

Click expects you to pass at least two positional arguments to the option decorator. They are option name and function argument name.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--string-to-echo', 'string_to_echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)


.. click:run::

    invoke(echo, args=['--help'])
```

However, if you don't pass in the function argument name, then Click will try to infer it. A simple way to name your option is by taking the function argument, adding two dashes to the front and converting underscores to dashes. In this case, Click will infer the function argument name correctly so you can add only the option name.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--string-to-echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)

.. click:run::

    invoke(echo, args=['--string-to-echo', 'Hi!'])
```

More formally, Click will try to infer the function argument name by:

1. If a positional argument name does not have a prefix, it is chosen.
2. If a positional argument name starts with with two dashes, the first one given is chosen.
3. The first positional argument prefixed with one dash is chosen otherwise.

The chosen positional argument is converted to lower case, up to two dashes are removed from the beginning, and other dashes are converted to underscores to get the function argument name.

```{eval-rst}
.. list-table:: Examples
    :widths: 15 10
    :header-rows: 1

    * - Decorator Arguments
      - Function Name
    * - ``"-f", "--foo-bar"``
      - foo_bar
    * - ``"-x"``
      - x
    * - ``"-f", "--filename", "dest"``
      - dest
    * - ``"--CamelCase"``
      - camelcase
    * - ``"-f", "-fb"``
      - f
    * - ``"--f", "--foo-bar"``
      - f
    * - ``"---f"``
      - _f
```

## Basic Example

A simple {class}`click.Option` takes one argument. This will assume the argument is not required. If the decorated function takes an positional argument then None is passed it. This will also assume the type is `str`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--text')
    def print_this(text):
        click.echo(text)


.. click:run::

    invoke(print_this, args=['--text=this'])

    invoke(print_this, args=[])


.. click:run::

    invoke(print_this, args=['--help'])

```

## Setting a Default

Instead of setting the `type`, you may set a default and Click will try to infer the type.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--n', default=1)
    def dots(n):
        click.echo('.' * n)

.. click:run::

    invoke(dots, args=['--help'])
```

## Multi Value Options

To make an option take multiple values, pass in `nargs`. Note you may pass in any positive integer, but not -1. The values are passed to the underlying function as a tuple.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--pos', nargs=2, type=float)
    def findme(pos):
        a, b = pos
        click.echo(f"{a} / {b}")

.. click:run::

    invoke(findme, args=['--pos', '2.0', '3.0'])

```

(tuple-type)=

## Multi Value Options as Tuples

```{versionadded} 4.0
```

As you can see that by using `nargs` set to a specific number each item in
the resulting tuple is of the same type. This might not be what you want.
Commonly you might want to use different types for different indexes in
the tuple. For this you can directly specify a tuple as type:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--item', type=(str, int))
    def putitem(item):
        name, id = item
        click.echo(f"name={name} id={id}")


And on the command line:

.. click:run::

    invoke(putitem, args=['--item', 'peter', '1338'])
```

By using a tuple literal as type, `nargs` gets automatically set to the
length of the tuple and the {class}`click.Tuple` type is automatically
used. The above example is thus equivalent to this:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--item', nargs=2, type=click.Tuple([str, int]))
    def putitem(item):
        name, id = item
        click.echo(f"name={name} id={id}")
```

(multiple-options)=

## Multiple Options

The multiple options format allows options to take an arbitrary number of arguments (which is called variadic). The arguments are passed to the underlying function as a tuple. If set, the default must be a list or tuple. Setting a string as a default will be interpreted as list of characters.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--message', '-m', multiple=True)
    def commit(message):
        click.echo(message)
        for m in message:
            click.echo(m)

.. click:run::

    invoke(commit, args=['-m', 'foo', '-m', 'bar', '-m', 'here'])
```

## Counting

To count the occurrence of an option pass in `count=True`. If the option is not passed in, then the count is 0. Counting is commonly used for verbosity.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('-v', '--verbose', count=True)
    def log(verbose):
        click.echo(f"Verbosity: {verbose}")

.. click:run::

    invoke(log, args=[])
    invoke(log, args=['-vvv'])
```

(option-boolean-flag)=

## Boolean

Boolean options (boolean flags) take the value True or False. The simplest case sets the default value to `False` if the flag is not passed, and `True` if it is.

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--shout', is_flag=True)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)


.. click:run::

    invoke(info)
    invoke(info, args=['--shout'])

```

To implement this more explicitly, pass in on-option `/` off-option. Click will automatically set `is_flag=True`.

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--shout/--no-shout', default=False)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

.. click:run::

    invoke(info)
    invoke(info, args=['--shout'])
    invoke(info, args=['--no-shout'])
```

Use cases for this more explicit pattern include:

* The default can be dynamic so the user can explicitly specify the option with either on or off option, or pass in no option to use the dynamic default.
* Shell scripts sometimes want to be explicit even when it's the default
* Shell aliases can set a flag, then an invocation can add a negation of the flag

If a forward slash(`/`) is contained in your option name already, you can split the parameters using `;`. In Windows `/` is commonly used as the prefix character.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('/debug;/no-debug')
    def log(debug):
        click.echo(f"debug={debug}")
```

```{versionchanged} 6.0
```

If you want to define an alias for the second option only, then you will need to use leading whitespace to disambiguate the format string.

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--shout/--no-shout', ' /-N', default=False)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

.. click:run::

    invoke(info, args=['--help'])
```

## Flag Value

To have an flag pass a value to the underlying function set `flag_value`. This automatically sets `is_flag=True`. To mark the flag as default, set `default=True`. Setting flag values can be used to create patterns like this:

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--upper', 'transformation', flag_value='upper', default=True)
    @click.option('--lower', 'transformation', flag_value='lower')
    def info(transformation):
        click.echo(getattr(sys.platform, transformation)())

.. click:run::

    invoke(info, args=['--help'])
    invoke(info, args=['--upper'])
    invoke(info, args=['--lower'])
    invoke(info)
```

````{note}
The `default` value is given to the underlying function as-is. So if you set `default=None`, the value passed to the function is the `None` Python value. Same for any other type.

But there is a special case for flags. If a flag has a `flag_value`, then setting `default=True` is interpreted as *the flag should be activated by default*. So instead of the underlying function receiving the `True` Python value, it will receive the `flag_value`.

Which means, in example above, this option:

```python
@click.option('--upper', 'transformation', flag_value='upper', default=True)
```

is equivalent to:

```python
@click.option('--upper', 'transformation', flag_value='upper', default='upper')
```

Because the two are equivalent, it is recommended to always use the second form, and set `default` to the actual value you want to pass. And not use the special `True` case. This makes the code more explicit and predictable.
````

## Values from Environment Variables

To pass in a value in from a specific environment variable use `envvar`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--username', envvar='USERNAME')
    def greet(username):
       click.echo(f"Hello {username}!")

.. click:run::

    invoke(greet, env={'USERNAME': 'john'})
```

If a list is passed to `envvar`, the first environment variable found is picked.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--username', envvar=['ALT_USERNAME', 'USERNAME'])
    def greet(username):
       click.echo(f"Hello {username}!")

.. click:run::

    invoke(greet, env={'ALT_USERNAME': 'Bill', 'USERNAME': 'john'})

```

Variable names are:
 - [Case-insensitive on Windows but not on other platforms](https://github.com/python/cpython/blob/aa9eb5f757ceff461e6e996f12c89e5d9b583b01/Lib/os.py#L777-L789).
 - Not stripped of whitespaces and should match the exact name provided to the `envvar` argument.

For flag options, there is two concepts to consider: the activation of the flag driven by the environment variable, and the value of the flag if it is activated.

The environment variable need to be interpreted, because values read from them are always strings. We need to transform these strings into boolean values that will determine if the flag is activated or not.

Here are the rules used to parse environment variable values for flag options:
   - `true`, `1`, `yes`, `on`, `t`, `y` are interpreted as activating the flag
   - `false`, `0`, `no`, `off`, `f`, `n` are interpreted as deactivating the flag
   - The presence of the environment variable without value is interpreted as deactivating the flag
   - Empty strings are interpreted as deactivating the flag
   - Values are case-insensitive, so the `True`, `TRUE`, `tRuE` strings are all activating the flag
   - Values are stripped of leading and trailing whitespaces before being interpreted, so the `" True "` string is transformed to `"true"` and so activates the flag
   - If the flag option has a `flag_value` argument, passing that value in the environment variable will activate the flag, in addition to all the cases described above
   - Any other value is interpreted as deactivating the flag

```{caution}
For boolean flags with a pair of values, the only recognized environment variable is the one provided to the `envvar` argument.

So an option defined as `--flag\--no-flag`, with a `envvar="FLAG"` parameter, there is no magical `NO_FLAG=<anything>` variable that is recognized. Only the `FLAG=<anything>` environment variable is recognized.
```

Once the status of the flag has been determine to be activated or not, the `flag_value` is used as the value of the flag if it is activated. If the flag is not activated, the value of the flag is set to `None` by default.

## Multiple Options from Environment Values

As options can accept multiple values, pulling in such values from
environment variables (which are strings) is a bit more complex. The way
Click solves this is by leaving it up to the type to customize this
behavior. For both `multiple` and `nargs` with values other than
`1`, Click will invoke the {meth}`ParamType.split_envvar_value` method to
perform the splitting.

The default implementation for all types is to split on whitespace. The
exceptions to this rule are the {class}`File` and {class}`Path` types
which both split according to the operating system's path splitting rules.
On Unix systems like Linux and OS X, the splitting happens on
every colon (`:`), and for Windows, splitting on every semicolon (`;`).

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('paths', '--path', envvar='PATHS', multiple=True,
                  type=click.Path())
    def perform(paths):
        for path in paths:
            click.echo(path)

    if __name__ == '__main__':
        perform()

.. click:run::

    import os
    invoke(perform, env={"PATHS": f"./foo/bar{os.path.pathsep}./test"})
```

## Other Prefix Characters

Click can deal with prefix characters besides `-` for options. Click can use
`/`, `+` as well as others. Note that alternative prefix characters are generally used very sparingly if at all within POSIX.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('+w/-w')
    def chmod(w):
        click.echo(f"writable={w}")

.. click:run::

    invoke(chmod, args=['+w'])
    invoke(chmod, args=['-w'])
```

There are special considerations for using `/` as prefix character, see {ref}`option-boolean-flag` for more.

(optional-value)=

## Optional Value

Providing the value to an option can be made optional, in which case
providing only the option's flag without a value will either show a
prompt or use its `flag_value`.

Setting `is_flag=False, flag_value=value` tells Click that the option
can still be passed a value, but if only the flag is given, the
value will be `flag_value`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option("--name", is_flag=False, flag_value="Flag", default="Default")
    def hello(name):
        click.echo(f"Hello, {name}!")

.. click:run::

    invoke(hello, args=[])
    invoke(hello, args=["--name", "Value"])
    invoke(hello, args=["--name"])
```

```
---

## docs/parameter-types.md

```markdown
(parameter-types)=

# Parameter Types

```{currentmodule} click
```

When the parameter type is set using `type`, Click will leverage the type to make your life easier, for example adding
data to your help pages. Most examples are done with options, but types are available to options and arguments.

```{contents}
---
depth: 2
local: true
---
```

## Built-in Types Examples

(choice-opts)=

### Choice

Sometimes, you want to have a parameter be a choice of a list of values. In that case you can use {class}`Choice` type.
It can be instantiated with a list of valid values. The originally passed choice will be returned, not the str passed on
the command line. Token normalization functions and `case_sensitive=False` can cause the two to be different but still
match. {meth}`Choice.normalize_choice` for more info.


Example:

```{eval-rst}
.. click:example::

    import enum

    class HashType(enum.Enum):
        MD5 = enum.auto()
        SHA1 = enum.auto()

    @click.command()
    @click.option('--hash-type',
                  type=click.Choice(HashType, case_sensitive=False))
    def digest(hash_type: HashType):
        click.echo(hash_type)

What it looks like:

.. click:run::

    invoke(digest, args=['--hash-type=MD5'])
    println()
    invoke(digest, args=['--hash-type=md5'])
    println()
    invoke(digest, args=['--hash-type=foo'])
    println()
    invoke(digest, args=['--help'])
```

Any iterable may be passed to {class}`Choice`. If an `Enum` is passed, the names of the enum members will be used as
valid choices.

Choices work with options that have `multiple=True`. If a `default` value is given with `multiple=True`, it should be a
list or tuple of valid choices.

Choices should be unique after normalization, see {meth}`Choice.normalize_choice` for more info.

```{versionchanged} 7.1
The resulting value from an option will always be one of the originally passed choices
regardless of `case_sensitive`.
```

(ranges)=

### Int and Float Ranges

The {class}`IntRange` type extends the {data}`INT` type to ensure the value is contained in the given range. The
{class}`FloatRange` type does the same for {data}`FLOAT`.

If `min` or `max` is omitted, that side is *unbounded*. Any value in that direction is accepted. By default, both bounds
are *closed*, which means the boundary value is included in the accepted range. `min_open` and `max_open` can be used to
exclude that boundary from the range.

If `clamp` mode is enabled, a value that is outside the range is set to the boundary instead of failing. For example,
the range `0, 5` would return `5` for the value `10`, or `0` for the value `-1`. When using {class}`FloatRange`, `clamp`
can only be enabled if both bounds are *closed* (the default).

```{eval-rst}
.. click:example::

    @click.command()
    @click.option("--count", type=click.IntRange(0, 20, clamp=True))
    @click.option("--digit", type=click.IntRange(0, 9))
    def repeat(count, digit):
        click.echo(str(digit) * count)

.. click:run::

    invoke(repeat, args=['--count=100', '--digit=5'])
    invoke(repeat, args=['--count=6', '--digit=12'])
```

## Built-in Types Listing

The supported parameter {ref}`click-api-types` are

- `str` / {data}`click.STRING`: The default parameter type which indicates unicode strings.

- `int` / {data}`click.INT`: A parameter that only accepts integers.

- `float` / {data}`click.FLOAT`: A parameter that only accepts floating point values.

- `bool` / {data}`click.BOOL`: A parameter that accepts boolean values. This is automatically used for boolean flags.
  The string values "1", "true", "t", "yes", "y", and "on" convert to `True`. "0", "false", "f", "no", "n", and "off"
  convert to `False`.

- {data}`click.UUID`: A parameter that accepts UUID values. This is not automatically guessed but represented as
  {class}`uuid.UUID`.

```{eval-rst}
*   .. autoclass:: Choice
       :noindex:
```

```{eval-rst}
*   .. autoclass:: DateTime
       :noindex:
```

```{eval-rst}
*   .. autoclass:: File
       :noindex:
```

```{eval-rst}
*   .. autoclass:: FloatRange
       :noindex:
```

```{eval-rst}
*   .. autoclass:: IntRange
       :noindex:
```

```{eval-rst}
*   .. autoclass:: Path
       :noindex:
```

## How to Implement Custom Types

To implement a custom type, you need to subclass the {class}`ParamType` class. For simple cases, passing a Python
function that fails with a `ValueError` is also supported, though discouraged. Override the {meth}`~ParamType.convert`
method to convert the value from a string to the correct type.

The following code implements an integer type that accepts hex and octal numbers in addition to normal integers, and
converts them into regular integers.

```python
import click

class BasedIntParamType(click.ParamType):
    name = "integer"

    def convert(self, value, param, ctx):
        if isinstance(value, int):
            return value

        try:
            if value[:2].lower() == "0x":
                return int(value[2:], 16)
            elif value[:1] == "0":
                return int(value, 8)
            return int(value, 10)
        except ValueError:
            self.fail(f"{value!r} is not a valid integer", param, ctx)

BASED_INT = BasedIntParamType()
```

The {attr}`~ParamType.name` attribute is optional and is used for documentation. Call {meth}`~ParamType.fail` if
conversion fails. The `param` and `ctx` arguments may be `None` in some cases such as prompts.

Values from user input or the command line will be strings, but default values and Python arguments may already be the
correct type. The custom type should check at the top if the value is already valid and pass it through to support those
cases.

```
---

## docs/parameters.md

```markdown
(parameters)=

# Parameters

```{currentmodule} click
```

Click supports only two principle types of parameters for scripts (by design): options and arguments.

## Options

- Are optional.
- Recommended to use for everything except subcommands, urls, or files.
- Can take a fixed number of arguments. The default is 1. They may be specified multiple times using {ref}`multiple-options`.
- Are fully documented by the help page.
- Have automatic prompting for missing input.
- Can act as flags (boolean or otherwise).
- Can be pulled from environment variables.

## Arguments

- Are optional with in reason, but not entirely so.
- Recommended to use for subcommands, urls, or files.
- Can take an arbitrary number of arguments.
- Are not fully documented by the help page since they may be too specific to be automatically documented. For more see {ref}`documenting-arguments`.
- Can be pulled from environment variables but only explicitly named ones. For more see {ref}`environment-variables`.

On each principle type you can specify {ref}`parameter-types`. Specifying these types helps Click add details to your help pages and help with the handling of those types.

(parameter-names)=

## Parameter Names

Parameters (options and arguments) have a name that will be used as
the Python argument name when calling the decorated function with
values.

In the example, the argument's name is `filename`. The name must match the python arg name. To provide a different name for use in help text, see {ref}`doc-meta-variables`.
The option's names are `-t` and `--times`. More names are available for options and are covered in {ref}`options`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('filename')
    @click.option('-t', '--times', type=int)
    def multi_echo(filename, times):
        """Print value filename multiple times."""
        for x in range(times):
            click.echo(filename)

.. click:run::

    invoke(multi_echo, ['--times=3', 'index.txt'], prog_name='multi_echo')
```

```
---

## docs/prompts.md

```markdown
# User Input Prompts

```{currentmodule} click
```

Click supports prompts in two different places. The first is automated prompts when the parameter handling happens, and
the second is to ask for prompts at a later point independently.

This can be accomplished with the {func}`prompt` function, which asks for valid input according to a type, or the
{func}`confirm` function, which asks for confirmation (yes/no).

```{contents}
---
depth: 2
local: true
---
```

(option-prompting)=

## Option Prompts

Option prompts are integrated into the option interface. Internally, it automatically calls either {func}`prompt` or
{func}`confirm` as necessary.

In some cases, you want parameters that can be provided from the command line, but if not provided, ask for user input
instead. This can be implemented with Click by defining a prompt string.

Example:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--name', prompt=True)
    def hello(name):
        click.echo(f"Hello {name}!")

And what it looks like:

.. click:run::

    invoke(hello, args=['--name=John'])
    invoke(hello, input=['John'])
```

If you are not happy with the default prompt string, you can ask for
a different one:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--name', prompt='Your name please')
    def hello(name):
        click.echo(f"Hello {name}!")

What it looks like:

.. click:run::

    invoke(hello, input=['John'])
```

It is advised that prompt not be used in conjunction with the multiple flag set to True. Instead, prompt in the function
interactively.

By default, the user will be prompted for an input if one was not passed through the command line. To turn this behavior
off, see {ref}`optional-value`.

## Input Prompts

To manually ask for user input, you can use the {func}`prompt` function. By default, it accepts any Unicode string, but
you can ask for any other type. For instance, you can ask for a valid integer:

```python
value = click.prompt('Please enter a valid integer', type=int)
```

Additionally, the type will be determined automatically if a default value is provided. For instance, the following will
only accept floats:

```python
value = click.prompt('Please enter a number', default=42.0)
```

## Optional Prompts

If the option has `prompt` enabled, then setting `prompt_required=False` tells Click to only show the prompt if the
option's flag is given, instead of if the option is not provided at all.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--name', prompt=True, prompt_required=False, default="Default")
    def hello(name):
        click.echo(f"Hello {name}!")

.. click:run::

    invoke(hello)
    invoke(hello, args=["--name", "Value"])
    invoke(hello, args=["--name"], input="Prompt")
```

If `required=True`, then the option will still prompt if it is not given, but it will also prompt if only the flag is
given.

## Confirmation Prompts

To ask if a user wants to continue with an action, the {func}`confirm` function comes in handy. By default, it returns
the result of the prompt as a boolean value:

```python
if click.confirm('Do you want to continue?'):
    click.echo('Well done!')
```

There is also the option to make the function automatically abort the execution of the program if it does not return
`True`:

```python
click.confirm('Do you want to continue?', abort=True)
```

## Dynamic Defaults for Prompts

The `auto_envvar_prefix` and `default_map` options for the context allow the program to read option values from the
environment or a configuration file. However, this overrides the prompting mechanism, so that the user does not get the
option to change the value interactively.

If you want to let the user configure the default value, but still be prompted if the option isn't specified on the
command line, you can do so by supplying a callable as the default value. For example, to get a default from the
environment:

```python
import os

@click.command()
@click.option(
    "--username", prompt=True,
    default=lambda: os.environ.get("USER", "")
)
def hello(username):
    click.echo(f"Hello, {username}!")
```

To describe what the default value will be, set it in ``show_default``.

```{eval-rst}
.. click:example::

    import os

    @click.command()
    @click.option(
        "--username", prompt=True,
        default=lambda: os.environ.get("USER", ""),
        show_default="current user"
    )
    def hello(username):
        click.echo(f"Hello, {username}!")

.. click:run::

   invoke(hello, args=["--help"])
```

```
