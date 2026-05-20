# Repository Context Part 7/7

Generated for LLM prompt context.

## tests/test_termui.py

```python
import contextlib
import io
import platform
import shlex
import shutil
import sys
import tempfile
import time
from unittest.mock import patch

import pytest

import click
import click._termui_impl
from click._compat import WIN
from click._termui_impl import Editor
from click._utils import UNSET
from click.exceptions import BadParameter
from click.exceptions import MissingParameter


class FakeClock:
    def __init__(self):
        self.now = time.time()

    def advance_time(self, seconds=1):
        self.now += seconds

    def time(self):
        return self.now


def _create_progress(length=10, **kwargs):
    progress = click.progressbar(tuple(range(length)))
    for key, value in kwargs.items():
        setattr(progress, key, value)
    return progress


def test_progressbar_strip_regression(runner, monkeypatch):
    label = "    padded line"

    @click.command()
    def cli():
        with _create_progress(label=label) as progress:
            for _ in progress:
                pass

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    assert (
        label
        in runner.invoke(cli, [], standalone_mode=False, catch_exceptions=False).output
    )


def test_progressbar_length_hint(runner, monkeypatch):
    class Hinted:
        def __init__(self, n):
            self.items = list(range(n))

        def __length_hint__(self):
            return len(self.items)

        def __iter__(self):
            return self

        def __next__(self):
            if self.items:
                return self.items.pop()
            else:
                raise StopIteration

        next = __next__

    @click.command()
    def cli():
        with click.progressbar(Hinted(10), label="test") as progress:
            for _ in progress:
                pass

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    result = runner.invoke(cli, [])
    assert result.exception is None


def test_progressbar_no_tty(runner, monkeypatch):
    @click.command()
    def cli():
        with _create_progress(label="working") as progress:
            for _ in progress:
                pass

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: False)
    assert runner.invoke(cli, []).output == "working\n"


def test_progressbar_hidden_manual(runner, monkeypatch):
    @click.command()
    def cli():
        with _create_progress(label="see nothing", hidden=True) as progress:
            for _ in progress:
                pass

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    assert runner.invoke(cli, []).output == ""


@pytest.mark.parametrize("avg, expected", [([], 0.0), ([1, 4], 2.5)])
def test_progressbar_time_per_iteration(runner, avg, expected):
    with _create_progress(2, avg=avg) as progress:
        assert progress.time_per_iteration == expected


@pytest.mark.parametrize("finished, expected", [(False, 5), (True, 0)])
def test_progressbar_eta(runner, finished, expected):
    with _create_progress(2, finished=finished, avg=[1, 4]) as progress:
        assert progress.eta == expected


@pytest.mark.parametrize(
    "eta, expected",
    [
        (0, "00:00:00"),
        (30, "00:00:30"),
        (90, "00:01:30"),
        (900, "00:15:00"),
        (9000, "02:30:00"),
        (99999999999, "1157407d 09:46:39"),
        (None, ""),
    ],
)
def test_progressbar_format_eta(runner, eta, expected):
    with _create_progress(1, eta_known=eta is not None, avg=[eta]) as progress:
        assert progress.format_eta() == expected


@pytest.mark.parametrize("pos, length", [(0, 5), (-1, 1), (5, 5), (6, 5), (4, 0)])
def test_progressbar_format_pos(runner, pos, length):
    with _create_progress(length, pos=pos) as progress:
        result = progress.format_pos()
        assert result == f"{pos}/{length}"


@pytest.mark.parametrize(
    "length, finished, pos, avg, expected",
    [
        (8, False, 7, 0, "#######-"),
        (0, True, 8, 0, "########"),
    ],
)
def test_progressbar_format_bar(runner, length, finished, pos, avg, expected):
    with _create_progress(
        length, width=8, pos=pos, finished=finished, avg=[avg]
    ) as progress:
        assert progress.format_bar() == expected


@pytest.mark.parametrize(
    "length, show_percent, show_pos, pos, expected",
    [
        (0, True, True, 0, "  [--------]  0/0    0%"),
        (0, False, True, 0, "  [--------]  0/0"),
        (0, False, False, 0, "  [--------]"),
        (0, False, False, 0, "  [--------]"),
        (8, True, True, 8, "  [########]  8/8  100%"),
    ],
)
def test_progressbar_format_progress_line(
    runner, length, show_percent, show_pos, pos, expected
):
    with _create_progress(
        length,
        width=8,
        show_percent=show_percent,
        pos=pos,
        show_pos=show_pos,
    ) as progress:
        assert progress.format_progress_line() == expected


@pytest.mark.parametrize("test_item", ["test", None])
def test_progressbar_format_progress_line_with_show_func(runner, test_item):
    def item_show_func(item):
        return item

    with _create_progress(
        item_show_func=item_show_func, current_item=test_item
    ) as progress:
        if test_item:
            assert progress.format_progress_line().endswith(test_item)
        else:
            assert progress.format_progress_line().endswith(progress.format_pct())


def test_progressbar_init_exceptions(runner):
    with pytest.raises(TypeError, match="iterable or length is required"):
        click.progressbar()


def test_progressbar_iter_outside_with_exceptions(runner):
    progress = click.progressbar(length=2)

    with pytest.raises(RuntimeError, match="with block"):
        iter(progress)


def test_progressbar_is_iterator(runner, monkeypatch):
    @click.command()
    def cli():
        with click.progressbar(range(10), label="test") as progress:
            while True:
                try:
                    next(progress)
                except StopIteration:
                    break

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    result = runner.invoke(cli, [])
    assert result.exception is None


def test_choices_list_in_prompt(runner, monkeypatch):
    @click.command()
    @click.option(
        "-g", type=click.Choice(["none", "day", "week", "month"]), prompt=True
    )
    def cli_with_choices(g):
        pass

    @click.command()
    @click.option(
        "-g",
        type=click.Choice(["none", "day", "week", "month"]),
        prompt=True,
        show_choices=False,
    )
    def cli_without_choices(g):
        pass

    result = runner.invoke(cli_with_choices, [], input="none")
    assert "(none, day, week, month)" in result.output

    result = runner.invoke(cli_without_choices, [], input="none")
    assert "(none, day, week, month)" not in result.output


@pytest.mark.parametrize(
    "file_kwargs", [{"mode": "rt"}, {"mode": "rb"}, {"lazy": True}]
)
def test_file_prompt_default_format(runner, file_kwargs):
    @click.command()
    @click.option("-f", default=__file__, prompt="file", type=click.File(**file_kwargs))
    def cli(f):
        click.echo(f.name)

    result = runner.invoke(cli, input="\n")
    assert result.output == f"file [{__file__}]: \n{__file__}\n"


def test_secho(runner):
    with runner.isolation() as outstreams:
        click.secho(None, nl=False)
        bytes = outstreams[0].getvalue()
        assert bytes == b""


@pytest.mark.skipif(platform.system() == "Windows", reason="No style on Windows.")
@pytest.mark.parametrize(
    ("value", "expect"), [(123, b"\x1b[45m123\x1b[0m"), (b"test", b"test")]
)
def test_secho_non_text(runner, value, expect):
    with runner.isolation() as (out, _, _):
        click.secho(value, nl=False, color=True, bg="magenta")
        result = out.getvalue()
        assert result == expect


def test_progressbar_yields_all_items(runner):
    with click.progressbar(range(3)) as progress:
        assert len(list(progress)) == 3


def test_progressbar_update(runner, monkeypatch):
    fake_clock = FakeClock()

    @click.command()
    def cli():
        with click.progressbar(range(4)) as progress:
            for _ in progress:
                fake_clock.advance_time()
                print("")

    monkeypatch.setattr(time, "time", fake_clock.time)
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    output = runner.invoke(cli, []).output

    lines = [line for line in output.split("\n") if "[" in line]

    assert "  0%" in lines[0]
    assert " 25%  00:00:03" in lines[1]
    assert " 50%  00:00:02" in lines[2]
    assert " 75%  00:00:01" in lines[3]
    assert "100%          " in lines[4]


def test_progressbar_item_show_func(runner, monkeypatch):
    """item_show_func should show the current item being yielded."""

    @click.command()
    def cli():
        with click.progressbar(range(3), item_show_func=lambda x: str(x)) as progress:
            for item in progress:
                click.echo(f" item {item}")

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    lines = runner.invoke(cli).output.splitlines()

    for i, line in enumerate(x for x in lines if "item" in x):
        assert f"{i}    item {i}" in line


def test_progressbar_update_with_item_show_func(runner, monkeypatch):
    @click.command()
    def cli():
        with click.progressbar(
            length=6, item_show_func=lambda x: f"Custom {x}"
        ) as progress:
            while not progress.finished:
                progress.update(2, progress.pos)
                click.echo()

    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    output = runner.invoke(cli, []).output

    lines = [line for line in output.split("\n") if "[" in line]

    assert "Custom 0" in lines[0]
    assert "Custom 2" in lines[1]
    assert "Custom 4" in lines[2]


def test_progress_bar_update_min_steps(runner):
    bar = _create_progress(update_min_steps=5)
    bar.update(3)
    assert bar._completed_intervals == 3
    assert bar.pos == 0
    bar.update(2)
    assert bar._completed_intervals == 0
    assert bar.pos == 5


@pytest.mark.parametrize("key_char", ("h", "H", "é", "À", " ", "字", "àH", "àR"))
@pytest.mark.parametrize("echo", [True, False])
@pytest.mark.skipif(not WIN, reason="Tests user-input using the msvcrt module.")
def test_getchar_windows(runner, monkeypatch, key_char, echo):
    monkeypatch.setattr(click._termui_impl.msvcrt, "getwche", lambda: key_char)
    monkeypatch.setattr(click._termui_impl.msvcrt, "getwch", lambda: key_char)
    monkeypatch.setattr(click.termui, "_getchar", None)
    assert click.getchar(echo) == key_char


@pytest.mark.parametrize(
    "special_key_char, key_char", [("\x00", "a"), ("\x00", "b"), ("\xe0", "c")]
)
@pytest.mark.skipif(
    not WIN, reason="Tests special character inputs using the msvcrt module."
)
def test_getchar_special_key_windows(runner, monkeypatch, special_key_char, key_char):
    ordered_inputs = [key_char, special_key_char]
    monkeypatch.setattr(
        click._termui_impl.msvcrt, "getwch", lambda: ordered_inputs.pop()
    )
    monkeypatch.setattr(click.termui, "_getchar", None)
    assert click.getchar() == f"{special_key_char}{key_char}"


@pytest.mark.parametrize(
    ("key_char", "exc"), [("\x03", KeyboardInterrupt), ("\x1a", EOFError)]
)
@pytest.mark.skipif(not WIN, reason="Tests user-input using the msvcrt module.")
def test_getchar_windows_exceptions(runner, monkeypatch, key_char, exc):
    monkeypatch.setattr(click._termui_impl.msvcrt, "getwch", lambda: key_char)
    monkeypatch.setattr(click.termui, "_getchar", None)

    with pytest.raises(exc):
        click.getchar()


@pytest.mark.skipif(platform.system() == "Windows", reason="No sed on Windows.")
def test_fast_edit(runner):
    result = click.edit("a\nb", editor="sed -i~ 's/$/Test/'")
    assert result == "aTest\nbTest\n"


@pytest.mark.skipif(platform.system() == "Windows", reason="No sed on Windows.")
def test_edit(runner):
    with tempfile.NamedTemporaryFile(mode="w") as named_tempfile:
        named_tempfile.write("a\nb\n")
        named_tempfile.flush()

        result = click.edit(filename=named_tempfile.name, editor="sed -i~ 's/$/Test/'")
        assert result is None

        # We need to reopen the file as it becomes unreadable after the edit.
        with open(named_tempfile.name) as reopened_file:
            # POSIX says that when sed writes a pattern space to output then it
            # is immediately followed by a newline and so the expected result
            # should contain the newline.  However, some sed implementations
            # (e.g. GNU sed) does not terminate the last line in the output
            # with the newline in a case the input data missed newline at the
            # end of last line.  Hence the input data (see above) should be
            # terminated by newline too.
            assert reopened_file.read() == "aTest\nbTest\n"


@pytest.mark.parametrize(
    ("editor_cmd", "filenames", "expected_args"),
    [
        pytest.param(
            "myeditor --wait --flag",
            ["file1.txt", "file2.txt"],
            ["myeditor", "--wait", "--flag", "file1.txt", "file2.txt"],
            id="editor with args",
        ),
        pytest.param(
            "vi",
            ['file"; rm -rf / ; echo "'],
            ["vi", 'file"; rm -rf / ; echo "'],
            id="shell metacharacters in filename",
        ),
        # Issue #1026: editor path with spaces must be quoted.
        pytest.param(
            '"C:\\Program Files\\Sublime Text 3\\sublime_text.exe"',
            ["f.txt"],
            ["C:\\Program Files\\Sublime Text 3\\sublime_text.exe", "f.txt"],
            id="quoted windows path with spaces",
        ),
        # PR #1477: pager/editor command with flags, like ``less -FRSX``.
        pytest.param(
            "less -FRSX",
            ["f.txt"],
            ["less", "-FRSX", "f.txt"],
            id="command with flags",
        ),
        # Issue #1026: quoted command with ``--wait`` flag.
        pytest.param(
            '"my command" --option value arg',
            ["f.txt"],
            ["my command", "--option", "value", "arg", "f.txt"],
            id="quoted command with args",
        ),
        # PR #1477: unquoted unix path.
        pytest.param(
            "/usr/bin/vim",
            ["f.txt"],
            ["/usr/bin/vim", "f.txt"],
            id="unix absolute path",
        ),
        # Issue #1026: macOS path with escaped space.
        pytest.param(
            "/Applications/Sublime\\ Text.app/Contents/SharedSupport/bin/subl",
            ["f.txt"],
            ["/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl", "f.txt"],
            id="escaped space in unix path",
        ),
        pytest.param(
            "  vim  ",
            ["f.txt"],
            ["vim", "f.txt"],
            id="leading and trailing whitespace",
        ),
        pytest.param(
            "vim\tf.txt",
            [],
            ["vim", "f.txt"],
            id="tab-separated tokens",
        ),
        pytest.param(
            "'/Applications/My Editor.app/Contents/MacOS/editor'",
            ["f.txt"],
            ["/Applications/My Editor.app/Contents/MacOS/editor", "f.txt"],
            id="single-quoted path with spaces",
        ),
        pytest.param(
            '"my editor" --wait --new-window',
            ["file 1.txt", "file 2.txt"],
            ["my editor", "--wait", "--new-window", "file 1.txt", "file 2.txt"],
            id="quoted editor with multiple flags and filenames with spaces",
        ),
        pytest.param(
            "vim -u NONE -N",
            ["f.txt"],
            ["vim", "-u", "NONE", "-N", "f.txt"],
            id="multiple short flags",
        ),
        pytest.param(
            "editor",
            ['file"name.txt'],
            ["editor", 'file"name.txt'],
            id="filename with double quote",
        ),
        pytest.param(
            "editor",
            ["file'name.txt"],
            ["editor", "file'name.txt"],
            id="filename with single quote",
        ),
    ],
)
def test_editor_path_normalization(editor_cmd, filenames, expected_args):
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.wait.return_value = 0
        Editor(editor=editor_cmd).edit_files(filenames)

        mock_popen.assert_called_once()
        args = mock_popen.call_args[1].get("args") or mock_popen.call_args[0][0]
        assert args == expected_args
        assert mock_popen.call_args[1].get("shell") is None


@pytest.mark.skipif(not WIN, reason="Windows-specific editor paths")
@pytest.mark.parametrize(
    ("editor_cmd", "expected_cmd"),
    [
        pytest.param(
            "notepad",
            ["notepad"],
            id="plain notepad",
        ),
        pytest.param(
            '"C:\\Program Files\\Sublime Text 3\\sublime_text.exe" --wait',
            ["C:\\Program Files\\Sublime Text 3\\sublime_text.exe", "--wait"],
            id="quoted path with flag",
        ),
    ],
)
def test_editor_windows_path_normalization(editor_cmd, expected_cmd):
    """Windows-specific tests: verify ``Popen`` receives unquoted paths that
    ``subprocess.list2cmdline`` can re-quote for ``CreateProcess``."""
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.wait.return_value = 0
        Editor(editor=editor_cmd).edit_files(["f.txt"])

        args = mock_popen.call_args[1].get("args") or mock_popen.call_args[0][0]
        assert args == expected_cmd + ["f.txt"]
        assert mock_popen.call_args[1].get("shell") is None


def test_editor_env_passed_through():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.wait.return_value = 0
        Editor(editor="vi", env={"MY_VAR": "1"}).edit_files(["f.txt"])

        env = mock_popen.call_args[1].get("env")
        assert env is not None
        assert env["MY_VAR"] == "1"


def test_editor_failure_exception():
    with patch("subprocess.Popen") as mock_popen:
        mock_popen.return_value.wait.return_value = 1
        with pytest.raises(click.ClickException, match="Editing failed"):
            Editor(editor="vi").edit_files(["f.txt"])


def test_editor_nonexistent_exception():
    with patch("subprocess.Popen", side_effect=OSError("not found")):
        with pytest.raises(click.ClickException, match="not found"):
            Editor(editor="nonexistent").edit_files(["f.txt"])


@pytest.mark.parametrize(
    ("pager_env", "expected_parts"),
    [
        # Simple commands.
        pytest.param("cat", ["cat"], id="simple command"),
        pytest.param("less", ["less"], id="less"),
        pytest.param("less -FRSX", ["less", "-FRSX"], id="command with flags"),
        # Whitespace handling.
        pytest.param("", [], id="empty string"),
        pytest.param("   ", [], id="whitespace only"),
        pytest.param("  less  ", ["less"], id="leading and trailing spaces"),
        pytest.param("less\t-R", ["less", "-R"], id="tab as separator"),
        # Quoted Windows paths: quotes are stripped in POSIX mode (the
        # default), preserving backslashes inside quoted tokens (issue #1026).
        pytest.param(
            '"C:\\Program Files\\Git\\usr\\bin\\less.exe"',
            ["C:\\Program Files\\Git\\usr\\bin\\less.exe"],
            id="quoted windows path with spaces",
        ),
        pytest.param(
            '"C:\\Program Files\\Git\\usr\\bin\\less.exe" -R',
            ["C:\\Program Files\\Git\\usr\\bin\\less.exe", "-R"],
            id="quoted windows path with flag",
        ),
        # Single-quoted path.
        pytest.param(
            "'/usr/local/bin/my pager'",
            ["/usr/local/bin/my pager"],
            id="single-quoted path with spaces",
        ),
        # Unix paths.
        pytest.param("/usr/bin/less", ["/usr/bin/less"], id="unix absolute path"),
        pytest.param(
            "/usr/bin/my\\ pager",
            ["/usr/bin/my pager"],
            id="escaped space in unix path",
        ),
        # PR #1477: POSIX mode (the default) eats unquoted backslashes.
        # On Windows, users must quote paths that contain backslashes.
        pytest.param(
            "C:\\path\\to\\exe /test other\\path",
            ["C:pathtoexe", "/test", "otherpath"],
            id="unquoted backslashes eaten in POSIX mode",
        ),
    ],
)
def test_pager_shlex_split(pager_env, expected_parts):
    """Verify shlex.split produces the expected argv for PAGER values.

    Tests the splitting logic used by :func:`click._termui_impl.pager` to
    turn the ``PAGER`` environment variable into an ``argv`` list. See
    issue #1026, PR #1477, PR #1543, PR #2775.
    """
    assert shlex.split(pager_env) == expected_parts


def _get_real_pager_command() -> str:
    """Return a real pager binary path used to exercise the pipe pager branch.

    ..warning::
        Unix-only for now: ``more.com`` on Windows is interactive and goes
        through ``_tempfilepager`` rather than ``_pipepager``.
    """
    pager_path = shutil.which("cat")
    assert pager_path is not None, "cat not available"
    return pager_path


def _run_get_pager_file_with_real_pager(monkeypatch, capfd, writer, color=False):
    """Run through the pipe pager backend selected by ``PAGER``."""
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    monkeypatch.setitem(
        click._termui_impl.os.environ, "PAGER", _get_real_pager_command()
    )

    with click.get_pager_file(color=color) as pager:
        writer(pager)

    # The real pager writes to the process stdout; stderr should stay quiet.
    out, err = capfd.readouterr()
    assert err == ""
    return out


def _write_pager_from_multiple_sites(pager):
    pager.write("prefix\n")
    click.echo("middle", file=pager)
    pager.write("suffix\n")


@pytest.mark.skipif(
    WIN,
    reason="Exercises the pipe pager path; Windows uses _tempfilepager.",
)
@pytest.mark.parametrize(
    ("writer", "color", "expected"),
    [
        pytest.param(
            _write_pager_from_multiple_sites,
            False,
            "prefix\nmiddle\nsuffix\n",
            id="multiple write sites",
        ),
        pytest.param(
            lambda pager: pager.write("hello\n"), False, "hello\n", id="plain text"
        ),
        pytest.param(
            lambda pager: pager.write(click.style("hello", fg="red") + "\n"),
            False,
            "hello\n",
            id="strip ansi",
        ),
        pytest.param(
            lambda pager: pager.write(click.style("hello", fg="red") + "\n"),
            True,
            click.style("hello", fg="red") + "\n",
            id="preserve ansi",
        ),
        pytest.param(lambda pager: pager.write(""), False, "", id="empty string"),
    ],
)
def test_get_pager_file_with_real_pager_binary_stream(
    monkeypatch, capfd, writer, color, expected
):
    """A real pager should exercise the BinaryIO branch."""
    output = _run_get_pager_file_with_real_pager(
        monkeypatch, capfd, writer, color=color
    )

    assert output == expected


@pytest.mark.skipif(
    WIN,
    reason="Exercises the pipe pager path; Windows uses _tempfilepager.",
)
@pytest.mark.parametrize(
    ("color", "expected"),
    [
        pytest.param(False, "hello\n", id="strip ansi"),
        pytest.param(True, click.style("hello", fg="red") + "\n", id="preserve ansi"),
    ],
)
def test_echo_via_pager_real_pager_handles_ansi(monkeypatch, capfd, color, expected):
    """``echo_via_pager`` should honor ``color`` like ``get_pager_file``."""
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    monkeypatch.setitem(
        click._termui_impl.os.environ, "PAGER", _get_real_pager_command()
    )

    click.echo_via_pager(click.style("hello", fg="red"), color=color)

    out, err = capfd.readouterr()
    assert err == ""
    assert out == expected


def test_get_pager_file_pager_missing_binary_falls_back(monkeypatch, tmp_path):
    """``PAGER`` pointing to a nonexistent binary falls back to the text stdout."""
    pager_out = tmp_path / "pager_out.txt"

    monkeypatch.setitem(
        click._termui_impl.os.environ,
        "PAGER",
        "click-tests-nonexistent-pager-9b3f2",
    )
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)

    with pager_out.open("w", encoding="utf-8") as text_stream:
        monkeypatch.setattr(
            click._termui_impl, "_default_text_stdout", lambda: text_stream
        )

        with click.get_pager_file() as pager:
            pager.write("hello\n")

    assert pager_out.read_text(encoding="utf-8") == "hello\n"


def test_get_pager_file_pager_unset_falls_back_when_no_default(monkeypatch, tmp_path):
    """``PAGER`` unset still works when the platform default isn't installed."""
    pager_out = tmp_path / "pager_out.txt"

    monkeypatch.delitem(click._termui_impl.os.environ, "PAGER", raising=False)
    monkeypatch.delitem(click._termui_impl.os.environ, "TERM", raising=False)
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: True)
    monkeypatch.setattr(shutil, "which", lambda _name: None)

    with pager_out.open("w", encoding="utf-8") as text_stream:
        monkeypatch.setattr(
            click._termui_impl, "_default_text_stdout", lambda: text_stream
        )

        with click.get_pager_file() as pager:
            pager.write("hello\n")

    assert pager_out.read_text(encoding="utf-8") == "hello\n"


@pytest.mark.parametrize(
    ("color", "expected"),
    [
        pytest.param(False, "hello\n", id="strip ansi"),
        pytest.param(True, click.style("hello", fg="red") + "\n", id="preserve ansi"),
    ],
)
def test_get_pager_file_nullpager_wraps_textio_stream(
    monkeypatch, tmp_path, color, expected
):
    """When paging falls back to a real TextIO stream, ``.buffer`` is wrapped."""
    pager_out = tmp_path / "pager_out.txt"

    with pager_out.open("w", encoding="utf-8") as text_stream:
        monkeypatch.setattr(
            click._termui_impl, "_default_text_stdout", lambda: text_stream
        )
        monkeypatch.setattr(
            click._termui_impl, "isatty", lambda stream: stream is not sys.stdin
        )

        with click.get_pager_file(color=color) as pager:
            pager.write(click.style("hello", fg="red") + "\n")

    assert pager_out.read_text(encoding="utf-8") == expected


def test_get_pager_file_nullpager_keeps_stringio_stream(monkeypatch):
    """The no-stdout fallback should keep a text-only stream and set ``.color``."""

    created = []

    def make_stringio():
        stream = io.StringIO()
        created.append(stream)
        return stream

    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(click._termui_impl, "StringIO", make_stringio)
    monkeypatch.setattr(click._termui_impl, "isatty", lambda _: False)

    styled_text = click.style("hello", fg="red")

    with click.get_pager_file(color=False) as pager:
        assert pager is created[0]
        pager.write(styled_text)

    assert created[0].getvalue() == styled_text


def test_get_pager_file_flushes_stream_on_exception(monkeypatch):
    """Exceptions should still flush the yielded stream in ``finally``."""

    class FlushableTextStream(io.StringIO):
        def __init__(self):
            super().__init__()
            self.color = None
            self.flush_calls = 0

        def flush(self):
            self.flush_calls += 1

    stream = FlushableTextStream()

    @contextlib.contextmanager
    def pager_contextmanager(color=None):
        yield stream, "utf-8", color

    monkeypatch.setattr(
        click._termui_impl, "_pager_contextmanager", pager_contextmanager
    )

    with pytest.raises(RuntimeError, match="boom"):
        with click.get_pager_file() as pager:
            assert pager is stream
            raise RuntimeError("boom")

    assert stream.flush_calls == 1


def test_editor_unclosed_quote():
    """An unclosed quote in the editor command raises ValueError."""
    with pytest.raises(ValueError, match="No closing quotation"):
        Editor(editor='"unclosed').edit_files(["f.txt"])


@pytest.mark.parametrize(
    ("prompt_required", "required", "args", "expect"),
    [
        (True, False, None, "prompt"),
        (True, False, ["-v"], "Option '-v' requires an argument."),
        (False, True, None, "prompt"),
        (False, True, ["-v"], "prompt"),
    ],
)
def test_prompt_required_with_required(runner, prompt_required, required, args, expect):
    @click.command()
    @click.option("-v", prompt=True, prompt_required=prompt_required, required=required)
    def cli(v):
        click.echo(str(v))

    result = runner.invoke(cli, args, input="prompt")
    assert expect in result.output


@pytest.mark.parametrize(
    ("args", "expect"),
    [
        # Flag not passed, don't prompt.
        pytest.param(None, None, id="no flag"),
        # Flag and value passed, don't prompt.
        pytest.param(["-v", "value"], "value", id="short sep value"),
        pytest.param(["--value", "value"], "value", id="long sep value"),
        pytest.param(["-vvalue"], "value", id="short join value"),
        pytest.param(["--value=value"], "value", id="long join value"),
        # Flag without value passed, prompt.
        pytest.param(["-v"], "prompt", id="short no value"),
        pytest.param(["--value"], "prompt", id="long no value"),
        # Don't use next option flag as value.
        pytest.param(["-v", "-o", "42"], ("prompt", "42"), id="no value opt"),
    ],
)
def test_prompt_required_false(runner, args, expect):
    @click.command()
    @click.option("-v", "--value", prompt=True, prompt_required=False)
    @click.option("-o")
    def cli(value, o):
        if o is not None:
            return value, o

        return value

    result = runner.invoke(cli, args=args, input="prompt", standalone_mode=False)
    assert result.exception is None
    assert result.return_value == expect


@pytest.mark.parametrize(
    ("prompt", "input", "default", "expect"),
    [
        (True, "password\npassword", None, "password"),
        ("Confirm Password", "password\npassword\n", None, "password"),
        (True, "\n\n", "", ""),
        (False, None, None, None),
    ],
)
def test_confirmation_prompt(runner, prompt, input, default, expect):
    @click.command()
    @click.option(
        "--password",
        prompt=prompt,
        hide_input=True,
        default=default,
        confirmation_prompt=prompt,
    )
    def cli(password):
        return password

    result = runner.invoke(cli, input=input, standalone_mode=False)
    assert result.exception is None
    assert result.return_value == expect

    if prompt == "Confirm Password":
        assert "Confirm Password: " in result.output


def test_false_show_default_cause_no_default_display_in_prompt(runner):
    @click.command()
    @click.option("--arg1", show_default=False, prompt=True, default="my-default-value")
    def cmd(arg1):
        pass

    # Confirm that the default value is not included in the output when `show_default`
    # is False
    result = runner.invoke(cmd, input="my-input", standalone_mode=False)
    assert "my-default-value" not in result.output


@pytest.mark.parametrize(
    ("show_default", "default", "user_input", "in_prompt", "not_in_prompt"),
    [
        # Regular string replaces the actual default in the prompt.
        ("custom", "actual", "\n", "(custom)", "actual"),
        # String with spaces.
        ("custom label", "actual", "\n", "(custom label)", "actual"),
        # Unicode characters.
        ("∞", "0", "\n", "(∞)", None),
        # Numeric default: custom string hides the number.
        ("unlimited", 42, "\n", "(unlimited)", "42"),
        # Explicit default=None: custom string still appears, must provide input.
        ("computed at runtime", None, "value\n", "(computed at runtime)", None),
        # No default kwarg at all (internal UNSET sentinel): same as None.
        ("computed at runtime", UNSET, "value\n", "(computed at runtime)", None),
        # Empty string is falsy: suppresses any default display.
        ("", "actual", "\n", None, "actual"),
    ],
    ids=[
        "simple-string",
        "string-with-spaces",
        "unicode",
        "numeric-default",
        "default-is-none",
        "default-is-unset",
        "empty-string-is-falsy",
    ],
)
def test_string_show_default_in_prompt(
    runner, show_default, default, user_input, in_prompt, not_in_prompt
):
    """When show_default is a string, the prompt should display that
    string in parentheses instead of the actual default value,
    matching the help text behavior. See pallets/click#2836."""

    option_kwargs = {"show_default": show_default, "prompt": True}
    if default is not UNSET:
        option_kwargs["default"] = default

    @click.command()
    @click.option("--arg1", **option_kwargs)
    def cmd(arg1):
        click.echo(arg1)

    result = runner.invoke(cmd, input=user_input, standalone_mode=False)
    prompt_line = result.output.split("\n")[0]
    if in_prompt is not None:
        assert in_prompt in prompt_line
    if not_in_prompt is not None:
        assert not_in_prompt not in prompt_line


REPEAT = object()
"""Sentinel value to indicate that the prompt is expected to be repeated.

I.e. the value provided by the user is not satisfactory and need to be re-prompted.
"""

INVALID = object()
"""Sentinel value to indicate that the prompt is expected to be invalid.

On invalid input, Click will output an error message and re-prompt the user.
"""

BOOLEAN_FLAG_PROMPT_CASES = [
    ###
    ### Test cases with prompt=True explicitly enabled for the flag.
    ###
    # Prompt is allowed and the flag has no default, so it prompts.
    ({"prompt": True}, [], "[y/N]", "y", True),
    ({"prompt": True}, [], "[y/N]", "n", False),
    # Empty input default to False.
    ({"prompt": True}, [], "[y/N]", "", False),
    # Changing the default to True, makes the prompt change to [Y/n].
    ({"prompt": True, "default": True}, [], "[Y/n]", "", True),
    ({"prompt": True, "default": True}, [], "[Y/n]", "y", True),
    ({"prompt": True, "default": True}, [], "[Y/n]", "n", False),
    # False is the default's default, so it prompts with [y/N].
    ({"prompt": True, "default": False}, [], "[y/N]", "", False),
    ({"prompt": True, "default": False}, [], "[y/N]", "y", True),
    ({"prompt": True, "default": False}, [], "[y/N]", "n", False),
    # Defaulting to None, prompts with [y/n], which makes the user explicitly choose
    # between True or False.
    ({"prompt": True, "default": None}, [], "[y/n]", "y", True),
    ({"prompt": True, "default": None}, [], "[y/n]", "n", False),
    # Random string default is treated as a truthy value, so it prompts with [Y/n].
    ({"prompt": True, "default": "foo"}, [], "[Y/n]", "", True),
    ({"prompt": True, "default": "foo"}, [], "[Y/n]", "y", True),
    ({"prompt": True, "default": "foo"}, [], "[Y/n]", "n", False),
    ###
    ### Test cases with required=True explicitly enabled for the flag.
    ###
    # A required flag just raises an error unless a default is set.
    ({"required": True}, [], None, None, MissingParameter),
    ({"required": True, "default": True}, [], None, None, True),
    ({"required": True, "default": False}, [], None, None, False),
    ({"required": True, "default": None}, [], None, None, None),
    ({"required": True, "default": "on"}, [], None, None, True),
    ({"required": True, "default": "off"}, [], None, None, False),
    ({"required": True, "default": "foo"}, [], None, None, BadParameter),
    ###
    ### Explicitly passing the flag to the CLI bypass any prompt, whatever the
    ### configuration of the flag.
    ###
    # Flag allowing a prompt.
    ({"prompt": True}, ["--flag"], None, None, True),
    ({"prompt": True}, ["--no-flag"], None, None, False),
    ({"prompt": True, "default": None}, ["--flag"], None, None, True),
    ({"prompt": True, "default": None}, ["--no-flag"], None, None, False),
    ({"prompt": True, "default": True}, ["--flag"], None, None, True),
    ({"prompt": True, "default": True}, ["--no-flag"], None, None, False),
    ({"prompt": True, "default": False}, ["--flag"], None, None, True),
    ({"prompt": True, "default": False}, ["--no-flag"], None, None, False),
    ({"prompt": True, "default": "foo"}, ["--flag"], None, None, True),
    ({"prompt": True, "default": "foo"}, ["--no-flag"], None, None, False),
    # Required flag.
    ({"required": True}, ["--flag"], None, None, True),
    ({"required": True}, ["--no-flag"], None, None, False),
    ({"required": True, "default": None}, ["--flag"], None, None, True),
    ({"required": True, "default": None}, ["--no-flag"], None, None, False),
    ({"required": True, "default": True}, ["--flag"], None, None, True),
    ({"required": True, "default": True}, ["--no-flag"], None, None, False),
    ({"required": True, "default": False}, ["--flag"], None, None, True),
    ({"required": True, "default": False}, ["--no-flag"], None, None, False),
    ({"required": True, "default": "foo"}, ["--flag"], None, None, True),
    ({"required": True, "default": "foo"}, ["--no-flag"], None, None, False),
]

FLAG_VALUE_PROMPT_CASES = [
    ###
    ### Test cases with prompt=True explicitly enabled for the flag.
    ###
    # Prompt is allowed and the flag has no default, so it prompts.
    # But the flag_value is not set, so it defaults to a string.
    ({"prompt": True}, [], "", "", REPEAT),
    ({"prompt": True}, [], "", "y", "y"),
    ({"prompt": True}, [], "", "n", "n"),
    ({"prompt": True}, [], "", "foo", "foo"),
    # This time we provide a boolean flag_value, which makes the flag behave like a
    # boolean flag, and use the appropriate variation of [y/n].
    ({"prompt": True, "flag_value": True}, [], "[y/N]", "", False),
    ({"prompt": True, "flag_value": True}, [], "[y/N]", "y", True),
    ({"prompt": True, "flag_value": True}, [], "[y/N]", "n", False),
    ({"prompt": True, "flag_value": False}, [], "[y/N]", "", False),
    ({"prompt": True, "flag_value": False}, [], "[y/N]", "y", True),
    ({"prompt": True, "flag_value": False}, [], "[y/N]", "n", False),
    # Other flag values changes the auto-detection of the flag type.
    ({"prompt": True, "flag_value": None}, [], "", "", REPEAT),
    ({"prompt": True, "flag_value": None}, [], "", "y", "y"),
    ({"prompt": True, "flag_value": None}, [], "", "n", "n"),
    ({"prompt": True, "flag_value": "foo"}, [], "", "", REPEAT),
    ({"prompt": True, "flag_value": "foo"}, [], "", "y", "y"),
    ({"prompt": True, "flag_value": "foo"}, [], "", "n", "n"),
    ###
    ### Test cases with a flag_value and a default.
    ###
    # default=True
    ({"prompt": True, "default": True, "flag_value": True}, [], "[Y/n]", "", True),
    ({"prompt": True, "default": True, "flag_value": True}, [], "[Y/n]", "y", True),
    ({"prompt": True, "default": True, "flag_value": True}, [], "[Y/n]", "n", False),
    # For boolean flags, default=True is a literal value, not a sentinel meaning
    # "activate flag", so the prompt shows [Y/n] with default=True. See:
    # https://github.com/pallets/click/issues/3111
    # https://github.com/pallets/click/pull/3239
    ({"prompt": True, "default": True, "flag_value": False}, [], "[Y/n]", "", True),
    ({"prompt": True, "default": True, "flag_value": False}, [], "[Y/n]", "y", True),
    ({"prompt": True, "default": True, "flag_value": False}, [], "[Y/n]", "n", False),
    # default=False
    ({"prompt": True, "default": False, "flag_value": True}, [], "[y/N]", "", False),
    ({"prompt": True, "default": False, "flag_value": True}, [], "[y/N]", "y", True),
    ({"prompt": True, "default": False, "flag_value": True}, [], "[y/N]", "n", False),
    ({"prompt": True, "default": False, "flag_value": False}, [], "[y/N]", "", False),
    ({"prompt": True, "default": False, "flag_value": False}, [], "[y/N]", "y", True),
    ({"prompt": True, "default": False, "flag_value": False}, [], "[y/N]", "n", False),
    # default=None
    (
        {"prompt": True, "default": None, "flag_value": True},
        [],
        "[y/n]",
        "",
        INVALID,
    ),
    ({"prompt": True, "default": None, "flag_value": True}, [], "[y/n]", "y", True),
    ({"prompt": True, "default": None, "flag_value": True}, [], "[y/n]", "n", False),
    (
        {"prompt": True, "default": None, "flag_value": False},
        [],
        "[y/n]",
        "",
        INVALID,
    ),
    ({"prompt": True, "default": None, "flag_value": False}, [], "[y/n]", "y", True),
    ({"prompt": True, "default": None, "flag_value": False}, [], "[y/n]", "n", False),
    # If the flag_value is None, the flag behave like a string flag, whatever the
    # default is.
    ({"prompt": True, "default": True, "flag_value": None}, [], "", "", REPEAT),
    ({"prompt": True, "default": True, "flag_value": None}, [], "", "y", "y"),
    ({"prompt": True, "default": True, "flag_value": None}, [], "", "n", "n"),
    (
        {"prompt": True, "default": False, "flag_value": None},
        [],
        "[False]",
        "",
        "False",
    ),
    ({"prompt": True, "default": False, "flag_value": None}, [], "[False]", "y", "y"),
    ({"prompt": True, "default": False, "flag_value": None}, [], "[False]", "n", "n"),
    ({"prompt": True, "default": None, "flag_value": None}, [], "", "", REPEAT),
    ({"prompt": True, "default": None, "flag_value": None}, [], "", "y", "y"),
    ({"prompt": True, "default": None, "flag_value": None}, [], "", "n", "n"),
]


@pytest.mark.parametrize(
    ("opt_decls", "opt_params", "args", "prompt", "input", "expected"),
    # Boolean flag prompt cases.
    [("--flag/--no-flag", *case_params) for case_params in BOOLEAN_FLAG_PROMPT_CASES]
    # Non-boolean flag prompt cases.
    + [("--flag", *case_params) for case_params in FLAG_VALUE_PROMPT_CASES],
)
def test_flag_value_prompt(
    runner, opt_decls, opt_params, args, prompt, input, expected
):
    """Check how flag value are prompted and handled by all combinations of
    ``prompt``, ``default``, and ``flag_value`` parameters.

    Covers concerns raised in issue https://github.com/pallets/click/issues/1992.
    """

    @click.command()
    @click.option(opt_decls, **opt_params)
    def cli(flag):
        click.echo(repr(flag))

    invoke_options = {"standalone_mode": False}
    if input is not None:
        assert isinstance(input, str)
        invoke_options["input"] = f"{input}\n"

    result = runner.invoke(cli, args, **invoke_options)

    if expected in (MissingParameter, BadParameter):
        assert isinstance(result.exception, expected)
        assert not result.output
        assert result.exit_code == 1

    else:
        expected_output = ""
        if prompt is not None:
            # Build the expected prompt.
            assert isinstance(prompt, str)
            expected_prompt = f"Flag {prompt}: " if prompt else "Flag: "

            # Add the user input to the expected output.
            assert isinstance(input, str)
            expected_output += f"{expected_prompt}{input}\n"

            if expected is INVALID:
                expected_output += "Error: invalid input\n"

            # The prompt is expected to be repeated.
            if expected in (REPEAT, INVALID):
                expected_output += expected_prompt

        if expected not in (REPEAT, INVALID):
            expected_output += f"{expected!r}\n"

        assert result.output == expected_output
        assert not result.stderr
        assert result.exit_code == 0 if expected not in (REPEAT, INVALID) else 1


class _CustomTypeNoValue(click.ParamType):
    name = "custom"

    def convert(self, value, param, ctx):
        if len(value) < 4:
            self.fail("Password must be at least 4 characters", param, ctx)
        return value


class _CustomTypeWithRawValue(click.ParamType):
    name = "custom_raw"

    def convert(self, value, param, ctx):
        if value == "bad":
            self.fail(f"rejected: {value}", param, ctx)
        return value


class _PasswordLengthType(click.ParamType):
    """Mirrors the issue's original use case: a password validator
    that references the user-typed value in its error message without
    quoting it.
    """

    name = "password"

    def convert(self, value, param, ctx):
        if len(value) < 10:
            self.fail(f"{value} is too short", param, ctx)
        return value


class _MixedQuotedAndRawType(click.ParamType):
    """Custom type that mentions the user input both quoted (built-in
    pattern) and raw within the same message.
    """

    name = "mixed"

    def convert(self, value, param, ctx):
        self.fail(f"got {value!r} which is the same as {value}", param, ctx)


class _StaticMessageType(click.ParamType):
    """Custom type whose error message never references the value."""

    name = "static"

    def convert(self, value, param, ctx):
        self.fail("Authentication failed for this account", param, ctx)


class _RejectAllRawType(click.ParamType):
    """Always rejects, with the raw value (unquoted) in the message."""

    name = "reject_all_raw"

    def convert(self, value, param, ctx):
        self.fail(f"rejected: {value}", param, ctx)


class _MultiRawType(click.ParamType):
    """Mentions the raw value multiple times in the same message."""

    name = "multi_raw"

    def convert(self, value, param, ctx):
        self.fail(f"got {value} but {value} is bad", param, ctx)


class _MultiReprType(click.ParamType):
    """Mentions ``repr(value)`` multiple times in the same message."""

    name = "multi_repr"

    def convert(self, value, param, ctx):
        self.fail(f"got {value!r} and {value!r}", param, ctx)


class _ApostropheReprType(click.ParamType):
    """Custom type whose ``repr(value)`` switches to double quotes when
    the value itself contains a single quote.
    """

    name = "apostrophe_repr"

    def convert(self, value, param, ctx):
        self.fail(f"rejected {value!r}", param, ctx)


@pytest.mark.parametrize(
    ("type", "user_input", "expected_fragment", "unexpected_fragment"),
    [
        pytest.param(
            click.INT,
            "bad",
            "'***' is not a valid integer",
            "bad",
            id="builtin-int-masks-repr-value",
        ),
        pytest.param(
            _CustomTypeNoValue(),
            "bad",
            "Password must be at least 4 characters",
            None,
            id="custom-no-value-shows-message",
        ),
        pytest.param(
            _CustomTypeWithRawValue(),
            "bad",
            "rejected: '***'",
            "bad",
            id="custom-raw-value-masked",
        ),
        pytest.param(
            _PasswordLengthType(),
            "PASSWORD",
            "'***' is too short",
            "PASSWORD",
            id="unquoted-custom-message-should-mask-not-fallback",
        ),
        pytest.param(
            _MixedQuotedAndRawType(),
            "leakybits",
            "got '***' which is the same as '***'",
            "leakybits",
            id="mixed-quoted-and-raw-both-masked-at-source",
        ),
        pytest.param(
            click.IntRange(min=10, max=99),
            "1",
            "is not in the range",
            None,
            id="intrange-numeric-substring-falls-back-to-generic",
        ),
        pytest.param(
            _StaticMessageType(),
            "ent",
            "Authentication failed for this account",
            None,
            id="partial-word-match-falls-back-to-generic",
        ),
        # When the raw (unquoted) value appears in the message, mask it instead
        # of replacing the whole message with a generic fallback that throws
        # useful information away.
        pytest.param(
            _RejectAllRawType(),
            "secret",
            "rejected: '***'",
            "secret",
            id="raw-value-should-be-masked-not-fallback",
        ),
        # When the raw value occurs more than
        # once unquoted, every occurrence must be masked.
        pytest.param(
            _MultiRawType(),
            "secret",
            "got '***' but '***' is bad",
            "secret",
            id="multi-occurrence-raw-mask-all",
        ),
        pytest.param(
            _MultiReprType(),
            "secret",
            "got '***' and '***'",
            "secret",
            id="multi-occurrence-repr-mask-all",
        ),
        pytest.param(
            _PasswordLengthType(),
            "a.b*c+",
            "'***' is too short",
            "a.b*c+",
            id="regex-special-chars-must-be-escaped",
        ),
        pytest.param(
            _PasswordLengthType(),
            "пароль",
            "'***' is too short",
            "пароль",
            id="unicode-value-masked",
        ),
        pytest.param(
            _ApostropheReprType(),
            "it's",
            "rejected '***'",
            "it's",
            id="apostrophe-in-value-uses-double-quote-repr",
        ),
        pytest.param(
            _MixedQuotedAndRawType(),
            "leakybits",
            "got '***' which is the same as '***'",
            "leakybits",
            id="mixed-quoted-and-raw-mask-both",
        ),
    ],
)
def test_hide_input_error_message(
    runner, type, user_input, expected_fragment, unexpected_fragment
):
    """https://github.com/pallets/click/issues/2809"""

    @click.command()
    @click.option("--password", prompt=True, hide_input=True, type=type)
    def cli(password):
        click.echo(password)

    result = runner.invoke(cli, input=user_input)
    assert expected_fragment in result.output
    if unexpected_fragment is not None:
        assert unexpected_fragment not in result.output


def test_hide_input_confirmation_prompt_mismatch_unaffected(runner):
    """The ``hide_input`` mask logic only applies to ``value_proc``
    failures. The separate ``confirmation_prompt`` mismatch path must
    keep emitting its own message, with no value leak from either entry.
    """

    @click.command()
    @click.option("--password", prompt=True, confirmation_prompt=True, hide_input=True)
    def cli(password):
        click.echo(f"got: {password}")

    # First pair mismatches, second pair matches.
    result = runner.invoke(cli, input="firstone\nsecondone\nfinalone\nfinalone\n")
    assert "Error: The two entered values do not match." in result.output
    assert "firstone" not in result.output
    assert "secondone" not in result.output
    # Successful prompt echoes the final value back via the command body.
    assert "got: finalone" in result.output
    assert result.exit_code == 0


def test_hide_input_value_never_leaks_when_err_true(runner):
    """``click.prompt(..., err=True)`` routes its error message to
    stderr. The masking logic must apply on that path too: the raw
    input must not appear on either stream.
    """

    @click.command()
    def cli():
        value = click.prompt(
            "Password",
            hide_input=True,
            type=_PasswordLengthType(),
            err=True,
        )
        click.echo(value)

    result = runner.invoke(cli, input="leaky\n", mix_stderr=False)
    assert "leaky" not in result.stdout
    assert "leaky" not in result.stderr

```
---

## tests/test_testing.py

```python
import faulthandler
import io
import os
import pdb
import sys
from io import BytesIO

import pytest

import click
from click.exceptions import ClickException
from click.testing import CliRunner


def test_runner():
    @click.command()
    def test():
        i = click.get_binary_stream("stdin")
        o = click.get_binary_stream("stdout")
        while True:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner()
    result = runner.invoke(test, input="Hello World!\n")
    assert not result.exception
    assert result.output == "Hello World!\n"


def test_echo_stdin_stream():
    @click.command()
    def test():
        i = click.get_binary_stream("stdin")
        o = click.get_binary_stream("stdout")
        while True:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test, input="Hello World!\n")
    assert not result.exception
    assert result.output == "Hello World!\nHello World!\n"


def test_echo_stdin_prompts():
    @click.command()
    def test_python_input():
        foo = input("Foo: ")
        click.echo(f"foo={foo}")

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test_python_input, input="bar bar\n")
    assert not result.exception
    assert result.output == "Foo: bar bar\nfoo=bar bar\n"

    @click.command()
    @click.option("--foo", prompt=True)
    def test_prompt(foo):
        click.echo(f"foo={foo}")

    result = runner.invoke(test_prompt, input="bar bar\n")
    assert not result.exception
    assert result.output == "Foo: bar bar\nfoo=bar bar\n"

    @click.command()
    @click.option("--foo", prompt=True, hide_input=True)
    def test_hidden_prompt(foo):
        click.echo(f"foo={foo}")

    result = runner.invoke(test_hidden_prompt, input="bar bar\n")
    assert not result.exception
    assert result.output == "Foo: \nfoo=bar bar\n"

    @click.command()
    @click.option("--foo", prompt=True)
    @click.option("--bar", prompt=True)
    def test_multiple_prompts(foo, bar):
        click.echo(f"foo={foo}, bar={bar}")

    result = runner.invoke(test_multiple_prompts, input="one\ntwo\n")
    assert not result.exception
    assert result.output == "Foo: one\nBar: two\nfoo=one, bar=two\n"


def test_runner_with_stream():
    @click.command()
    def test():
        i = click.get_binary_stream("stdin")
        o = click.get_binary_stream("stdout")
        while True:
            chunk = i.read(4096)
            if not chunk:
                break
            o.write(chunk)
            o.flush()

    runner = CliRunner()
    result = runner.invoke(test, input=BytesIO(b"Hello World!\n"))
    assert not result.exception
    assert result.output == "Hello World!\n"

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(test, input=BytesIO(b"Hello World!\n"))
    assert not result.exception
    assert result.output == "Hello World!\nHello World!\n"


def test_prompts():
    @click.command()
    @click.option("--foo", prompt=True)
    def test(foo):
        click.echo(f"foo={foo}")

    runner = CliRunner()
    result = runner.invoke(test, input="wau wau\n")
    assert not result.exception
    assert result.output == "Foo: wau wau\nfoo=wau wau\n"

    @click.command()
    @click.option("--foo", prompt=True, hide_input=True)
    def test(foo):
        click.echo(f"foo={foo}")

    runner = CliRunner()
    result = runner.invoke(test, input="wau wau\n")
    assert not result.exception
    assert result.output == "Foo: \nfoo=wau wau\n"


def test_getchar():
    @click.command()
    def continue_it():
        click.echo(click.getchar())

    runner = CliRunner()
    result = runner.invoke(continue_it, input="y")
    assert not result.exception
    assert result.output == "y\n"

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(continue_it, input="y")
    assert not result.exception
    assert result.output == "y\n"

    @click.command()
    def getchar_echo():
        click.echo(click.getchar(echo=True))

    runner = CliRunner()
    result = runner.invoke(getchar_echo, input="y")
    assert not result.exception
    assert result.output == "yy\n"

    runner = CliRunner(echo_stdin=True)
    result = runner.invoke(getchar_echo, input="y")
    assert not result.exception
    assert result.output == "yy\n"


def test_catch_exceptions():
    class CustomError(Exception):
        pass

    @click.command()
    def cli():
        raise CustomError(1)

    runner = CliRunner()

    result = runner.invoke(cli)
    assert isinstance(result.exception, CustomError)
    assert type(result.exc_info) is tuple
    assert len(result.exc_info) == 3

    with pytest.raises(CustomError):
        runner.invoke(cli, catch_exceptions=False)

    CustomError = SystemExit

    result = runner.invoke(cli)
    assert result.exit_code == 1


def test_catch_exceptions_cli_runner():
    """Test that invoke `catch_exceptions` takes the value from CliRunner if not set
    explicitly."""

    class CustomError(Exception):
        pass

    @click.command()
    def cli():
        raise CustomError(1)

    runner = CliRunner(catch_exceptions=False)

    result = runner.invoke(cli, catch_exceptions=True)
    assert isinstance(result.exception, CustomError)
    assert type(result.exc_info) is tuple
    assert len(result.exc_info) == 3

    with pytest.raises(CustomError):
        runner.invoke(cli)


def test_with_color():
    @click.command()
    def cli():
        click.secho("hello world", fg="blue")

    runner = CliRunner()

    result = runner.invoke(cli)
    assert result.output == "hello world\n"
    assert not result.exception

    result = runner.invoke(cli, color=True)
    assert result.output == f"{click.style('hello world', fg='blue')}\n"
    assert not result.exception


def test_with_color_errors():
    class CLIError(ClickException):
        def format_message(self) -> str:
            return click.style(self.message, fg="red")

    @click.command()
    def cli():
        raise CLIError("Red error")

    runner = CliRunner()

    result = runner.invoke(cli)
    assert result.output == "Error: Red error\n"
    assert result.exception

    result = runner.invoke(cli, color=True)
    assert result.output == f"Error: {click.style('Red error', fg='red')}\n"
    assert result.exception


def test_with_color_but_pause_not_blocking():
    @click.command()
    def cli():
        click.pause()

    runner = CliRunner()
    result = runner.invoke(cli, color=True)
    assert not result.exception
    assert result.output == ""


def test_exit_code_and_output_from_sys_exit():
    # See issue #362
    @click.command()
    def cli_string():
        click.echo("hello world")
        sys.exit("error")

    @click.command()
    @click.pass_context
    def cli_string_ctx_exit(ctx):
        click.echo("hello world")
        ctx.exit("error")

    @click.command()
    def cli_int():
        click.echo("hello world")
        sys.exit(1)

    @click.command()
    @click.pass_context
    def cli_int_ctx_exit(ctx):
        click.echo("hello world")
        ctx.exit(1)

    @click.command()
    def cli_float():
        click.echo("hello world")
        sys.exit(1.0)

    @click.command()
    @click.pass_context
    def cli_float_ctx_exit(ctx):
        click.echo("hello world")
        ctx.exit(1.0)

    @click.command()
    def cli_no_error():
        click.echo("hello world")

    runner = CliRunner()

    result = runner.invoke(cli_string)
    assert result.exit_code == 1
    assert result.output == "hello world\nerror\n"

    result = runner.invoke(cli_string_ctx_exit)
    assert result.exit_code == 1
    assert result.output == "hello world\nerror\n"

    result = runner.invoke(cli_int)
    assert result.exit_code == 1
    assert result.output == "hello world\n"

    result = runner.invoke(cli_int_ctx_exit)
    assert result.exit_code == 1
    assert result.output == "hello world\n"

    result = runner.invoke(cli_float)
    assert result.exit_code == 1
    assert result.output == "hello world\n1.0\n"

    result = runner.invoke(cli_float_ctx_exit)
    assert result.exit_code == 1
    assert result.output == "hello world\n1.0\n"

    result = runner.invoke(cli_no_error)
    assert result.exit_code == 0
    assert result.output == "hello world\n"


def test_env():
    @click.command()
    def cli_env():
        click.echo(f"ENV={os.environ['TEST_CLICK_ENV']}")

    runner = CliRunner()

    env_orig = dict(os.environ)
    env = dict(env_orig)
    assert "TEST_CLICK_ENV" not in env
    env["TEST_CLICK_ENV"] = "some_value"
    result = runner.invoke(cli_env, env=env)
    assert result.exit_code == 0
    assert result.output == "ENV=some_value\n"

    assert os.environ == env_orig


def test_stderr():
    @click.command()
    def cli_stderr():
        click.echo("1 - stdout")
        click.echo("2 - stderr", err=True)
        click.echo("3 - stdout")
        click.echo("4 - stderr", err=True)

    runner_mix = CliRunner()
    result_mix = runner_mix.invoke(cli_stderr)

    assert result_mix.output == "1 - stdout\n2 - stderr\n3 - stdout\n4 - stderr\n"
    assert result_mix.stdout == "1 - stdout\n3 - stdout\n"
    assert result_mix.stderr == "2 - stderr\n4 - stderr\n"

    @click.command()
    def cli_empty_stderr():
        click.echo("stdout")

    runner = CliRunner()
    result = runner.invoke(cli_empty_stderr)

    assert result.output == "stdout\n"
    assert result.stdout == "stdout\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "args, expected_output",
    [
        (None, "bar\n"),
        ([], "bar\n"),
        ("", "bar\n"),
        (["--foo", "one two"], "one two\n"),
        ('--foo "one two"', "one two\n"),
    ],
)
def test_args(args, expected_output):
    @click.command()
    @click.option("--foo", default="bar")
    def cli_args(foo):
        click.echo(foo)

    runner = CliRunner()
    result = runner.invoke(cli_args, args=args)
    assert result.exit_code == 0
    assert result.output == expected_output


def test_setting_prog_name_in_extra():
    @click.command()
    def cli():
        click.echo("ok")

    runner = CliRunner()
    result = runner.invoke(cli, prog_name="foobar")
    assert not result.exception
    assert result.output == "ok\n"


def test_command_standalone_mode_returns_value():
    @click.command()
    def cli():
        click.echo("ok")
        return "Hello, World!"

    runner = CliRunner()
    result = runner.invoke(cli, standalone_mode=False)
    assert result.output == "ok\n"
    assert result.return_value == "Hello, World!"
    assert result.exit_code == 0


def test_file_stdin_attrs(runner):
    @click.command()
    @click.argument("f", type=click.File())
    def cli(f):
        click.echo(f.name)
        click.echo(f.mode, nl=False)

    result = runner.invoke(cli, ["-"])
    assert result.output == "<stdin>\nr"


def test_isolated_runner(runner):
    with runner.isolated_filesystem() as d:
        assert os.path.exists(d)

    assert not os.path.exists(d)


def test_isolated_runner_custom_tempdir(runner, tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path) as d:
        assert os.path.exists(d)

    assert os.path.exists(d)
    os.rmdir(d)


def test_isolation_stderr_errors():
    """Writing to stderr should escape invalid characters instead of
    raising a UnicodeEncodeError.
    """
    runner = CliRunner()

    with runner.isolation() as (_, err, _):
        click.echo("\udce2", err=True, nl=False)
        assert err.getvalue() == b"\\udce2"


def test_isolation_flushes_unflushed_stderr():
    """An un-flushed write to stderr, as with `print(..., file=sys.stderr)`, will end up
    flushed by the runner at end of invocation.
    """
    runner = CliRunner()

    with runner.isolation() as (_, err, _):
        click.echo("\udce2", err=True, nl=False)
        assert err.getvalue() == b"\\udce2"

    @click.command()
    def cli():
        # set end="", flush=False so that it's totally clear that we won't get any
        # auto-flush behaviors
        print("gyarados gyarados gyarados", file=sys.stderr, end="", flush=False)

    result = runner.invoke(cli)
    assert result.stderr == "gyarados gyarados gyarados"


def test_pdb_uses_real_streams():
    """``pdb.Pdb()`` inside ``CliRunner`` defaults to real terminal streams
    so that interactive debuggers work instead of reading from the
    captured ``BytesIO`` stdin.
    """

    @click.command()
    def cli():
        debugger = pdb.Pdb()
        assert debugger.stdin is sys.__stdin__
        assert debugger.stdout is sys.__stdout__
        click.echo("after debugger")

    runner = CliRunner()
    result = runner.invoke(cli, catch_exceptions=False)
    assert result.output == "after debugger\n"


def test_pdb_explicit_streams_honored():
    """Explicit ``stdin``/``stdout`` arguments to ``pdb.Pdb()`` are not
    overridden by the ``CliRunner`` patch.
    """

    @click.command()
    def cli():
        custom_in = sys.stdin
        custom_out = sys.stdout
        debugger = pdb.Pdb(stdin=custom_in, stdout=custom_out)
        assert debugger.stdin is custom_in
        assert debugger.stdout is custom_out

    runner = CliRunner()
    runner.invoke(cli, catch_exceptions=False)


def test_pdb_init_restored_after_invoke():
    """``pdb.Pdb.__init__`` is restored to its original after invoke."""
    original = pdb.Pdb.__init__

    @click.command()
    def cli():
        pass

    runner = CliRunner()
    runner.invoke(cli)

    assert pdb.Pdb.__init__ is original


needs_fd_capture = pytest.mark.skipif(
    sys.platform == "win32",
    reason="fd capture not supported on Windows",
)


def test_capture_invalid_mode():
    """Invalid capture mode raises ValueError."""
    with pytest.raises(ValueError, match="capture"):
        CliRunner(capture="invalid")  # type: ignore[arg-type]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only test")
def test_capture_fd_windows_error():
    """fd capture raises ValueError on Windows."""
    with pytest.raises(ValueError, match="not supported on Windows"):
        CliRunner(capture="fd")


@needs_fd_capture
def test_capture_fd_os_write():
    """capture='fd' captures writes to fd 1/2 that bypass sys.stdout."""

    @click.command()
    def cli():
        click.echo("python stdout")
        os.write(1, b"fd stdout\n")
        os.write(2, b"fd stderr\n")

    runner = CliRunner(capture="fd")
    result = runner.invoke(cli)
    assert "python stdout" in result.stdout
    assert "fd stdout" in result.stdout
    assert "fd stderr" in result.stderr


@needs_fd_capture
def test_capture_fd_stale_reference():
    """capture='fd' captures writes from stale stdout references (issue #2874).

    Simulates ``from sys import stdout`` at import time, which grabs
    the real stdout connected to fd 1.  The stale object's underlying
    FileIO uses fd 1, so redirecting fd 1 captures its writes.
    """
    # open(1, ..., closefd=False) creates a writer whose underlying
    # FileIO uses fd 1 directly. This mirrors the real scenario:
    # the original sys.stdout is a TextIOWrapper -> BufferedWriter ->
    # FileIO(fd=1).
    stale_stdout = open(1, "w", closefd=False)  # noqa: SIM115

    @click.command()
    def cli():
        stale_stdout.write("stale write\n")
        stale_stdout.flush()
        click.echo("normal write")

    runner = CliRunner(capture="fd")
    result = runner.invoke(cli)
    assert "normal write" in result.stdout
    assert "stale write" in result.stdout


@needs_fd_capture
def test_capture_fd_logging_handler(tmp_path):
    """capture='fd' captures logging output from a handler holding a stale
    stderr reference (issue #2827).

    stdlib logging.StreamHandler grabs sys.stderr at configuration time.
    Under normal CliRunner (sys-level capture), the handler still writes
    to the original stream object and output is lost. fd-level capture
    redirects the underlying file descriptor, so the writes are captured.
    """
    import logging

    # Create a writer backed by the real fd 2, simulating a handler
    # configured at import time before pytest or CliRunner replaced
    # sys.stderr. open(2, closefd=False) mirrors the real scenario:
    # the original sys.stderr is a TextIOWrapper -> BufferedWriter ->
    # FileIO(fd=2).
    stale_stderr = open(2, "w", closefd=False)  # noqa: SIM115
    handler = logging.StreamHandler(stale_stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger(f"click_test_{tmp_path.name}")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    @click.command()
    def cli():
        logger.info("log from stale handler")
        click.echo("normal echo")

    # sys-level capture misses the log line (it bypasses sys.stderr).
    runner_sys = CliRunner(capture="sys")
    result_sys = runner_sys.invoke(cli)
    assert "normal echo" in result_sys.output
    assert "log from stale handler" not in result_sys.output

    # fd-level capture catches it by redirecting fd 2.
    runner_fd = CliRunner(capture="fd")
    result_fd = runner_fd.invoke(cli)
    assert "normal echo" in result_fd.output
    assert "log from stale handler" in result_fd.output

    logger.removeHandler(handler)


@needs_fd_capture
def test_capture_fd_faulthandler():
    """faulthandler.enable() works with capture='fd' (issue #2865)."""

    @click.command()
    def cli():
        faulthandler.enable()
        click.echo("after faulthandler")

    runner = CliRunner(capture="fd")
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "after faulthandler" in result.output


def test_capture_sys_fileno_raises():
    """capture='sys' leaves fileno() raising UnsupportedOperation, so user
    code that does ``os.dup2(w, sys.stdout.fileno())`` cannot mutate the host
    runner's stdout (issue #3384).
    """

    @click.command()
    def cli():
        with pytest.raises(io.UnsupportedOperation):
            sys.stdout.fileno()
        with pytest.raises(io.UnsupportedOperation):
            sys.stderr.fileno()
        click.echo("ok")

    runner = CliRunner(capture="sys")
    result = runner.invoke(cli)
    assert result.exit_code == 0, result.output
    assert "ok" in result.stdout


@needs_fd_capture
def test_capture_fd_stderr_separation():
    """capture='fd' properly separates fd-level stdout and stderr."""

    @click.command()
    def cli():
        click.echo("py-out")
        click.echo("py-err", err=True)
        os.write(1, b"fd-out\n")
        os.write(2, b"fd-err\n")

    runner = CliRunner(capture="fd")
    result = runner.invoke(cli)
    assert "py-out" in result.stdout
    assert "fd-out" in result.stdout
    assert "py-err" in result.stderr
    assert "fd-err" in result.stderr
    # Mixed output has all of them
    assert "py-out" in result.output
    assert "py-err" in result.output
    assert "fd-out" in result.output
    assert "fd-err" in result.output


@needs_fd_capture
def test_capture_fd_nesting():
    """Nested CliRunner.invoke() with fd capture works correctly."""

    @click.command("inner")
    def inner_cli():
        click.echo("inner")

    @click.command("outer")
    def outer_cli():
        click.echo("outer")
        os.write(1, b"outer fd\n")
        inner_runner = CliRunner(capture="fd")
        inner_result = inner_runner.invoke(inner_cli)
        click.echo(f"inner captured: {inner_result.stdout.strip()}")

    runner = CliRunner(capture="fd")
    result = runner.invoke(outer_cli)
    assert "outer" in result.stdout
    assert "outer fd" in result.stdout
    assert "inner captured: inner" in result.stdout


@needs_fd_capture
@pytest.mark.parametrize("runner_capture", ["sys", "fd"])
@pytest.mark.parametrize("pytest_fixture", ["capsys", "capfd"])
def test_capture_pytest_matrix(
    request: pytest.FixtureRequest,
    runner_capture: str,
    pytest_fixture: str,
) -> None:
    """Matrix of ``CliRunner`` capture modes and Pytest capture fixtures."""
    pytest_cap = request.getfixturevalue(pytest_fixture)

    @click.command()
    def cli() -> None:
        click.echo("inside-stdout")
        click.echo("inside-stderr", err=True)

    runner = CliRunner(capture=runner_capture)
    result = runner.invoke(cli)

    # CliRunner sees Click's output.
    assert result.exit_code == 0
    assert "inside-stdout" in result.stdout
    assert "inside-stderr" in result.stderr

    # Pytest capture machinery is still working after invoke().
    print("post-invoke-stdout")
    print("post-invoke-stderr", file=sys.stderr)
    captured = pytest_cap.readouterr()
    assert "post-invoke-stdout" in captured.out
    assert "post-invoke-stderr" in captured.err

    # Click output is not leaking into Pytest.
    assert "inside-stdout" not in captured.out
    assert "inside-stderr" not in captured.err

```
---

## tests/test_types.py

```python
import os.path
import pathlib
import platform
import tempfile

import pytest

import click
from click import FileError


@pytest.mark.parametrize(
    ("type", "value", "expect"),
    [
        (click.IntRange(0, 5), "3", 3),
        (click.IntRange(5), "5", 5),
        (click.IntRange(5), "100", 100),
        (click.IntRange(max=5), "5", 5),
        (click.IntRange(max=5), "-100", -100),
        (click.IntRange(0, clamp=True), "-1", 0),
        (click.IntRange(max=5, clamp=True), "6", 5),
        (click.IntRange(0, min_open=True, clamp=True), "0", 1),
        (click.IntRange(max=5, max_open=True, clamp=True), "5", 4),
        (click.FloatRange(0.5, 1.5), "1.2", 1.2),
        (click.FloatRange(0.5, min_open=True), "0.51", 0.51),
        (click.FloatRange(max=1.5, max_open=True), "1.49", 1.49),
        (click.FloatRange(0.5, clamp=True), "-0.0", 0.5),
        (click.FloatRange(max=1.5, clamp=True), "inf", 1.5),
    ],
)
def test_range(type, value, expect):
    assert type.convert(value, None, None) == expect


@pytest.mark.parametrize(
    ("type", "value", "expect"),
    [
        (click.IntRange(0, 5), "6", "6 is not in the range 0<=x<=5."),
        (click.IntRange(5), "4", "4 is not in the range x>=5."),
        (click.IntRange(max=5), "6", "6 is not in the range x<=5."),
        (click.IntRange(0, 5, min_open=True), 0, "0<x<=5"),
        (click.IntRange(0, 5, max_open=True), 5, "0<=x<5"),
        (click.FloatRange(0.5, min_open=True), 0.5, "x>0.5"),
        (click.FloatRange(max=1.5, max_open=True), 1.5, "x<1.5"),
    ],
)
def test_range_fail(type, value, expect):
    with pytest.raises(click.BadParameter) as exc_info:
        type.convert(value, None, None)

    assert expect in exc_info.value.message


@pytest.mark.parametrize(
    ("error_message", "expected"),
    [
        ("bad value: nope", "bad value: nope"),
        ("", "nope"),
    ],
)
def test_func_param_type_uses_value_error_message(error_message, expected):
    def parse(value):
        raise ValueError(error_message if error_message else "")

    func_type = click.types.FuncParamType(parse)

    with pytest.raises(click.BadParameter) as exc_info:
        func_type.convert("nope", None, None)

    assert expected in exc_info.value.message


def test_float_range_no_clamp_open():
    with pytest.raises(TypeError):
        click.FloatRange(0, 1, max_open=True, clamp=True)

    sneaky = click.FloatRange(0, 1, max_open=True)
    sneaky.clamp = True

    with pytest.raises(RuntimeError):
        sneaky.convert("1.5", None, None)


@pytest.mark.parametrize(
    ("nargs", "multiple", "default", "expect"),
    [
        (2, False, None, None),
        (2, False, (None, None), (None, None)),
        (None, True, None, ()),
        (None, True, (None, None), (None, None)),
        (2, True, None, ()),
        (2, True, [(None, None)], ((None, None),)),
        (-1, None, None, ()),
    ],
)
def test_cast_multi_default(runner, nargs, multiple, default, expect):
    if nargs == -1:
        param = click.Argument(["a"], nargs=nargs, default=default)
    else:
        param = click.Option(["-a"], nargs=nargs, multiple=multiple, default=default)

    cli = click.Command("cli", params=[param], callback=lambda a: a)
    result = runner.invoke(cli, standalone_mode=False)
    assert result.exception is None
    assert result.return_value == expect


@pytest.mark.parametrize(
    ("cls", "expect"),
    [
        (None, "a/b/c.txt"),
        (str, "a/b/c.txt"),
        (bytes, b"a/b/c.txt"),
        (pathlib.Path, pathlib.Path("a", "b", "c.txt")),
    ],
)
def test_path_type(runner, cls, expect):
    cli = click.Command(
        "cli",
        params=[click.Argument(["p"], type=click.Path(path_type=cls))],
        callback=lambda p: p,
    )
    result = runner.invoke(cli, ["a/b/c.txt"], standalone_mode=False)
    assert result.exception is None
    assert result.return_value == expect


def _symlinks_supported():
    with tempfile.TemporaryDirectory(prefix="click-pytest-") as tempdir:
        target = os.path.join(tempdir, "target")
        open(target, "w").close()
        link = os.path.join(tempdir, "link")

        try:
            os.symlink(target, link)
            return True
        except OSError:
            return False


@pytest.mark.skipif(
    not _symlinks_supported(), reason="The current OS or FS doesn't support symlinks."
)
def test_path_resolve_symlink(tmp_path, runner):
    test_file = tmp_path / "file"
    test_file_str = os.fspath(test_file)
    test_file.write_text("")

    path_type = click.Path(resolve_path=True)
    param = click.Argument(["a"], type=path_type)
    ctx = click.Context(click.Command("cli", params=[param]))

    test_dir = tmp_path / "dir"
    test_dir.mkdir()

    abs_link = test_dir / "abs"
    abs_link.symlink_to(test_file)
    abs_rv = path_type.convert(os.fspath(abs_link), param, ctx)
    assert abs_rv == test_file_str

    rel_link = test_dir / "rel"
    rel_link.symlink_to(pathlib.Path("..") / "file")
    rel_rv = path_type.convert(os.fspath(rel_link), param, ctx)
    assert rel_rv == test_file_str


def _non_utf8_filenames_supported():
    with tempfile.TemporaryDirectory(prefix="click-pytest-") as tempdir:
        try:
            f = open(os.path.join(tempdir, "\udcff"), "w")
        except OSError:
            return False

        f.close()
        return True


@pytest.mark.skipif(
    not _non_utf8_filenames_supported(),
    reason="The current OS or FS doesn't support non-UTF-8 filenames.",
)
def test_path_surrogates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    type = click.Path(exists=True)
    path = pathlib.Path("\udcff")

    with pytest.raises(click.BadParameter, match="'�' does not exist"):
        type.convert(path, None, None)

    type = click.Path(file_okay=False)
    path.touch()

    with pytest.raises(click.BadParameter, match="'�' is a file"):
        type.convert(path, None, None)

    path.unlink()
    type = click.Path(dir_okay=False)
    path.mkdir()

    with pytest.raises(click.BadParameter, match="'�' is a directory"):
        type.convert(path, None, None)

    path.rmdir()

    def no_access(*args, **kwargs):
        """Test environments may be running as root, so we have to fake the result of
        the access tests that use os.access
        """
        p = args[0]
        assert p == path, f"unexpected os.access call on file not under test: {p!r}"
        return False

    path.touch()
    type = click.Path(readable=True)

    with pytest.raises(click.BadParameter, match="'�' is not readable"):
        with monkeypatch.context() as m:
            m.setattr(os, "access", no_access)
            type.convert(path, None, None)

    type = click.Path(readable=False, writable=True)

    with pytest.raises(click.BadParameter, match="'�' is not writable"):
        with monkeypatch.context() as m:
            m.setattr(os, "access", no_access)
            type.convert(path, None, None)

    type = click.Path(readable=False, executable=True)

    with pytest.raises(click.BadParameter, match="'�' is not executable"):
        with monkeypatch.context() as m:
            m.setattr(os, "access", no_access)
            type.convert(path, None, None)

    path.unlink()


@pytest.mark.parametrize(
    "type",
    [
        click.File(mode="r"),
        click.File(mode="r", lazy=True),
    ],
)
def test_file_surrogates(type, tmp_path):
    path = tmp_path / "\udcff"

    # - common case: �': No such file or directory
    # - special case: Illegal byte sequence
    # The special case is seen with rootless Podman. The root cause is most
    # likely that the path is handled by a user-space program (FUSE).
    match = r"(�': No such file or directory|Illegal byte sequence)"
    with pytest.raises(click.BadParameter, match=match):
        type.convert(path, None, None)


def test_file_error_surrogates():
    message = FileError(filename="\udcff").format_message()
    assert message == "Could not open file '�': unknown error"


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Filepath syntax differences."
)
def test_invalid_path_with_esc_sequence():
    with pytest.raises(click.BadParameter) as exc_info:
        with tempfile.TemporaryDirectory(prefix="my\ndir") as tempdir:
            click.Path(dir_okay=False).convert(tempdir, None, None)

    assert "my\\ndir" in exc_info.value.message


def test_choice_get_invalid_choice_message():
    choice = click.Choice(["a", "b", "c"])
    message = choice.get_invalid_choice_message("d", ctx=None)
    assert message == "'d' is not one of 'a', 'b', 'c'."

```
---

## tests/test_utils.py

```python
import os
import pathlib
import stat
import subprocess
import sys
from collections import namedtuple
from contextlib import nullcontext
from decimal import Decimal
from fractions import Fraction
from functools import partial
from io import StringIO
from unittest.mock import patch

import pytest

import click._termui_impl
import click.utils
from click._compat import MAC
from click._compat import WIN
from click._utils import UNSET


def test_unset_sentinel():
    value = UNSET

    assert value
    assert value is UNSET
    assert value == UNSET
    assert repr(value) == "Sentinel.UNSET"
    assert str(value) == "Sentinel.UNSET"
    assert bool(value) is True

    # Try all native Python values that can be falsy or truthy.
    # See: https://docs.python.org/3/library/stdtypes.html#truth-value-testing
    real_values = (
        None,
        True,
        False,
        0,
        1,
        0.0,
        1.0,
        0j,
        1j,
        Decimal(0),
        Decimal(1),
        Fraction(0, 1),
        Fraction(1, 1),
        "",
        "a",
        "UNSET",
        "Sentinel.UNSET",
        [1],
        (1),
        {1: "a"},
        set(),
        set([1]),
        frozenset(),
        frozenset([1]),
        range(0),
        range(1),
    )

    for real_value in real_values:
        assert value != real_value
        assert value is not real_value

    assert value not in real_values


def test_echo(runner):
    with runner.isolation() as outstreams:
        click.echo("\N{SNOWMAN}")
        click.echo(b"\x44\x44")
        click.echo(42, nl=False)
        click.echo(b"a", nl=False)
        click.echo("\x1b[31mx\x1b[39m", nl=False)
        bytes = outstreams[0].getvalue().replace(b"\r\n", b"\n")
        assert bytes == b"\xe2\x98\x83\nDD\n42ax"

    # if wrapped, we expect bytes to survive.
    @click.command()
    def cli():
        click.echo(b"\xf6")

    result = runner.invoke(cli, [])
    assert result.stdout_bytes == b"\xf6\n"

    # Ensure we do not strip for bytes.
    with runner.isolation() as outstreams:
        click.echo(bytearray(b"\x1b[31mx\x1b[39m"), nl=False)
        assert outstreams[0].getvalue() == b"\x1b[31mx\x1b[39m"


def test_echo_custom_file():
    f = StringIO()
    click.echo("hello", file=f)
    assert f.getvalue() == "hello\n"


def test_echo_no_streams(monkeypatch, runner):
    """echo should not fail when stdout and stderr are None with pythonw on Windows."""
    with runner.isolation():
        sys.stdout = None
        sys.stderr = None
        click.echo("test")
        click.echo("test", err=True)


@pytest.mark.parametrize(
    ("styles", "ref"),
    [
        ({"fg": "black"}, "\x1b[30mx y\x1b[0m"),
        ({"fg": "red"}, "\x1b[31mx y\x1b[0m"),
        ({"fg": "green"}, "\x1b[32mx y\x1b[0m"),
        ({"fg": "yellow"}, "\x1b[33mx y\x1b[0m"),
        ({"fg": "blue"}, "\x1b[34mx y\x1b[0m"),
        ({"fg": "magenta"}, "\x1b[35mx y\x1b[0m"),
        ({"fg": "cyan"}, "\x1b[36mx y\x1b[0m"),
        ({"fg": "white"}, "\x1b[37mx y\x1b[0m"),
        ({"bg": "black"}, "\x1b[40mx y\x1b[0m"),
        ({"bg": "red"}, "\x1b[41mx y\x1b[0m"),
        ({"bg": "green"}, "\x1b[42mx y\x1b[0m"),
        ({"bg": "yellow"}, "\x1b[43mx y\x1b[0m"),
        ({"bg": "blue"}, "\x1b[44mx y\x1b[0m"),
        ({"bg": "magenta"}, "\x1b[45mx y\x1b[0m"),
        ({"bg": "cyan"}, "\x1b[46mx y\x1b[0m"),
        ({"bg": "white"}, "\x1b[47mx y\x1b[0m"),
        ({"bg": 91}, "\x1b[48;5;91mx y\x1b[0m"),
        ({"bg": (135, 0, 175)}, "\x1b[48;2;135;0;175mx y\x1b[0m"),
        ({"bold": True}, "\x1b[1mx y\x1b[0m"),
        ({"dim": True}, "\x1b[2mx y\x1b[0m"),
        ({"underline": True}, "\x1b[4mx y\x1b[0m"),
        ({"overline": True}, "\x1b[53mx y\x1b[0m"),
        ({"italic": True}, "\x1b[3mx y\x1b[0m"),
        ({"blink": True}, "\x1b[5mx y\x1b[0m"),
        ({"reverse": True}, "\x1b[7mx y\x1b[0m"),
        ({"strikethrough": True}, "\x1b[9mx y\x1b[0m"),
        ({"bold": False}, "\x1b[22mx y\x1b[0m"),
        ({"dim": False}, "\x1b[22mx y\x1b[0m"),
        ({"underline": False}, "\x1b[24mx y\x1b[0m"),
        ({"overline": False}, "\x1b[55mx y\x1b[0m"),
        ({"italic": False}, "\x1b[23mx y\x1b[0m"),
        ({"blink": False}, "\x1b[25mx y\x1b[0m"),
        ({"reverse": False}, "\x1b[27mx y\x1b[0m"),
        ({"strikethrough": False}, "\x1b[29mx y\x1b[0m"),
        ({"fg": "black", "reset": False}, "\x1b[30mx y"),
    ],
)
def test_styling(styles, ref):
    assert click.style("x y", **styles) == ref
    assert click.unstyle(ref) == "x y"


@pytest.mark.parametrize(("text", "expect"), [("\x1b[?25lx y\x1b[?25h", "x y")])
def test_unstyle_other_ansi(text, expect):
    assert click.unstyle(text) == expect


def test_filename_formatting():
    assert click.format_filename(b"foo.txt") == "foo.txt"
    assert click.format_filename(b"/x/foo.txt") == "/x/foo.txt"
    assert click.format_filename("/x/foo.txt") == "/x/foo.txt"
    assert click.format_filename("/x/foo.txt", shorten=True) == "foo.txt"
    assert click.format_filename("/x/\ufffd.txt", shorten=True) == "�.txt"


def test_prompts(runner):
    @click.command()
    def test():
        if click.confirm("Foo"):
            click.echo("yes!")
        else:
            click.echo("no :(")

    result = runner.invoke(test, input="y\n")
    assert not result.exception
    assert result.output == "Foo [y/N]: y\nyes!\n"

    result = runner.invoke(test, input="\n")
    assert not result.exception
    assert result.output == "Foo [y/N]: \nno :(\n"

    result = runner.invoke(test, input="n\n")
    assert not result.exception
    assert result.output == "Foo [y/N]: n\nno :(\n"

    @click.command()
    def test_no():
        if click.confirm("Foo", default=True):
            click.echo("yes!")
        else:
            click.echo("no :(")

    result = runner.invoke(test_no, input="y\n")
    assert not result.exception
    assert result.output == "Foo [Y/n]: y\nyes!\n"

    result = runner.invoke(test_no, input="\n")
    assert not result.exception
    assert result.output == "Foo [Y/n]: \nyes!\n"

    result = runner.invoke(test_no, input="n\n")
    assert not result.exception
    assert result.output == "Foo [Y/n]: n\nno :(\n"


def test_confirm_repeat(runner):
    cli = click.Command(
        "cli", params=[click.Option(["--a/--no-a"], default=None, prompt=True)]
    )
    result = runner.invoke(cli, input="\ny\n")
    assert result.output == "A [y/n]: \nError: invalid input\nA [y/n]: y\n"


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
def test_prompts_abort(monkeypatch, capsys):
    def f(_):
        raise KeyboardInterrupt()

    monkeypatch.setattr("click.termui.hidden_prompt_func", f)

    try:
        click.prompt("Password", hide_input=True)
    except click.Abort:
        click.echo("interrupted")

    out, err = capsys.readouterr()
    # On non-Windows, prompt is passed directly to getpass, not echoed separately
    assert out == "\ninterrupted\n"


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
@pytest.mark.parametrize(
    ("call", "expected_prompt"),
    [
        (lambda: click.prompt("Name"), "Name: "),
        (lambda: click.prompt("Pw", hide_input=True), "Pw: "),
        (lambda: click.prompt("IP", prompt_suffix="."), "IP."),
        (lambda: click.confirm("OK"), "OK [y/N]: "),
    ],
    ids=["prompt", "prompt-hidden", "prompt-custom-suffix", "confirm"],
)
def test_full_prompt_passed_to_readline(monkeypatch, call, expected_prompt):
    """On non-Windows, prompt and confirm pass the full prompt text to the
    underlying prompt function so readline handles editing correctly.

    https://github.com/pallets/click/issues/2968
    https://github.com/pallets/click/pull/2969
    """
    received = []

    def capture(text):
        received.append(text)
        return "y"

    monkeypatch.setattr("click.termui.visible_prompt_func", capture)
    monkeypatch.setattr("click.termui.hidden_prompt_func", capture)
    call()
    assert received == [expected_prompt]


def test_prompts_eof(runner):
    """If too few lines of input are given, prompt should exit, not hang."""

    @click.command
    def echo():
        for _ in range(3):
            click.echo(click.prompt("", type=int))

    # only provide two lines of input for three prompts
    result = runner.invoke(echo, input="1\n2\n")
    assert result.exit_code == 1


def _test_gen_func():
    yield "a"
    yield "b"
    yield "c"
    yield "abc"


def _test_gen_func_fails():
    yield "test"
    raise RuntimeError("This is a test.")


def _test_gen_func_echo(file=None):
    yield "test"
    click.echo("hello", file=file)
    yield "test"


def _test_simulate_keyboard_interrupt(file=None):
    yield "output_before_keyboard_interrupt"
    raise KeyboardInterrupt()


EchoViaPagerTest = namedtuple(
    "EchoViaPagerTest",
    (
        "description",
        "test_input",
        "expected_pager",
        "expected_stdout",
        "expected_stderr",
        "expected_error",
    ),
)


@pytest.mark.skipif(WIN, reason="Different behavior on windows.")
@pytest.mark.skipif(
    MAC and sys.version_info >= (3, 13) and sys._is_gil_enabled(),
    reason="Generator exception tests are flaky in Python 3.14t on macOS.",
)
@pytest.mark.parametrize(
    "pager_cmd", ["cat", "cat ", " cat ", "less", " less", " less "]
)
@pytest.mark.parametrize(
    "test",
    [
        # We need to pass a parameter function instead of a plain param
        # as pytest.mark.parametrize will reuse the parameters causing the
        # generators to be used up so they will not yield anymore
        EchoViaPagerTest(
            description="Plain string argument",
            test_input=lambda: "just text",
            expected_pager="just text\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Iterable argument",
            test_input=lambda: ["itera", "ble"],
            expected_pager="iterable\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Generator function argument",
            test_input=lambda: _test_gen_func,
            expected_pager="abcabc\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="String generator argument",
            test_input=lambda: _test_gen_func(),
            expected_pager="abcabc\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Number generator expression argument",
            test_input=lambda: (c for c in range(6)),
            expected_pager="012345\n",
            expected_stdout="",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Exception in generator function argument",
            test_input=lambda: _test_gen_func_fails,
            # Because generator throws early on, the pager did not have
            # a chance yet to write the file.
            expected_pager="",
            expected_stdout="",
            expected_stderr="",
            expected_error=RuntimeError,
        ),
        EchoViaPagerTest(
            description="Exception in generator argument",
            test_input=lambda: _test_gen_func_fails,
            # Because generator throws early on, the pager did not have a
            # chance yet to write the file.
            expected_pager="",
            expected_stdout="",
            expected_stderr="",
            expected_error=RuntimeError,
        ),
        EchoViaPagerTest(
            description="Keyboard interrupt should not terminate the pager",
            test_input=lambda: _test_simulate_keyboard_interrupt(),
            # Due to the keyboard interrupt during pager execution, click program
            # should abort, but the pager should stay open.
            # This allows users to cancel the program and search in the pager
            # output, before they decide to terminate the pager.
            expected_pager="output_before_keyboard_interrupt",
            expected_stdout="",
            expected_stderr="",
            expected_error=KeyboardInterrupt,
        ),
        EchoViaPagerTest(
            description="Writing to stdout during generator execution",
            test_input=lambda: _test_gen_func_echo(),
            expected_pager="testtest\n",
            expected_stdout="hello\n",
            expected_stderr="",
            expected_error=None,
        ),
        EchoViaPagerTest(
            description="Writing to stderr during generator execution",
            test_input=lambda: _test_gen_func_echo(file=sys.stderr),
            expected_pager="testtest\n",
            expected_stdout="",
            expected_stderr="hello\n",
            expected_error=None,
        ),
    ],
)
def test_echo_via_pager(monkeypatch, capfd, pager_cmd, test, tmp_path):
    monkeypatch.setitem(os.environ, "PAGER", pager_cmd)
    monkeypatch.setattr(click._termui_impl, "isatty", lambda x: True)

    test_input = test.test_input()
    expected_pager = test.expected_pager
    expected_stdout = test.expected_stdout
    expected_stderr = test.expected_stderr
    expected_error = test.expected_error

    check_raise = pytest.raises(expected_error) if expected_error else nullcontext()

    pager_out_tmp = tmp_path / "pager_out.txt"
    with pager_out_tmp.open("w") as f:
        force_subprocess_stdout = patch.object(
            subprocess,
            "Popen",
            partial(subprocess.Popen, stdout=f),
        )
        with force_subprocess_stdout:
            with check_raise:
                click.echo_via_pager(test_input)

    out, err = capfd.readouterr()

    pager = pager_out_tmp.read_text()

    assert pager == expected_pager, (
        f"Unexpected pager output in test case '{test.description}'"
    )
    assert out == expected_stdout, (
        f"Unexpected stdout in test case '{test.description}'"
    )
    assert err == expected_stderr, (
        f"Unexpected stderr in test case '{test.description}'"
    )


def test_echo_color_flag(monkeypatch, capfd):
    isatty = True
    monkeypatch.setattr(click._compat, "isatty", lambda x: isatty)

    text = "foo"
    styled_text = click.style(text, fg="red")
    assert styled_text == "\x1b[31mfoo\x1b[0m"

    click.echo(styled_text, color=False)
    out, err = capfd.readouterr()
    assert out == f"{text}\n"

    click.echo(styled_text, color=True)
    out, err = capfd.readouterr()
    assert out == f"{styled_text}\n"

    isatty = True
    click.echo(styled_text)
    out, err = capfd.readouterr()
    assert out == f"{styled_text}\n"

    isatty = False
    # Faking isatty() is not enough on Windows;
    # the implementation caches the colorama wrapped stream
    # so we have to use a new stream for each test
    stream = StringIO()
    click.echo(styled_text, file=stream)
    assert stream.getvalue() == f"{text}\n"

    stream = StringIO()
    click.echo(styled_text, file=stream, color=True)
    assert stream.getvalue() == f"{styled_text}\n"


def test_prompt_cast_default(capfd, monkeypatch):
    monkeypatch.setattr(sys, "stdin", StringIO("\n"))
    value = click.prompt("value", default="100", type=int)
    capfd.readouterr()
    assert isinstance(value, int)


@pytest.mark.skipif(WIN, reason="Test too complex to make work windows.")
def test_echo_writing_to_standard_error(capfd, monkeypatch):
    def emulate_input(text):
        """Emulate keyboard input."""
        monkeypatch.setattr(sys, "stdin", StringIO(text))

    click.echo("Echo to standard output")
    out, err = capfd.readouterr()
    assert out == "Echo to standard output\n"
    assert err == ""

    click.echo("Echo to standard error", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Echo to standard error\n"

    emulate_input("asdlkj\n")
    click.prompt("Prompt to stdin")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin: "
    assert err == ""

    emulate_input("asdlkj\n")
    click.prompt("Prompt to stdin with no suffix", prompt_suffix="")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin with no suffix"
    assert err == ""

    # On non-Windows the full prompt goes through redirect_stdout so
    # nothing leaks to stdout when err=True.
    # https://github.com/pallets/click/issues/2968
    emulate_input("asdlkj\n")
    click.prompt("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr: "

    # https://github.com/pallets/click/issues/3019
    emulate_input("asdlkj\n")
    click.prompt("Prompt to stderr with no suffix", prompt_suffix="", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr with no suffix"

    emulate_input("y\n")
    click.confirm("Prompt to stdin")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin [y/N]: "
    assert err == ""

    emulate_input("y\n")
    click.confirm("Prompt to stdin with no suffix", prompt_suffix="")
    out, err = capfd.readouterr()
    assert out == "Prompt to stdin with no suffix [y/N]"
    assert err == ""

    # https://github.com/pallets/click/issues/2968
    emulate_input("y\n")
    click.confirm("Prompt to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr [y/N]: "

    # https://github.com/pallets/click/issues/3019
    emulate_input("y\n")
    click.confirm("Prompt to stderr with no suffix", prompt_suffix="", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Prompt to stderr with no suffix [y/N]"

    monkeypatch.setattr(click.termui, "isatty", lambda x: True)
    monkeypatch.setattr(click.termui, "getchar", lambda: " ")

    click.pause("Pause to stdout")
    out, err = capfd.readouterr()
    assert out == "Pause to stdout\n"
    assert err == ""

    click.pause("Pause to stderr", err=True)
    out, err = capfd.readouterr()
    assert out == ""
    assert err == "Pause to stderr\n"


def test_echo_with_capsys(capsys):
    click.echo("Capture me.")
    out, err = capsys.readouterr()
    assert out == "Capture me.\n"


def test_open_file(runner):
    @click.command()
    @click.argument("filename")
    def cli(filename):
        with click.open_file(filename) as f:
            click.echo(f.read())

        click.echo("meep")

    with runner.isolated_filesystem():
        with open("hello.txt", "w") as f:
            f.write("Cool stuff")

        result = runner.invoke(cli, ["hello.txt"])
        assert result.exception is None
        assert result.output == "Cool stuff\nmeep\n"

        result = runner.invoke(cli, ["-"], input="foobar")
        assert result.exception is None
        assert result.output == "foobar\nmeep\n"


def test_open_file_pathlib_dash(runner):
    @click.command()
    @click.argument(
        "filename", type=click.Path(allow_dash=True, path_type=pathlib.Path)
    )
    def cli(filename):
        click.echo(str(type(filename)))

        with click.open_file(filename) as f:
            click.echo(f.read())

        result = runner.invoke(cli, ["-"], input="value")
        assert result.exception is None
        assert result.output == "pathlib.Path\nvalue\n"


def test_open_file_ignore_errors_stdin(runner):
    @click.command()
    @click.argument("filename")
    def cli(filename):
        with click.open_file(filename, errors="ignore") as f:
            click.echo(f.read())

    result = runner.invoke(cli, ["-"], input=os.urandom(16))
    assert result.exception is None


def test_open_file_respects_ignore(runner):
    with runner.isolated_filesystem():
        with open("test.txt", "w") as f:
            f.write("Hello world!")

        with click.open_file("test.txt", encoding="utf8", errors="ignore") as f:
            assert f.errors == "ignore"


def test_open_file_ignore_invalid_utf8(runner):
    with runner.isolated_filesystem():
        with open("test.txt", "wb") as f:
            f.write(b"\xe2\x28\xa1")

        with click.open_file("test.txt", encoding="utf8", errors="ignore") as f:
            f.read()


def test_open_file_ignore_no_encoding(runner):
    with runner.isolated_filesystem():
        with open("test.bin", "wb") as f:
            f.write(os.urandom(16))

        with click.open_file("test.bin", errors="ignore") as f:
            f.read()


@pytest.mark.skipif(WIN, reason="os.chmod() is not fully supported on Windows.")
@pytest.mark.parametrize("permissions", [0o400, 0o444, 0o600, 0o644])
def test_open_file_atomic_permissions_existing_file(runner, permissions):
    with runner.isolated_filesystem():
        with open("existing.txt", "w") as f:
            f.write("content")
        os.chmod("existing.txt", permissions)

        @click.command()
        @click.argument("filename")
        def cli(filename):
            click.open_file(filename, "w", atomic=True).close()

        result = runner.invoke(cli, ["existing.txt"])
        assert result.exception is None
        assert stat.S_IMODE(os.stat("existing.txt").st_mode) == permissions


@pytest.mark.skipif(WIN, reason="os.stat() is not fully supported on Windows.")
def test_open_file_atomic_permissions_new_file(runner):
    with runner.isolated_filesystem():

        @click.command()
        @click.argument("filename")
        def cli(filename):
            click.open_file(filename, "w", atomic=True).close()

        # Create a test file to get the expected permissions for new files
        # according to the current umask.
        with open("test.txt", "w"):
            pass
        permissions = stat.S_IMODE(os.stat("test.txt").st_mode)

        result = runner.invoke(cli, ["new.txt"])
        assert result.exception is None
        assert stat.S_IMODE(os.stat("new.txt").st_mode) == permissions


def test_iter_keepopenfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        for e_line, a_line in zip(expected, click.utils.KeepOpenFile(f), strict=False):
            assert e_line == a_line.strip()


def test_iter_lazyfile(tmpdir):
    expected = list(map(str, range(10)))
    p = tmpdir.mkdir("testdir").join("testfile")
    p.write("\n".join(expected))
    with p.open() as f:
        with click.utils.LazyFile(f.name) as lf:
            for e_line, a_line in zip(expected, lf, strict=False):
                assert e_line == a_line.strip()


class MockMain:
    __slots__ = "__package__"

    def __init__(self, package_name):
        self.__package__ = package_name


@pytest.mark.parametrize(
    ("path", "main", "expected"),
    [
        ("example.py", None, "example.py"),
        (str(pathlib.Path("/foo/bar/example.py")), None, "example.py"),
        ("example", None, "example"),
        (str(pathlib.Path("example/__main__.py")), "example", "python -m example"),
        (str(pathlib.Path("example/cli.py")), "example", "python -m example.cli"),
        (str(pathlib.Path("./example")), "", "example"),
    ],
)
def test_detect_program_name(path, main, expected):
    assert click.utils._detect_program_name(path, _main=MockMain(main)) == expected


def test_expand_args(monkeypatch):
    user = os.path.expanduser("~")
    assert user in click.utils._expand_args(["~"])
    monkeypatch.setenv("CLICK_TEST", "hello")
    assert "hello" in click.utils._expand_args(["$CLICK_TEST"])
    assert "pyproject.toml" in click.utils._expand_args(["*.toml"])
    assert os.path.join("tests", "conftest.py") in click.utils._expand_args(
        ["**/conftest.py"]
    )
    assert "*.not-found" in click.utils._expand_args(["*.not-found"])
    # a bad glob pattern, such as a pytest identifier, should return itself
    assert click.utils._expand_args(["test.py::test_bad"])[0] == "test.py::test_bad"


@pytest.mark.parametrize(
    ("value", "max_length", "expect"),
    [
        pytest.param("", 10, "", id="empty"),
        pytest.param("123 567 90", 10, "123 567 90", id="equal length, no dot"),
        pytest.param("123 567 9. aaaa bbb", 10, "123 567 9.", id="sentence < max"),
        pytest.param("123 567\n\n 9. aaaa bbb", 10, "123 567", id="paragraph < max"),
        pytest.param("123 567 90123.", 10, "123 567...", id="truncate"),
        pytest.param("123 5678 xxxxxx", 10, "123...", id="length includes suffix"),
        pytest.param(
            "token in ~/.netrc ciao ciao",
            20,
            "token in ~/.netrc...",
            id="ignore dot in word",
        ),
    ],
)
@pytest.mark.parametrize(
    "alter",
    [
        pytest.param(None, id=""),
        pytest.param(
            lambda text: "\n\b\n" + "  ".join(text.split(" ")) + "\n", id="no-wrap mark"
        ),
    ],
)
def test_make_default_short_help(value, max_length, alter, expect):
    assert len(expect) <= max_length

    if alter:
        value = alter(value)

    out = click.utils.make_default_short_help(value, max_length)
    assert out == expect

```
---

## tests/typing/typing_aliased_group.py

```python
"""Example from https://click.palletsprojects.com/en/stable/advanced/#command-aliases"""

from __future__ import annotations

from typing_extensions import assert_type

import click


class AliasedGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command, list[str]]:
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        assert cmd is not None
        return cmd.name, cmd, args


@click.command(cls=AliasedGroup)
def cli() -> None:
    pass


assert_type(cli, AliasedGroup)


@cli.command()
def push() -> None:
    pass


@cli.command()
def pop() -> None:
    pass

```
---

## tests/typing/typing_confirmation_option.py

```python
"""From https://click.palletsprojects.com/en/stable/options/#yes-parameters"""

from typing_extensions import assert_type

import click


@click.command()
@click.confirmation_option(prompt="Are you sure you want to drop the db?")
def dropdb() -> None:
    click.echo("Dropped all tables!")


assert_type(dropdb, click.Command)

```
---

## tests/typing/typing_group_kw_options.py

```python
from typing_extensions import assert_type

import click


@click.group(context_settings={})
def hello() -> None:
    pass


assert_type(hello, click.Group)

```
---

## tests/typing/typing_help_option.py

```python
from typing_extensions import assert_type

import click


@click.command()
@click.help_option("-h", "--help")
def hello() -> None:
    """Simple program that greets NAME for a total of COUNT times."""
    click.echo("Hello!")


assert_type(hello, click.Command)

```
---

## tests/typing/typing_options.py

```python
"""From https://click.palletsprojects.com/en/stable/quickstart/#adding-parameters"""

from typing_extensions import assert_type

import click


@click.command()
@click.option("--count", default=1, help="number of greetings")
@click.argument("name")
def hello(count: int, name: str) -> None:
    for _ in range(count):
        click.echo(f"Hello {name}!")


assert_type(hello, click.Command)

```
---

## tests/typing/typing_password_option.py

```python
import codecs

from typing_extensions import assert_type

import click


@click.command()
@click.password_option()
def encrypt(password: str) -> None:
    click.echo(f"encoded: to {codecs.encode(password, 'rot13')}")


assert_type(encrypt, click.Command)

```
---

## tests/typing/typing_progressbar.py

```python
from __future__ import annotations

from typing_extensions import assert_type

from click import progressbar
from click._termui_impl import ProgressBar


def test_length_is_int() -> None:
    with progressbar(length=5) as bar:
        assert_type(bar, ProgressBar[int])
        for i in bar:
            assert_type(i, int)


def it() -> tuple[str, ...]:
    return ("hello", "world")


def test_generic_on_iterable() -> None:
    with progressbar(it()) as bar:
        assert_type(bar, ProgressBar[str])
        for s in bar:
            assert_type(s, str)

```
---

## tests/typing/typing_simple_example.py

```python
"""The simple example from https://github.com/pallets/click#a-simple-example."""

from typing_extensions import assert_type

import click


@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
def hello(count: int, name: str) -> None:
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")


assert_type(hello, click.Command)

```
---

## tests/typing/typing_version_option.py

```python
"""
From https://click.palletsprojects.com/en/stable/options/#callbacks-and-eager-options.
"""

from typing_extensions import assert_type

import click


@click.command()
@click.version_option("0.1")
def hello() -> None:
    click.echo("Hello World!")


assert_type(hello, click.Command)

```
