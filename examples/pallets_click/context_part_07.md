# Repository Context Part 7/9

Generated for LLM prompt context.

## tests/test_basic.py

```python
from __future__ import annotations

import enum
import os
from itertools import chain

import pytest

import click
from click._utils import UNSET


def test_basic_functionality(runner):
    @click.command()
    def cli():
        """Hello World!"""
        click.echo("I EXECUTED")

    result = runner.invoke(cli, ["--help"])
    assert not result.exception
    assert "Hello World!" in result.output
    assert "Show this message and exit." in result.output
    assert result.exit_code == 0
    assert "I EXECUTED" not in result.output

    result = runner.invoke(cli, [])
    assert not result.exception
    assert "I EXECUTED" in result.output
    assert result.exit_code == 0


def test_repr():
    @click.command()
    def command():
        pass

    @click.group()
    def group():
        pass

    @group.command()
    def subcommand():
        pass

    assert repr(command) == "<Command command>"
    assert repr(group) == "<Group group>"
    assert repr(subcommand) == "<Command subcommand>"


def test_return_values():
    @click.command()
    def cli():
        return 42

    with cli.make_context("foo", []) as ctx:
        rv = cli.invoke(ctx)
        assert rv == 42


def test_basic_group(runner):
    @click.group()
    def cli():
        """This is the root."""
        click.echo("ROOT EXECUTED")

    @cli.command()
    def subcommand():
        """This is a subcommand."""
        click.echo("SUBCOMMAND EXECUTED")

    result = runner.invoke(cli, ["--help"])
    assert not result.exception
    assert "COMMAND [ARGS]..." in result.output
    assert "This is the root" in result.output
    assert "This is a subcommand." in result.output
    assert result.exit_code == 0
    assert "ROOT EXECUTED" not in result.output

    result = runner.invoke(cli, ["subcommand"])
    assert not result.exception
    assert result.exit_code == 0
    assert "ROOT EXECUTED" in result.output
    assert "SUBCOMMAND EXECUTED" in result.output


def test_group_commands_dict(runner):
    """A Group can be built with a dict of commands."""

    @click.command()
    def sub():
        click.echo("sub", nl=False)

    cli = click.Group(commands={"other": sub})
    result = runner.invoke(cli, ["other"])
    assert result.output == "sub"


def test_group_from_list(runner):
    """A Group can be built with a list of commands."""

    @click.command()
    def sub():
        click.echo("sub", nl=False)

    cli = click.Group(commands=[sub])
    result = runner.invoke(cli, ["sub"])
    assert result.output == "sub"


@pytest.mark.parametrize(
    ("args", "expect"),
    [
        ([], "S:[no value]"),
        (["--s=42"], "S:[42]"),
        (["--s"], "Error: Option '--s' requires an argument."),
        (["--s="], "S:[]"),
        (["--s=\N{SNOWMAN}"], "S:[\N{SNOWMAN}]"),
    ],
)
def test_string_option(runner, args, expect):
    @click.command()
    @click.option("--s", default="no value")
    def cli(s):
        click.echo(f"S:[{s}]")

    result = runner.invoke(cli, args)
    assert expect in result.output

    if expect.startswith("Error:"):
        assert result.exception is not None
    else:
        assert result.exception is None


@pytest.mark.parametrize(
    ("args", "expect"),
    [
        ([], "I:[84]"),
        (["--i=23"], "I:[46]"),
        (["--i=x"], "Error: Invalid value for '--i': 'x' is not a valid integer."),
    ],
)
def test_int_option(runner, args, expect):
    @click.command()
    @click.option("--i", default=42)
    def cli(i):
        click.echo(f"I:[{i * 2}]")

    result = runner.invoke(cli, args)
    assert expect in result.output

    if expect.startswith("Error:"):
        assert result.exception is not None
    else:
        assert result.exception is None


@pytest.mark.parametrize(
    ("args", "expect"),
    [
        ([], "U:[ba122011-349f-423b-873b-9d6a79c688ab]"),
        (
            ["--u=821592c1-c50e-4971-9cd6-e89dc6832f86"],
            "U:[821592c1-c50e-4971-9cd6-e89dc6832f86]",
        ),
        (["--u=x"], "Error: Invalid value for '--u': 'x' is not a valid UUID."),
    ],
)
def test_uuid_option(runner, args, expect):
    @click.command()
    @click.option(
        "--u", default="ba122011-349f-423b-873b-9d6a79c688ab", type=click.UUID
    )
    def cli(u):
        click.echo(f"U:[{u}]")

    result = runner.invoke(cli, args)
    assert expect in result.output

    if expect.startswith("Error:"):
        assert result.exception is not None
    else:
        assert result.exception is None


@pytest.mark.parametrize(
    ("args", "expect"),
    [
        ([], "F:[42.0]"),
        ("--f=23.5", "F:[23.5]"),
        ("--f=x", "Error: Invalid value for '--f': 'x' is not a valid float."),
    ],
)
def test_float_option(runner, args, expect):
    @click.command()
    @click.option("--f", default=42.0)
    def cli(f):
        click.echo(f"F:[{f}]")

    result = runner.invoke(cli, args)
    assert expect in result.output

    if expect.startswith("Error:"):
        assert result.exception is not None
    else:
        assert result.exception is None


@pytest.mark.parametrize(
    ("args", "default", "expect"),
    [
        (["--on"], True, True),
        (["--on"], False, True),
        (["--on"], None, True),
        (["--on"], UNSET, True),
        (["--off"], True, False),
        (["--off"], False, False),
        (["--off"], None, False),
        (["--off"], UNSET, False),
        ([], True, True),
        ([], False, False),
        ([], None, None),
        ([], UNSET, False),
    ],
)
def test_boolean_switch(runner, args, default, expect):
    @click.command()
    @click.option("--on/--off", default=default)
    def cli(on):
        return on

    result = runner.invoke(cli, args, standalone_mode=False)
    assert result.return_value is expect


@pytest.mark.parametrize(
    ("default", "args", "expect"),
    (
        (True, ["--f"], True),
        (True, [], True),
        (False, ["--f"], True),
        (False, [], False),
        # Boolean flags have a 3-states logic.
        # See: https://github.com/pallets/click/issues/3024#issue-3285556668
        (None, ["--f"], True),
        (None, [], None),
    ),
)
def test_boolean_flag(runner, default, args, expect):
    @click.command()
    @click.option("--f", is_flag=True, default=default)
    def cli(f):
        return f

    result = runner.invoke(cli, args, standalone_mode=False)
    assert result.return_value is expect


@pytest.mark.parametrize(
    ("value", "expect"),
    chain(
        ((x, "True") for x in ("1", "true", "t", "yes", "y", "on")),
        ((x, "False") for x in ("0", "false", "f", "no", "n", "off")),
    ),
)
def test_boolean_conversion(runner, value, expect):
    @click.command()
    @click.option("--flag", type=bool)
    def cli(flag):
        click.echo(flag, nl=False)

    result = runner.invoke(cli, ["--flag", value])
    assert result.output == expect

    result = runner.invoke(cli, ["--flag", value.title()])
    assert result.output == expect


@pytest.mark.parametrize(
    ("default", "args", "expected"),
    # These test cases are similar to the ones in
    # tests/test_options.py::test_default_dual_option_callback, so keep them in sync.
    (
        # Each option is returning its own flag_value, whatever the default is.
        (True, ["--upper"], "upper"),
        (True, ["--lower"], "lower"),
        (False, ["--upper"], "upper"),
        (False, ["--lower"], "lower"),
        (None, ["--upper"], "upper"),
        (None, ["--lower"], "lower"),
        (UNSET, ["--upper"], "upper"),
        (UNSET, ["--lower"], "lower"),
        # Check that the last option wins when both are specified.
        (True, ["--upper", "--lower"], "lower"),
        (True, ["--lower", "--upper"], "upper"),
        # Check that the default is returned as-is when no option is specified.
        ("upper", [], "upper"),
        ("lower", [], "lower"),
        ("uPPer", [], "uPPer"),
        ("lOwEr", [], "lOwEr"),
        (" ᕕ( ᐛ )ᕗ ", [], " ᕕ( ᐛ )ᕗ "),
        (None, [], None),
        # Default is normalized to None if it is UNSET.
        (UNSET, [], None),
        # Special case: if default=True and flag_value is set, the value returned is the
        # flag_value, not the True Python value itself.
        (True, [], "upper"),
        # Non-string defaults are process as strings by the default Parameter's type.
        (False, [], "False"),
        (42, [], "42"),
        (12.3, [], "12.3"),
    ),
)
def test_flag_value_dual_options(runner, default, args, expected):
    """Check how default is processed when options compete for the same variable name.

    Covers the regression reported in
    https://github.com/pallets/click/issues/3024#issuecomment-3146199461
    """

    @click.command()
    @click.option("--upper", "case", flag_value="upper", default=default)
    @click.option("--lower", "case", flag_value="lower")
    def cli(case):
        click.echo(repr(case), nl=False)

    result = runner.invoke(cli, args)
    assert result.output == repr(expected)


def test_file_option(runner):
    @click.command()
    @click.option("--file", type=click.File("w"))
    def input(file):
        file.write("Hello World!\n")

    @click.command()
    @click.option("--file", type=click.File("r"))
    def output(file):
        click.echo(file.read())

    with runner.isolated_filesystem():
        result_in = runner.invoke(input, ["--file=example.txt"])
        result_out = runner.invoke(output, ["--file=example.txt"])

    assert not result_in.exception
    assert result_in.output == ""
    assert not result_out.exception
    assert result_out.output == "Hello World!\n\n"


def test_file_lazy_mode(runner):
    do_io = False

    @click.command()
    @click.option("--file", type=click.File("w"))
    def input(file):
        if do_io:
            file.write("Hello World!\n")

    @click.command()
    @click.option("--file", type=click.File("r"))
    def output(file):
        pass

    with runner.isolated_filesystem():
        os.mkdir("example.txt")

        do_io = True
        result_in = runner.invoke(input, ["--file=example.txt"])
        assert result_in.exit_code == 1

        do_io = False
        result_in = runner.invoke(input, ["--file=example.txt"])
        assert result_in.exit_code == 0

        result_out = runner.invoke(output, ["--file=example.txt"])
        assert result_out.exception

    @click.command()
    @click.option("--file", type=click.File("w", lazy=False))
    def input_non_lazy(file):
        file.write("Hello World!\n")

    with runner.isolated_filesystem():
        os.mkdir("example.txt")
        result_in = runner.invoke(input_non_lazy, ["--file=example.txt"])
        assert result_in.exit_code == 2
        assert "Invalid value for '--file': 'example.txt'" in result_in.output


def test_path_option(runner):
    @click.command()
    @click.option("-O", type=click.Path(file_okay=False, exists=True, writable=True))
    def write_to_dir(o):
        with open(os.path.join(o, "foo.txt"), "wb") as f:
            f.write(b"meh\n")

    with runner.isolated_filesystem():
        os.mkdir("test")

        result = runner.invoke(write_to_dir, ["-O", "test"])
        assert not result.exception

        with open("test/foo.txt", "rb") as f:
            assert f.read() == b"meh\n"

        result = runner.invoke(write_to_dir, ["-O", "test/foo.txt"])
        assert "is a file" in result.output

    @click.command()
    @click.option("-f", type=click.Path(exists=True))
    def showtype(f):
        click.echo(f"is_file={os.path.isfile(f)}")
        click.echo(f"is_dir={os.path.isdir(f)}")

    with runner.isolated_filesystem():
        result = runner.invoke(showtype, ["-f", "xxx"])
        assert "does not exist" in result.output

        result = runner.invoke(showtype, ["-f", "."])
        assert "is_file=False" in result.output
        assert "is_dir=True" in result.output

    @click.command()
    @click.option("-f", type=click.Path())
    def exists(f):
        click.echo(f"exists={os.path.exists(f)}")

    with runner.isolated_filesystem():
        result = runner.invoke(exists, ["-f", "xxx"])
        assert "exists=False" in result.output

        result = runner.invoke(exists, ["-f", "."])
        assert "exists=True" in result.output


def test_choice_option(runner):
    @click.command()
    @click.option("--method", type=click.Choice(["foo", "bar", "baz"]))
    def cli(method):
        click.echo(method)

    result = runner.invoke(cli, ["--method=foo"])
    assert not result.exception
    assert result.output == "foo\n"

    result = runner.invoke(cli, ["--method=meh"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '--method': 'meh' is not one of 'foo', 'bar', 'baz'."
        in result.output
    )

    result = runner.invoke(cli, ["--help"])
    assert "--method [foo|bar|baz]" in result.output


def test_choice_argument(runner):
    @click.command()
    @click.argument("method", type=click.Choice(["foo", "bar", "baz"]))
    def cli(method):
        click.echo(method)

    result = runner.invoke(cli, ["foo"])
    assert not result.exception
    assert result.output == "foo\n"

    result = runner.invoke(cli, ["meh"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '{foo|bar|baz}': 'meh' is not one of 'foo',"
        " 'bar', 'baz'." in result.output
    )

    result = runner.invoke(cli, ["--help"])
    assert "{foo|bar|baz}" in result.output


def test_choice_argument_enum(runner):
    class MyEnum(str, enum.Enum):
        FOO = "foo-value"
        BAR = "bar-value"
        BAZ = "baz-value"

    @click.command()
    @click.argument("method", type=click.Choice(MyEnum, case_sensitive=False))
    def cli(method: MyEnum):
        assert isinstance(method, MyEnum)
        click.echo(method)

    result = runner.invoke(cli, ["foo"])
    assert result.output == "foo-value\n"
    assert not result.exception

    result = runner.invoke(cli, ["meh"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '{foo|bar|baz}': 'meh' is not one of 'foo',"
        " 'bar', 'baz'." in result.output
    )

    result = runner.invoke(cli, ["--help"])
    assert "{foo|bar|baz}" in result.output


def test_choice_argument_custom_type(runner):
    class MyClass:
        def __init__(self, value: str) -> None:
            self.value = value

        def __str__(self) -> str:
            return self.value

    @click.command()
    @click.argument(
        "method", type=click.Choice([MyClass("foo"), MyClass("bar"), MyClass("baz")])
    )
    def cli(method: MyClass):
        assert isinstance(method, MyClass)
        click.echo(method)

    result = runner.invoke(cli, ["foo"])
    assert not result.exception
    assert result.output == "foo\n"

    result = runner.invoke(cli, ["meh"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '{foo|bar|baz}': 'meh' is not one of 'foo',"
        " 'bar', 'baz'." in result.output
    )

    result = runner.invoke(cli, ["--help"])
    assert "{foo|bar|baz}" in result.output


def test_choice_argument_none(runner):
    @click.command()
    @click.argument(
        "method", type=click.Choice(["not-none", None], case_sensitive=False)
    )
    def cli(method: str | None):
        assert isinstance(method, str) or method is None
        click.echo(repr(method), nl=False)

    result = runner.invoke(cli, ["not-none"])
    assert not result.exception
    assert result.output == repr("not-none")

    result = runner.invoke(cli, ["none"])
    assert not result.exception
    assert result.output == repr(None)

    result = runner.invoke(cli, [])
    assert result.exception
    assert (
        "Error: Missing argument '{not-none|none}'. "
        "Choose from:\n\tnot-none,\n\tnone\n" in result.stderr
    )

    result = runner.invoke(cli, ["--help"])
    assert result.output.startswith("Usage: cli [OPTIONS] {not-none|none}\n")


def test_datetime_option_default(runner):
    @click.command()
    @click.option("--start_date", type=click.DateTime())
    def cli(start_date):
        click.echo(start_date.strftime("%Y-%m-%dT%H:%M:%S"))

    result = runner.invoke(cli, ["--start_date=2015-09-29"])
    assert not result.exception
    assert result.output == "2015-09-29T00:00:00\n"

    result = runner.invoke(cli, ["--start_date=2015-09-29T09:11:22"])
    assert not result.exception
    assert result.output == "2015-09-29T09:11:22\n"

    result = runner.invoke(cli, ["--start_date=2015-09"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '--start_date': '2015-09' does not match the formats"
        " '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'."
    ) in result.output

    result = runner.invoke(cli, ["--help"])
    assert (
        "--start_date [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]" in result.output
    )


def test_datetime_option_custom(runner):
    @click.command()
    @click.option("--start_date", type=click.DateTime(formats=["%A %B %d, %Y"]))
    def cli(start_date):
        click.echo(start_date.strftime("%Y-%m-%dT%H:%M:%S"))

    result = runner.invoke(cli, ["--start_date=Wednesday June 05, 2010"])
    assert not result.exception
    assert result.output == "2010-06-05T00:00:00\n"


def test_required_option(runner):
    @click.command()
    @click.option("--foo", required=True)
    def cli(foo):
        click.echo(foo)

    result = runner.invoke(cli, [])
    assert result.exit_code == 2
    assert "Missing option '--foo'" in result.output


def test_evaluation_order(runner):
    called = []

    def memo(ctx, param, value):
        called.append(value)
        return value

    @click.command()
    @click.option("--missing", default="missing", is_eager=False, callback=memo)
    @click.option("--eager-flag1", flag_value="eager1", is_eager=True, callback=memo)
    @click.option("--eager-flag2", flag_value="eager2", is_eager=True, callback=memo)
    @click.option("--eager-flag3", flag_value="eager3", is_eager=True, callback=memo)
    @click.option("--normal-flag1", flag_value="normal1", is_eager=False, callback=memo)
    @click.option("--normal-flag2", flag_value="normal2", is_eager=False, callback=memo)
    @click.option("--normal-flag3", flag_value="normal3", is_eager=False, callback=memo)
    def cli(**x):
        pass

    result = runner.invoke(
        cli,
        [
            "--eager-flag2",
            "--eager-flag1",
            "--normal-flag2",
            "--eager-flag3",
            "--normal-flag3",
            "--normal-flag3",
            "--normal-flag1",
            "--normal-flag1",
        ],
    )
    assert not result.exception
    assert called == [
        "eager2",
        "eager1",
        "eager3",
        "normal2",
        "normal3",
        "normal1",
        "missing",
    ]


def test_hidden_option(runner):
    @click.command()
    @click.option("--nope", hidden=True)
    def cli(nope):
        click.echo(nope)

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "--nope" not in result.output


def test_hidden_command(runner):
    @click.group()
    def cli():
        pass

    @cli.command(hidden=True)
    def nope():
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "nope" not in result.output


def test_hidden_group(runner):
    @click.group()
    def cli():
        pass

    @cli.group(hidden=True)
    def subgroup():
        pass

    @subgroup.command()
    def nope():
        pass

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "subgroup" not in result.output
    assert "nope" not in result.output


def test_summary_line(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    def cmd():
        """
        Summary line without period

        Here is a sentence. And here too.
        """
        pass

    result = runner.invoke(cli, ["--help"])
    assert "Summary line without period" in result.output
    assert "Here is a sentence." not in result.output


def test_help_invalid_default(runner):
    cli = click.Command(
        "cli",
        params=[
            click.Option(
                ["-a"],
                type=click.Path(exists=True),
                default="not found",
                show_default=True,
            ),
        ],
    )
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "default: not found" in result.output

```
---

## tests/test_chain.py

```python
import sys

import pytest

import click


def debug():
    click.echo(
        f"{sys._getframe(1).f_code.co_name}"
        f"={'|'.join(click.get_current_context().args)}"
    )


def test_basic_chaining(runner):
    @click.group(chain=True)
    def cli():
        pass

    @cli.command("sdist")
    def sdist():
        click.echo("sdist called")

    @cli.command("bdist")
    def bdist():
        click.echo("bdist called")

    result = runner.invoke(cli, ["bdist", "sdist", "bdist"])
    assert not result.exception
    assert result.output.splitlines() == [
        "bdist called",
        "sdist called",
        "bdist called",
    ]


@pytest.mark.parametrize(
    ("args", "expect"),
    [
        (["--help"], "COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]..."),
        (["--help"], "ROOT HELP"),
        (["sdist", "--help"], "SDIST HELP"),
        (["bdist", "--help"], "BDIST HELP"),
        (["bdist", "sdist", "--help"], "SDIST HELP"),
    ],
)
def test_chaining_help(runner, args, expect):
    @click.group(chain=True)
    def cli():
        """ROOT HELP"""
        pass

    @cli.command("sdist")
    def sdist():
        """SDIST HELP"""
        click.echo("sdist called")

    @cli.command("bdist")
    def bdist():
        """BDIST HELP"""
        click.echo("bdist called")

    result = runner.invoke(cli, args)
    assert not result.exception
    assert expect in result.output


def test_chaining_with_options(runner):
    @click.group(chain=True)
    def cli():
        pass

    @cli.command("sdist")
    @click.option("--format")
    def sdist(format):
        click.echo(f"sdist called {format}")

    @cli.command("bdist")
    @click.option("--format")
    def bdist(format):
        click.echo(f"bdist called {format}")

    result = runner.invoke(cli, ["bdist", "--format=1", "sdist", "--format=2"])
    assert not result.exception
    assert result.output.splitlines() == ["bdist called 1", "sdist called 2"]


@pytest.mark.parametrize(("chain", "expect"), [(False, "1"), (True, "[]")])
def test_no_command_result_callback(runner, chain, expect):
    """When a group has ``invoke_without_command=True``, the result
    callback is always invoked. A regular group invokes it with
    its return value, a chained group with ``[]``.
    """

    @click.group(invoke_without_command=True, chain=chain)
    def cli():
        return 1

    @cli.result_callback()
    def process_result(result):
        click.echo(result, nl=False)

    result = runner.invoke(cli, [])
    assert result.output == expect


def test_chaining_with_arguments(runner):
    @click.group(chain=True)
    def cli():
        pass

    @cli.command("sdist")
    @click.argument("format")
    def sdist(format):
        click.echo(f"sdist called {format}")

    @cli.command("bdist")
    @click.argument("format")
    def bdist(format):
        click.echo(f"bdist called {format}")

    result = runner.invoke(cli, ["bdist", "1", "sdist", "2"])
    assert not result.exception
    assert result.output.splitlines() == ["bdist called 1", "sdist called 2"]


@pytest.mark.parametrize(
    ("args", "input", "expect"),
    [
        (["-f", "-"], "foo\nbar", ["foo", "bar"]),
        (["-f", "-", "strip"], "foo \n bar", ["foo", "bar"]),
        (["-f", "-", "strip", "uppercase"], "foo \n bar", ["FOO", "BAR"]),
    ],
)
def test_pipeline(runner, args, input, expect):
    @click.group(chain=True, invoke_without_command=True)
    @click.option("-f", type=click.File("r"))
    def cli(f):
        pass

    @cli.result_callback()
    def process_pipeline(processors, f):
        iterator = (x.rstrip("\r\n") for x in f)
        for processor in processors:
            iterator = processor(iterator)
        for item in iterator:
            click.echo(item)

    @cli.command("uppercase")
    def make_uppercase():
        def processor(iterator):
            for line in iterator:
                yield line.upper()

        return processor

    @cli.command("strip")
    def make_strip():
        def processor(iterator):
            for line in iterator:
                yield line.strip()

        return processor

    result = runner.invoke(cli, args, input=input)
    assert not result.exception
    assert result.output.splitlines() == expect


def test_args_and_chain(runner):
    @click.group(chain=True)
    def cli():
        debug()

    @cli.command()
    def a():
        debug()

    @cli.command()
    def b():
        debug()

    @cli.command()
    def c():
        debug()

    result = runner.invoke(cli, ["a", "b", "c"])
    assert not result.exception
    assert result.output.splitlines() == ["cli=", "a=", "b=", "c="]


def test_group_arg_behavior(runner):
    with pytest.raises(RuntimeError):

        @click.group(chain=True)
        @click.argument("forbidden", required=False)
        def bad_cli():
            pass

    with pytest.raises(RuntimeError):

        @click.group(chain=True)
        @click.argument("forbidden", nargs=-1)
        def bad_cli2():
            pass

    @click.group(chain=True)
    @click.argument("arg")
    def cli(arg):
        click.echo(f"cli:{arg}")

    @cli.command()
    def a():
        click.echo("a")

    result = runner.invoke(cli, ["foo", "a"])
    assert not result.exception
    assert result.output.splitlines() == ["cli:foo", "a"]


@pytest.mark.xfail
def test_group_chaining(runner):
    @click.group(chain=True)
    def cli():
        debug()

    @cli.group()
    def l1a():
        debug()

    @l1a.command()
    def l2a():
        debug()

    @l1a.command()
    def l2b():
        debug()

    @cli.command()
    def l1b():
        debug()

    result = runner.invoke(cli, ["l1a", "l2a", "l1b"])
    assert not result.exception
    assert result.output.splitlines() == ["cli=", "l1a=", "l2a=", "l1b="]

```
---

## tests/test_command_decorators.py

```python
import pytest

import click


def test_command_no_parens(runner):
    @click.command
    def cli():
        click.echo("hello")

    result = runner.invoke(cli)
    assert result.exception is None
    assert result.output == "hello\n"


def test_custom_command_no_parens(runner):
    class CustomCommand(click.Command):
        pass

    class CustomGroup(click.Group):
        command_class = CustomCommand

    @click.group(cls=CustomGroup)
    def grp():
        pass

    @grp.command
    def cli():
        click.echo("hello custom command class")

    result = runner.invoke(cli)
    assert result.exception is None
    assert result.output == "hello custom command class\n"


def test_group_no_parens(runner):
    @click.group
    def grp():
        click.echo("grp1")

    @grp.command
    def cmd1():
        click.echo("cmd1")

    @grp.group
    def grp2():
        click.echo("grp2")

    @grp2.command
    def cmd2():
        click.echo("cmd2")

    result = runner.invoke(grp, ["cmd1"])
    assert result.exception is None
    assert result.output == "grp1\ncmd1\n"

    result = runner.invoke(grp, ["grp2", "cmd2"])
    assert result.exception is None
    assert result.output == "grp1\ngrp2\ncmd2\n"


def test_params_argument(runner):
    opt = click.Argument(["a"])

    @click.command(params=[opt])
    @click.argument("b")
    def cli(a, b):
        click.echo(f"{a} {b}")

    assert cli.params[0].name == "a"
    assert cli.params[1].name == "b"
    result = runner.invoke(cli, ["1", "2"])
    assert result.output == "1 2\n"


@pytest.mark.parametrize(
    "name",
    [
        "init_data",
        "init_data_command",
        "init_data_cmd",
        "init_data_group",
        "init_data_grp",
    ],
)
def test_generate_name(name: str) -> None:
    def f():
        pass

    f.__name__ = name
    f = click.command(f)
    assert f.name == "init-data"

```
---

## tests/test_commands.py

```python
import re

import pytest

import click


def test_other_command_invoke(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        return ctx.invoke(other_cmd, arg=42)

    @click.command()
    @click.argument("arg", type=click.INT)
    def other_cmd(arg):
        click.echo(arg)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "42\n"


def test_other_command_forward(runner):
    cli = click.Group()

    @cli.command()
    @click.option("--count", default=1)
    def test(count):
        click.echo(f"Count: {count:d}")

    @cli.command()
    @click.option("--count", default=1)
    @click.pass_context
    def dist(ctx, count):
        ctx.forward(test)
        ctx.invoke(test, count=42)

    result = runner.invoke(cli, ["dist"])
    assert not result.exception
    assert result.output == "Count: 1\nCount: 42\n"


def test_forwarded_params_consistency(runner):
    cli = click.Group()

    @cli.command()
    @click.option("-a")
    @click.pass_context
    def first(ctx, **kwargs):
        click.echo(f"{ctx.params}")

    @cli.command()
    @click.option("-a")
    @click.option("-b")
    @click.pass_context
    def second(ctx, **kwargs):
        click.echo(f"{ctx.params}")
        ctx.forward(first)

    result = runner.invoke(cli, ["second", "-a", "foo", "-b", "bar"])
    assert not result.exception
    assert result.output == "{'a': 'foo', 'b': 'bar'}\n{'a': 'foo', 'b': 'bar'}\n"


def test_auto_shorthelp(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    def short():
        """This is a short text."""

    @cli.command()
    def special_chars():
        """Login and store the token in ~/.netrc."""

    @cli.command()
    def long():
        """This is a long text that is too long to show as short help
        and will be truncated instead."""

    result = runner.invoke(cli, ["--help"])
    assert (
        re.search(
            r"Commands:\n\s+"
            r"long\s+This is a long text that is too long to show as short help"
            r"\.\.\.\n\s+"
            r"short\s+This is a short text\.\n\s+"
            r"special-chars\s+Login and store the token in ~/.netrc\.\s*",
            result.output,
        )
        is not None
    )


def test_command_no_args_is_help(runner):
    result = runner.invoke(click.Command("test", no_args_is_help=True))
    assert result.exit_code == 2
    assert "Show this message and exit." in result.output


def test_default_maps(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--name", default="normal")
    def foo(name):
        click.echo(name)

    result = runner.invoke(cli, ["foo"], default_map={"foo": {"name": "changed"}})

    assert not result.exception
    assert result.output == "changed\n"


@pytest.mark.parametrize(
    ("args", "exit_code", "expect"),
    [
        (["obj1"], 2, "Error: Missing command."),
        (["obj1", "--help"], 0, "Show this message and exit."),
        (["obj1", "move"], 0, "obj=obj1\nmove\n"),
        ([], 2, "Show this message and exit."),
    ],
)
def test_group_with_args(runner, args, exit_code, expect):
    @click.group()
    @click.argument("obj")
    def cli(obj):
        click.echo(f"obj={obj}")

    @cli.command()
    def move():
        click.echo("move")

    result = runner.invoke(cli, args)
    assert result.exit_code == exit_code
    assert expect in result.output


def test_custom_parser(runner):
    import optparse

    @click.group()
    def cli():
        pass

    class OptParseCommand(click.Command):
        def __init__(self, name, parser, callback):
            super().__init__(name)
            self.parser = parser
            self.callback = callback

        def parse_args(self, ctx, args):
            try:
                opts, args = parser.parse_args(args)
            except Exception as e:
                ctx.fail(str(e))
            ctx.args = args
            ctx.params = vars(opts)

        def get_usage(self, ctx):
            return self.parser.get_usage()

        def get_help(self, ctx):
            return self.parser.format_help()

        def invoke(self, ctx):
            ctx.invoke(self.callback, ctx.args, **ctx.params)

    parser = optparse.OptionParser(usage="Usage: foo test [OPTIONS]")
    parser.add_option(
        "-f", "--file", dest="filename", help="write report to FILE", metavar="FILE"
    )
    parser.add_option(
        "-q",
        "--quiet",
        action="store_false",
        dest="verbose",
        default=True,
        help="don't print status messages to stdout",
    )

    def test_callback(args, filename, verbose):
        click.echo(" ".join(args))
        click.echo(filename)
        click.echo(verbose)

    cli.add_command(OptParseCommand("test", parser, test_callback))

    result = runner.invoke(cli, ["test", "-f", "f.txt", "-q", "q1.txt", "q2.txt"])
    assert result.exception is None
    assert result.output.splitlines() == ["q1.txt q2.txt", "f.txt", "False"]

    result = runner.invoke(cli, ["test", "--help"])
    assert result.exception is None
    assert result.output.splitlines() == [
        "Usage: foo test [OPTIONS]",
        "",
        "Options:",
        "  -h, --help            show this help message and exit",
        "  -f FILE, --file=FILE  write report to FILE",
        "  -q, --quiet           don't print status messages to stdout",
    ]


def test_object_propagation(runner):
    for chain in False, True:

        @click.group(chain=chain)
        @click.option("--debug/--no-debug", default=False)
        @click.pass_context
        def cli(ctx, debug):
            if ctx.obj is None:
                ctx.obj = {}
            ctx.obj["DEBUG"] = debug

        @cli.command()
        @click.pass_context
        def sync(ctx):
            click.echo(f"Debug is {'on' if ctx.obj['DEBUG'] else 'off'}")

        result = runner.invoke(cli, ["sync"])
        assert result.exception is None
        assert result.output == "Debug is off\n"


@pytest.mark.parametrize(
    ("opt_params", "expected"),
    (
        # Original tests.
        ({"type": click.INT, "default": 42}, 42),
        ({"type": click.INT, "default": "15"}, 15),
        ({"multiple": True}, ()),
        # SENTINEL value tests.
        ({"default": None}, None),
        ({"type": click.STRING}, None),  # No default specified, should be None.
        ({"type": click.BOOL, "default": False}, False),
        ({"type": click.BOOL, "default": True}, True),
        ({"type": click.FLOAT, "default": 3.14}, 3.14),
        # Multiple with default.
        ({"multiple": True, "default": [1, 2, 3]}, (1, 2, 3)),
        ({"multiple": True, "default": ()}, ()),
        # Required option without value should use SENTINEL behavior.
        ({"required": False}, None),
        # Choice type with default.
        ({"type": click.Choice(["a", "b", "c"]), "default": "b"}, "b"),
        # Path type with default.
        ({"type": click.Path(), "default": "/tmp"}, "/tmp"),
        # Flag options.
        ({"is_flag": True, "default": False}, False),
        ({"is_flag": True, "default": True}, True),
        # Count option.
        ({"count": True}, 0),
        # Hidden option.
        ({"hidden": True, "default": "secret"}, "secret"),
    ),
)
def test_other_command_invoke_with_defaults(runner, opt_params, expected):
    @click.command()
    @click.pass_context
    def cli(ctx):
        return ctx.invoke(other_cmd)

    @click.command()
    @click.option("-a", **opt_params)
    @click.pass_context
    def other_cmd(ctx, a):
        return ctx.info_name, a

    result = runner.invoke(cli, standalone_mode=False)

    assert result.return_value == ("other", expected)


def test_invoked_subcommand(runner):
    @click.group(invoke_without_command=True)
    @click.pass_context
    def cli(ctx):
        if ctx.invoked_subcommand is None:
            click.echo("no subcommand, use default")
            ctx.invoke(sync)
        else:
            click.echo("invoke subcommand")

    @cli.command()
    def sync():
        click.echo("in subcommand")

    result = runner.invoke(cli, ["sync"])
    assert not result.exception
    assert result.output == "invoke subcommand\nin subcommand\n"

    result = runner.invoke(cli)
    assert not result.exception
    assert result.output == "no subcommand, use default\nin subcommand\n"


def test_aliased_command_canonical_name(runner):
    class AliasedGroup(click.Group):
        def get_command(self, ctx, cmd_name):
            return push

        def resolve_command(self, ctx, args):
            _, command, args = super().resolve_command(ctx, args)
            return command.name, command, args

    cli = AliasedGroup()

    @cli.command()
    def push():
        click.echo("push command")

    result = runner.invoke(cli, ["pu", "--help"])
    assert not result.exception
    assert result.output.startswith("Usage: root push [OPTIONS]")


def test_group_add_command_name(runner):
    cli = click.Group("cli")
    cmd = click.Command("a", params=[click.Option(["-x"], required=True)])
    cli.add_command(cmd, "b")
    # Check that the command is accessed through the registered name,
    # not the original name.
    result = runner.invoke(cli, ["b"], default_map={"b": {"x": 3}})
    assert result.exit_code == 0


@pytest.mark.parametrize(
    ("invocation_order", "declaration_order", "expected_order"),
    [
        # Non-eager options.
        ([], ["-a"], ["-a"]),
        (["-a"], ["-a"], ["-a"]),
        ([], ["-a", "-c"], ["-a", "-c"]),
        (["-a"], ["-a", "-c"], ["-a", "-c"]),
        (["-c"], ["-a", "-c"], ["-c", "-a"]),
        ([], ["-c", "-a"], ["-c", "-a"]),
        (["-a"], ["-c", "-a"], ["-a", "-c"]),
        (["-c"], ["-c", "-a"], ["-c", "-a"]),
        (["-a", "-c"], ["-a", "-c"], ["-a", "-c"]),
        (["-c", "-a"], ["-a", "-c"], ["-c", "-a"]),
        # Eager options.
        ([], ["-b"], ["-b"]),
        (["-b"], ["-b"], ["-b"]),
        ([], ["-b", "-d"], ["-b", "-d"]),
        (["-b"], ["-b", "-d"], ["-b", "-d"]),
        (["-d"], ["-b", "-d"], ["-d", "-b"]),
        ([], ["-d", "-b"], ["-d", "-b"]),
        (["-b"], ["-d", "-b"], ["-b", "-d"]),
        (["-d"], ["-d", "-b"], ["-d", "-b"]),
        (["-b", "-d"], ["-b", "-d"], ["-b", "-d"]),
        (["-d", "-b"], ["-b", "-d"], ["-d", "-b"]),
        # Mixed options.
        ([], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-a"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-b"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-c"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-c", "-a"]),
        (["-d"], ["-a", "-b", "-c", "-d"], ["-d", "-b", "-a", "-c"]),
        (["-a", "-b"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-b", "-a"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-d", "-c"], ["-a", "-b", "-c", "-d"], ["-d", "-b", "-c", "-a"]),
        (["-c", "-d"], ["-a", "-b", "-c", "-d"], ["-d", "-b", "-c", "-a"]),
        (["-a", "-b", "-c", "-d"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        (["-b", "-d", "-a", "-c"], ["-a", "-b", "-c", "-d"], ["-b", "-d", "-a", "-c"]),
        ([], ["-b", "-d", "-e", "-a", "-c"], ["-b", "-d", "-e", "-a", "-c"]),
        (["-a", "-d"], ["-b", "-d", "-e", "-a", "-c"], ["-d", "-b", "-e", "-a", "-c"]),
        (["-c", "-d"], ["-b", "-d", "-e", "-a", "-c"], ["-d", "-b", "-e", "-c", "-a"]),
    ],
)
def test_iter_params_for_processing(
    invocation_order, declaration_order, expected_order
):
    parameters = {
        "-a": click.Option(["-a"]),
        "-b": click.Option(["-b"], is_eager=True),
        "-c": click.Option(["-c"]),
        "-d": click.Option(["-d"], is_eager=True),
        "-e": click.Option(["-e"], is_eager=True),
    }

    invocation_params = [parameters[opt_id] for opt_id in invocation_order]
    declaration_params = [parameters[opt_id] for opt_id in declaration_order]
    expected_params = [parameters[opt_id] for opt_id in expected_order]

    assert (
        click.core.iter_params_for_processing(invocation_params, declaration_params)
        == expected_params
    )


def test_help_param_priority(runner):
    """Cover the edge-case in which the eagerness of help option was not
    respected, because it was internally generated multiple times.

    See: https://github.com/pallets/click/pull/2811
    """

    def print_and_exit(ctx, param, value):
        if value:
            click.echo(f"Value of {param.name} is: {value}")
            ctx.exit()

    @click.command(context_settings={"help_option_names": ("--my-help",)})
    @click.option("-a", is_flag=True, expose_value=False, callback=print_and_exit)
    @click.option(
        "-b", is_flag=True, expose_value=False, callback=print_and_exit, is_eager=True
    )
    def cli():
        pass

    # --my-help is properly called and stop execution.
    result = runner.invoke(cli, ["--my-help"])
    assert "Value of a is: True" not in result.stdout
    assert "Value of b is: True" not in result.stdout
    assert "--my-help" in result.stdout
    assert result.exit_code == 0

    # -a is properly called and stop execution.
    result = runner.invoke(cli, ["-a"])
    assert "Value of a is: True" in result.stdout
    assert "Value of b is: True" not in result.stdout
    assert "--my-help" not in result.stdout
    assert result.exit_code == 0

    # -a takes precedence over -b and stop execution.
    result = runner.invoke(cli, ["-a", "-b"])
    assert "Value of a is: True" not in result.stdout
    assert "Value of b is: True" in result.stdout
    assert "--my-help" not in result.stdout
    assert result.exit_code == 0

    # --my-help is eager by default so takes precedence over -a and stop
    # execution, whatever the order.
    for args in [["-a", "--my-help"], ["--my-help", "-a"]]:
        result = runner.invoke(cli, args)
        assert "Value of a is: True" not in result.stdout
        assert "Value of b is: True" not in result.stdout
        assert "--my-help" in result.stdout
        assert result.exit_code == 0

    # Both -b and --my-help are eager so they're called in the order they're
    # invoked by the user.
    result = runner.invoke(cli, ["-b", "--my-help"])
    assert "Value of a is: True" not in result.stdout
    assert "Value of b is: True" in result.stdout
    assert "--my-help" not in result.stdout
    assert result.exit_code == 0

    # But there was a bug when --my-help is called before -b, because the
    # --my-help option created by click via help_option_names is internally
    # created twice and is not the same object, breaking the priority order
    # produced by iter_params_for_processing.
    result = runner.invoke(cli, ["--my-help", "-b"])
    assert "Value of a is: True" not in result.stdout
    assert "Value of b is: True" not in result.stdout
    assert "--my-help" in result.stdout
    assert result.exit_code == 0


def test_unprocessed_options(runner):
    @click.command(context_settings=dict(ignore_unknown_options=True))
    @click.argument("args", nargs=-1, type=click.UNPROCESSED)
    @click.option("--verbose", "-v", count=True)
    def cli(verbose, args):
        click.echo(f"Verbosity: {verbose}")
        click.echo(f"Args: {'|'.join(args)}")

    result = runner.invoke(cli, ["-foo", "-vvvvx", "--muhaha", "x", "y", "-x"])
    assert not result.exception
    assert result.output.splitlines() == [
        "Verbosity: 4",
        "Args: -foo|-x|--muhaha|x|y|-x",
    ]


@pytest.mark.parametrize("doc", ["CLI HELP", None])
@pytest.mark.parametrize("deprecated", [True, "USE OTHER COMMAND INSTEAD"])
def test_deprecated_in_help_messages(runner, doc, deprecated):
    @click.command(deprecated=deprecated, help=doc)
    def cli():
        pass

    result = runner.invoke(cli, ["--help"])
    assert "(DEPRECATED" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


@pytest.mark.parametrize("deprecated", [True, "USE OTHER COMMAND INSTEAD"])
def test_deprecated_in_invocation(runner, deprecated):
    @click.command(deprecated=deprecated)
    def deprecated_cmd():
        pass

    result = runner.invoke(deprecated_cmd)
    assert "DeprecationWarning:" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


def test_command_parse_args_collects_option_prefixes():
    @click.command()
    @click.option("+p", is_flag=True)
    @click.option("!e", is_flag=True)
    def test(p, e):
        pass

    ctx = click.Context(test)
    test.parse_args(ctx, [])

    assert ctx._opt_prefixes == {"-", "--", "+", "!"}


def test_group_parse_args_collects_base_option_prefixes():
    @click.group()
    @click.option("~t", is_flag=True)
    def group(t):
        pass

    @group.command()
    @click.option("+p", is_flag=True)
    def command1(p):
        pass

    @group.command()
    @click.option("!e", is_flag=True)
    def command2(e):
        pass

    ctx = click.Context(group)
    group.parse_args(ctx, ["command1", "+p"])

    assert ctx._opt_prefixes == {"-", "--", "~"}


def test_group_invoke_collects_used_option_prefixes(runner):
    opt_prefixes = set()

    @click.group()
    @click.option("~t", is_flag=True)
    def group(t):
        pass

    @group.command()
    @click.option("+p", is_flag=True)
    @click.pass_context
    def command1(ctx, p):
        nonlocal opt_prefixes
        opt_prefixes = ctx._opt_prefixes

    @group.command()
    @click.option("!e", is_flag=True)
    def command2(e):
        pass

    runner.invoke(group, ["command1"])
    assert opt_prefixes == {"-", "--", "~", "+"}


@pytest.mark.parametrize("exc", (EOFError, KeyboardInterrupt))
def test_abort_exceptions_with_disabled_standalone_mode(runner, exc):
    @click.command()
    def cli():
        raise exc("catch me!")

    rv = runner.invoke(cli, standalone_mode=False)
    assert rv.exit_code == 1
    assert isinstance(rv.exception.__cause__, exc)
    assert rv.exception.__cause__.args == ("catch me!",)

```
---

## tests/test_compat.py

```python
from click._compat import should_strip_ansi


def test_is_jupyter_kernel_output():
    class JupyterKernelFakeStream:
        pass

    # implementation detail, aka cheapskate test
    JupyterKernelFakeStream.__module__ = "ipykernel.faked"
    assert not should_strip_ansi(stream=JupyterKernelFakeStream())

```
---

## tests/test_context.py

```python
import logging
from contextlib import AbstractContextManager
from contextlib import contextmanager
from types import TracebackType

import pytest

import click
from click import Context
from click import Option
from click import Parameter
from click.core import ParameterSource
from click.decorators import help_option
from click.decorators import pass_meta_key


def test_ensure_context_objects(runner):
    class Foo:
        def __init__(self):
            self.title = "default"

    pass_foo = click.make_pass_decorator(Foo, ensure=True)

    @click.group()
    @pass_foo
    def cli(foo):
        pass

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "default\n"


def test_get_context_objects(runner):
    class Foo:
        def __init__(self):
            self.title = "default"

    pass_foo = click.make_pass_decorator(Foo, ensure=True)

    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = Foo()
        ctx.obj.title = "test"

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "test\n"


def test_get_context_objects_no_ensuring(runner):
    class Foo:
        def __init__(self):
            self.title = "default"

    pass_foo = click.make_pass_decorator(Foo)

    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = Foo()
        ctx.obj.title = "test"

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "test\n"


def test_get_context_objects_missing(runner):
    class Foo:
        pass

    pass_foo = click.make_pass_decorator(Foo)

    @click.group()
    @click.pass_context
    def cli(ctx):
        pass

    @cli.command()
    @pass_foo
    def test(foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ["test"])
    assert result.exception is not None
    assert isinstance(result.exception, RuntimeError)
    assert (
        "Managed to invoke callback without a context object of type"
        " 'Foo' existing" in str(result.exception)
    )


def test_multi_enter(runner):
    called = []

    @click.command()
    @click.pass_context
    def cli(ctx):
        def callback():
            called.append(True)

        ctx.call_on_close(callback)

        with ctx:
            pass
        assert not called

    result = runner.invoke(cli, [])
    assert result.exception is None
    assert called == [True]


def test_global_context_object(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        assert click.get_current_context() is ctx
        ctx.obj = "FOOBAR"
        assert click.get_current_context().obj == "FOOBAR"

    assert click.get_current_context(silent=True) is None
    runner.invoke(cli, [], catch_exceptions=False)
    assert click.get_current_context(silent=True) is None


def test_context_meta(runner):
    LANG_KEY = f"{__name__}.lang"

    def set_language(value):
        click.get_current_context().meta[LANG_KEY] = value

    def get_language():
        return click.get_current_context().meta.get(LANG_KEY, "en_US")

    @click.command()
    @click.pass_context
    def cli(ctx):
        assert get_language() == "en_US"
        set_language("de_DE")
        assert get_language() == "de_DE"

    runner.invoke(cli, [], catch_exceptions=False)


def test_make_pass_meta_decorator(runner):
    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.meta["value"] = "good"

    @cli.command()
    @pass_meta_key("value")
    def show(value):
        return value

    result = runner.invoke(cli, ["show"], standalone_mode=False)
    assert result.return_value == "good"


def test_make_pass_meta_decorator_doc():
    pass_value = pass_meta_key("value")
    assert "the 'value' key from :attr:`click.Context.meta`" in pass_value.__doc__
    pass_value = pass_meta_key("value", doc_description="the test value")
    assert "passes the test value" in pass_value.__doc__


def test_hiding_of_unset_sentinel_in_callbacks():
    """Fix: https://github.com/pallets/click/issues/3136"""

    def inspect_other_params(ctx, param, value):
        """A callback that inspects other parameters' values via the context."""
        assert click.get_current_context() is ctx
        click.echo(f"callback.my_arg: {ctx.params.get('my_arg')!r}")
        click.echo(f"callback.my_opt: {ctx.params.get('my_opt')!r}")
        click.echo(f"callback.my_callback: {ctx.params.get('my_callback')!r}")

        click.echo(f"callback.param: {param!r}")
        click.echo(f"callback.value: {value!r}")

        return "hard-coded"

    class ParameterInternalCheck(Option):
        """An option that checks internal state during processing."""

        def process_value(self, ctx, value):
            """Check that UNSET values are hidden as None in ctx.params within the
            callback, and then properly restored afterwards.
            """
            assert click.get_current_context() is ctx
            click.echo(f"before_process.my_arg: {ctx.params.get('my_arg')!r}")
            click.echo(f"before_process.my_opt: {ctx.params.get('my_opt')!r}")
            click.echo(f"before_process.my_callback: {ctx.params.get('my_callback')!r}")

            value = super().process_value(ctx, value)

            assert click.get_current_context() is ctx
            click.echo(f"after_process.my_arg: {ctx.params.get('my_arg')!r}")
            click.echo(f"after_process.my_opt: {ctx.params.get('my_opt')!r}")
            click.echo(f"after_process.my_callback: {ctx.params.get('my_callback')!r}")

            return value

    def change_other_params(ctx, param, value):
        """A callback that modifies other parameters' values via the context."""
        assert click.get_current_context() is ctx
        click.echo(f"before_change.my_arg: {ctx.params.get('my_arg')!r}")
        click.echo(f"before_change.my_opt: {ctx.params.get('my_opt')!r}")
        click.echo(f"before_change.my_callback: {ctx.params.get('my_callback')!r}")

        click.echo(f"before_change.param: {param!r}")
        click.echo(f"before_change.value: {value!r}")

        ctx.params["my_arg"] = "changed"
        # Reset to None parameters that where not UNSET to see they are not forced back
        # to UNSET.
        ctx.params["my_callback"] = None

        return value

    @click.command
    @click.argument("my-arg", required=False)
    @click.option("--my-opt")
    @click.option("--my-callback", callback=inspect_other_params)
    @click.option("--check-internal", cls=ParameterInternalCheck)
    @click.option(
        "--modifying-callback", cls=ParameterInternalCheck, callback=change_other_params
    )
    @click.pass_context
    def cli(ctx, my_arg, my_opt, my_callback, check_internal, modifying_callback):
        click.echo(f"cli.my_arg: {my_arg!r}")
        click.echo(f"cli.my_opt: {my_opt!r}")
        click.echo(f"cli.my_callback: {my_callback!r}")
        click.echo(f"cli.check_internal: {check_internal!r}")
        click.echo(f"cli.modifying_callback: {modifying_callback!r}")

    runner = click.testing.CliRunner()
    result = runner.invoke(cli)

    assert result.stdout.splitlines() == [
        # Values of other parameters within the callback are None, not UNSET.
        "callback.my_arg: None",
        "callback.my_opt: None",
        "callback.my_callback: None",
        "callback.param: <Option my_callback>",
        "callback.value: None",
        # Previous UNSET values were not altered by the callback.
        "before_process.my_arg: Sentinel.UNSET",
        "before_process.my_opt: Sentinel.UNSET",
        "before_process.my_callback: 'hard-coded'",
        "after_process.my_arg: Sentinel.UNSET",
        "after_process.my_opt: Sentinel.UNSET",
        "after_process.my_callback: 'hard-coded'",
        # Changes on other parameters within the callback are restored afterwards.
        "before_process.my_arg: Sentinel.UNSET",
        "before_process.my_opt: Sentinel.UNSET",
        "before_process.my_callback: 'hard-coded'",
        "before_change.my_arg: None",
        "before_change.my_opt: None",
        "before_change.my_callback: 'hard-coded'",
        "before_change.param: <ParameterInternalCheck modifying_callback>",
        "before_change.value: None",
        "after_process.my_arg: 'changed'",
        "after_process.my_opt: Sentinel.UNSET",
        "after_process.my_callback: None",
        # Unset values within the main command are UNSET, but hidden as None.
        "cli.my_arg: 'changed'",
        "cli.my_opt: None",
        "cli.my_callback: None",
        "cli.check_internal: None",
        "cli.modifying_callback: None",
    ]
    assert not result.stderr
    assert not result.exception
    assert result.exit_code == 0


def test_context_pushing():
    rv = []

    @click.command()
    def cli():
        pass

    ctx = click.Context(cli)

    @ctx.call_on_close
    def test_callback():
        rv.append(42)

    with ctx.scope(cleanup=False):
        # Internal
        assert ctx._depth == 2

    assert rv == []

    with ctx.scope():
        # Internal
        assert ctx._depth == 1

    assert rv == [42]


def test_pass_obj(runner):
    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = "test"

    @cli.command()
    @click.pass_obj
    def test(obj):
        click.echo(obj)

    result = runner.invoke(cli, ["test"])
    assert not result.exception
    assert result.output == "test\n"


def test_close_before_pop(runner):
    called = []

    @click.command()
    @click.pass_context
    def cli(ctx):
        ctx.obj = "test"

        @ctx.call_on_close
        def foo():
            assert click.get_current_context().obj == "test"
            called.append(True)

        click.echo("aha!")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "aha!\n"
    assert called == [True]


def test_close_before_exit(runner):
    called = []

    @click.command()
    @click.pass_context
    def cli(ctx):
        ctx.obj = "test"

        @ctx.call_on_close
        def foo():
            assert click.get_current_context().obj == "test"
            called.append(True)

        ctx.exit()

        click.echo("aha!")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert not result.output
    assert called == [True]


@pytest.mark.parametrize(
    ("cli_args", "expect"),
    [
        pytest.param(
            ("--option-with-callback", "--force-exit"),
            ["ExitingOption", "NonExitingOption"],
            id="natural_order",
        ),
        pytest.param(
            ("--force-exit", "--option-with-callback"),
            ["ExitingOption"],
            id="eagerness_precedence",
        ),
    ],
)
def test_multiple_eager_callbacks(runner, cli_args, expect):
    """Checks all callbacks are called on exit, even the nasty ones hidden within
    callbacks.

    Also checks the order in which they're called.
    """
    # Keeps track of callback calls.
    called = []

    class NonExitingOption(Option):
        def reset_state(self):
            called.append(self.__class__.__name__)

        def set_state(self, ctx: Context, param: Parameter, value: str) -> str:
            ctx.call_on_close(self.reset_state)
            return value

        def __init__(self, *args, **kwargs) -> None:
            kwargs.setdefault("expose_value", False)
            kwargs.setdefault("callback", self.set_state)
            super().__init__(*args, **kwargs)

    class ExitingOption(NonExitingOption):
        def set_state(self, ctx: Context, param: Parameter, value: str) -> str:
            value = super().set_state(ctx, param, value)
            ctx.exit()
            return value

    @click.command()
    @click.option("--option-with-callback", is_eager=True, cls=NonExitingOption)
    @click.option("--force-exit", is_eager=True, cls=ExitingOption)
    def cli():
        click.echo("This will never be printed as we forced exit via --force-exit")

    result = runner.invoke(cli, cli_args)
    assert not result.exception
    assert not result.output

    assert called == expect


def test_no_state_leaks(runner):
    """Demonstrate state leaks with a specific case of the generic test above.

    Use a logger as a real-world example of a common fixture which, due to its global
    nature, can leak state if not clean-up properly in a callback.
    """
    # Keeps track of callback calls.
    called = []

    class DebugLoggerOption(Option):
        """A custom option to set the name of the debug logger."""

        logger_name: str
        """The ID of the logger to use."""

        def reset_loggers(self):
            """Forces logger managed by the option to be reset to the default level."""
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(logging.NOTSET)

            # Logger has been properly reset to its initial state.
            assert logger.level == logging.NOTSET
            assert logger.getEffectiveLevel() == logging.WARNING

            called.append(True)

        def set_level(self, ctx: Context, param: Parameter, value: str) -> None:
            """Set the logger to DEBUG level."""
            # Keep the logger name around so we can reset it later when winding down
            # the option.
            self.logger_name = value

            # Get the global logger object.
            logger = logging.getLogger(self.logger_name)

            # Check pre-conditions: new logger is not set, but inherits its level from
            # default <root> logger. That's the exact same state we are expecting our
            # logger to be in after being messed with by the CLI.
            assert logger.level == logging.NOTSET
            assert logger.getEffectiveLevel() == logging.WARNING

            logger.setLevel(logging.DEBUG)
            ctx.call_on_close(self.reset_loggers)
            return value

        def __init__(self, *args, **kwargs) -> None:
            kwargs.setdefault("callback", self.set_level)
            super().__init__(*args, **kwargs)

    @click.command()
    @click.option("--debug-logger-name", is_eager=True, cls=DebugLoggerOption)
    @help_option()
    @click.pass_context
    def messing_with_logger(ctx, debug_logger_name):
        # Introspect context to make sure logger name are aligned.
        assert debug_logger_name == ctx.command.params[0].logger_name

        logger = logging.getLogger(debug_logger_name)

        # Logger's level has been properly set to DEBUG by DebugLoggerOption.
        assert logger.level == logging.DEBUG
        assert logger.getEffectiveLevel() == logging.DEBUG

        logger.debug("Blah blah blah")

        ctx.exit()

        click.echo("This will never be printed as we exited early")

    # Call the CLI to mess with the custom logger.
    result = runner.invoke(
        messing_with_logger, ["--debug-logger-name", "my_logger", "--help"]
    )

    assert called == [True]

    # Check the custom logger has been reverted to it initial state by the option
    # callback after being messed with by the CLI.
    logger = logging.getLogger("my_logger")
    assert logger.level == logging.NOTSET
    assert logger.getEffectiveLevel() == logging.WARNING

    assert not result.exception
    assert result.output.startswith("Usage: messing-with-logger [OPTIONS]")


def test_with_resource():
    @contextmanager
    def manager():
        val = [1]
        yield val
        val[0] = 0

    ctx = click.Context(click.Command("test"))

    with ctx.scope():
        rv = ctx.with_resource(manager())
        assert rv[0] == 1

    assert rv == [0]


def test_with_resource_exception() -> None:
    class TestContext(AbstractContextManager[list[int]]):
        _handle_exception: bool
        _base_val: int
        val: list[int]

        def __init__(self, base_val: int = 1, *, handle_exception: bool = True) -> None:
            self._handle_exception = handle_exception
            self._base_val = base_val

        def __enter__(self) -> list[int]:
            self.val = [self._base_val]
            return self.val

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None:
            if not exc_type:
                self.val[0] = self._base_val - 1
                return None

            self.val[0] = self._base_val + 1
            return self._handle_exception

    class TestException(Exception):
        pass

    ctx = click.Context(click.Command("test"))

    base_val = 1

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        assert rv[0] == base_val

    assert rv == [base_val - 1]

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        raise TestException()

    assert rv == [base_val + 1]

    with pytest.raises(TestException):
        with ctx.scope():
            rv = ctx.with_resource(
                TestContext(base_val=base_val, handle_exception=False)
            )
            raise TestException()


def test_with_resource_nested_exception() -> None:
    class TestContext(AbstractContextManager[list[int]]):
        _handle_exception: bool
        _base_val: int
        val: list[int]

        def __init__(self, base_val: int = 1, *, handle_exception: bool = True) -> None:
            self._handle_exception = handle_exception
            self._base_val = base_val

        def __enter__(self) -> list[int]:
            self.val = [self._base_val]
            return self.val

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> bool | None:
            if not exc_type:
                self.val[0] = self._base_val - 1
                return None

            self.val[0] = self._base_val + 1
            return self._handle_exception

    class TestException(Exception):
        pass

    ctx = click.Context(click.Command("test"))
    base_val = 1
    base_val_nested = 11

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        rv_nested = ctx.with_resource(TestContext(base_val=base_val_nested))
        assert rv[0] == base_val
        assert rv_nested[0] == base_val_nested

    assert rv == [base_val - 1]
    assert rv_nested == [base_val_nested - 1]

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        rv_nested = ctx.with_resource(TestContext(base_val=base_val_nested))
        raise TestException()

    # If one of the context "eats" the exceptions they will not be forwarded to other
    # parts. This is due to how ExitStack unwinding works
    assert rv_nested == [base_val_nested + 1]
    assert rv == [base_val - 1]

    with ctx.scope():
        rv = ctx.with_resource(TestContext(base_val=base_val))
        rv_nested = ctx.with_resource(
            TestContext(base_val=base_val_nested, handle_exception=False)
        )
        raise TestException()

    assert rv_nested == [base_val_nested + 1]
    assert rv == [base_val + 1]

    with pytest.raises(TestException):
        rv = ctx.with_resource(TestContext(base_val=base_val, handle_exception=False))
        rv_nested = ctx.with_resource(
            TestContext(base_val=base_val_nested, handle_exception=False)
        )
        raise TestException()


def test_make_pass_decorator_args(runner):
    """
    Test to check that make_pass_decorator doesn't consume arguments based on
    invocation order.
    """

    class Foo:
        title = "foocmd"

    pass_foo = click.make_pass_decorator(Foo)

    @click.group()
    @click.pass_context
    def cli(ctx):
        ctx.obj = Foo()

    @cli.command()
    @click.pass_context
    @pass_foo
    def test1(foo, ctx):
        click.echo(foo.title)

    @cli.command()
    @pass_foo
    @click.pass_context
    def test2(ctx, foo):
        click.echo(foo.title)

    result = runner.invoke(cli, ["test1"])
    assert not result.exception
    assert result.output == "foocmd\n"

    result = runner.invoke(cli, ["test2"])
    assert not result.exception
    assert result.output == "foocmd\n"


def test_propagate_show_default_setting(runner):
    """A context's ``show_default`` setting defaults to the value from
    the parent context.
    """
    group = click.Group(
        commands={
            "sub": click.Command("sub", params=[click.Option(["-a"], default="a")]),
        },
        context_settings={"show_default": True},
    )
    result = runner.invoke(group, ["sub", "--help"])
    assert "[default: a]" in result.output


def test_exit_not_standalone():
    @click.command()
    @click.pass_context
    def cli(ctx):
        ctx.exit(1)

    assert cli.main([], "test_exit_not_standalone", standalone_mode=False) == 1

    @click.command()
    @click.pass_context
    def cli(ctx):
        ctx.exit(0)

    assert cli.main([], "test_exit_not_standalone", standalone_mode=False) == 0


@pytest.mark.parametrize(
    ("option_args", "invoke_args", "expect"),
    [
        pytest.param({}, {}, ParameterSource.DEFAULT, id="default"),
        pytest.param(
            {},
            {"default_map": {"option": 1}},
            ParameterSource.DEFAULT_MAP,
            id="default_map",
        ),
        pytest.param(
            {},
            {"args": ["-o", "1"]},
            ParameterSource.COMMANDLINE,
            id="commandline short",
        ),
        pytest.param(
            {},
            {"args": ["--option", "1"]},
            ParameterSource.COMMANDLINE,
            id="commandline long",
        ),
        pytest.param(
            {},
            {"auto_envvar_prefix": "TEST", "env": {"TEST_OPTION": "1"}},
            ParameterSource.ENVIRONMENT,
            id="environment auto",
        ),
        pytest.param(
            {"envvar": "NAME"},
            {"env": {"NAME": "1"}},
            ParameterSource.ENVIRONMENT,
            id="environment manual",
        ),
    ],
)
def test_parameter_source(runner, option_args, invoke_args, expect):
    @click.command()
    @click.pass_context
    @click.option("-o", "--option", default=1, **option_args)
    def cli(ctx, option):
        return ctx.get_parameter_source("option")

    rv = runner.invoke(cli, standalone_mode=False, **invoke_args)
    assert rv.return_value == expect


def test_propagate_opt_prefixes():
    parent = click.Context(click.Command("test"))
    parent._opt_prefixes = {"-", "--", "!"}
    ctx = click.Context(click.Command("test2"), parent=parent)

    assert ctx._opt_prefixes == {"-", "--", "!"}

```
---

## tests/test_custom_classes.py

```python
import click


def test_command_context_class():
    """A command with a custom ``context_class`` should produce a
    context using that type.
    """

    class CustomContext(click.Context):
        pass

    class CustomCommand(click.Command):
        context_class = CustomContext

    command = CustomCommand("test")
    context = command.make_context("test", [])
    assert isinstance(context, CustomContext)


def test_context_invoke_type(runner):
    """A command invoked from a custom context should have a new
    context with the same type.
    """

    class CustomContext(click.Context):
        pass

    class CustomCommand(click.Command):
        context_class = CustomContext

    @click.command()
    @click.argument("first_id", type=int)
    @click.pass_context
    def second(ctx, first_id):
        assert isinstance(ctx, CustomContext)
        assert id(ctx) != first_id

    @click.command(cls=CustomCommand)
    @click.pass_context
    def first(ctx):
        assert isinstance(ctx, CustomContext)
        ctx.invoke(second, first_id=id(ctx))

    assert not runner.invoke(first).exception


def test_context_formatter_class():
    """A context with a custom ``formatter_class`` should format help
    using that type.
    """

    class CustomFormatter(click.HelpFormatter):
        def write_heading(self, heading):
            heading = click.style(heading, fg="yellow")
            return super().write_heading(heading)

    class CustomContext(click.Context):
        formatter_class = CustomFormatter

    context = CustomContext(
        click.Command("test", params=[click.Option(["--value"])]), color=True
    )
    assert "\x1b[33mOptions\x1b[0m:" in context.get_help()


def test_group_command_class(runner):
    """A group with a custom ``command_class`` should create subcommands
    of that type by default.
    """

    class CustomCommand(click.Command):
        pass

    class CustomGroup(click.Group):
        command_class = CustomCommand

    group = CustomGroup()
    subcommand = group.command()(lambda: None)
    assert type(subcommand) is CustomCommand
    subcommand = group.command(cls=click.Command)(lambda: None)
    assert type(subcommand) is click.Command


def test_group_group_class(runner):
    """A group with a custom ``group_class`` should create subgroups
    of that type by default.
    """

    class CustomSubGroup(click.Group):
        pass

    class CustomGroup(click.Group):
        group_class = CustomSubGroup

    group = CustomGroup()
    subgroup = group.group()(lambda: None)
    assert type(subgroup) is CustomSubGroup
    subgroup = group.command(cls=click.Group)(lambda: None)
    assert type(subgroup) is click.Group


def test_group_group_class_self(runner):
    """A group with ``group_class = type`` should create subgroups of
    the same type as itself.
    """

    class CustomGroup(click.Group):
        group_class = type

    group = CustomGroup()
    subgroup = group.group()(lambda: None)
    assert type(subgroup) is CustomGroup

```
---

## tests/test_defaults.py

```python
import click


def test_basic_defaults(runner):
    @click.command()
    @click.option("--foo", default=42, type=click.FLOAT)
    def cli(foo):
        assert isinstance(foo, float)
        click.echo(f"FOO:[{foo}]")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert "FOO:[42.0]" in result.output


def test_multiple_defaults(runner):
    @click.command()
    @click.option("--foo", default=[23, 42], type=click.FLOAT, multiple=True)
    def cli(foo):
        for item in foo:
            assert isinstance(item, float)
            click.echo(item)

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output.splitlines() == ["23.0", "42.0"]


def test_nargs_plus_multiple(runner):
    @click.command()
    @click.option(
        "--arg", default=((1, 2), (3, 4)), nargs=2, multiple=True, type=click.INT
    )
    def cli(arg):
        for a, b in arg:
            click.echo(f"<{a:d}|{b:d}>")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output.splitlines() == ["<1|2>", "<3|4>"]


def test_multiple_flag_default(runner):
    """Default default for flags when multiple=True should be empty tuple."""

    @click.command
    # flag due to secondary token
    @click.option("-y/-n", multiple=True)
    # flag due to is_flag
    @click.option("-f", is_flag=True, multiple=True)
    # flag due to flag_value
    @click.option("-v", "v", flag_value=1, multiple=True)
    @click.option("-q", "v", flag_value=-1, multiple=True)
    def cli(y, f, v):
        return y, f, v

    result = runner.invoke(cli, standalone_mode=False)
    assert result.return_value == ((), (), ())

    result = runner.invoke(cli, ["-y", "-n", "-f", "-v", "-q"], standalone_mode=False)
    assert result.return_value == ((True, False), (True,), (1, -1))


def test_flag_default_map(runner):
    """test flag with default map"""

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--name/--no-name", is_flag=True, show_default=True, help="name flag")
    def foo(name):
        click.echo(name)

    result = runner.invoke(cli, ["foo"])
    assert "False" in result.output

    result = runner.invoke(cli, ["foo", "--help"])
    assert "default: no-name" in result.output

    result = runner.invoke(cli, ["foo"], default_map={"foo": {"name": True}})
    assert "True" in result.output

    result = runner.invoke(cli, ["foo", "--help"], default_map={"foo": {"name": True}})
    assert "default: name" in result.output


def test_shared_param_prefers_first_default(runner):
    """test that the first default is chosen when multiple flags share a param name"""

    @click.command
    @click.option("--red", "color", flag_value="red")
    @click.option("--green", "color", flag_value="green", default=True)
    def prefers_green(color):
        click.echo(color)

    @click.command
    @click.option("--red", "color", flag_value="red", default=True)
    @click.option("--green", "color", flag_value="green")
    def prefers_red(color):
        click.echo(color)

    result = runner.invoke(prefers_green, [])
    assert "green" in result.output
    result = runner.invoke(prefers_green, ["--red"])
    assert "red" in result.output

    result = runner.invoke(prefers_red, [])
    assert "red" in result.output
    result = runner.invoke(prefers_red, ["--green"])
    assert "green" in result.output

```
---

## tests/test_formatting.py

```python
import click


def test_basic_functionality(runner):
    @click.command()
    def cli():
        """First paragraph.

        This is a very long second
        paragraph and not correctly
        wrapped but it will be rewrapped.

        \b
        This is
        a paragraph
        without rewrapping.

        \b
        1
         2
          3

        And this is a paragraph
        that will be rewrapped again.
        """

    result = runner.invoke(cli, ["--help"], terminal_width=60)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "  First paragraph.",
        "",
        "  This is a very long second paragraph and not correctly",
        "  wrapped but it will be rewrapped.",
        "",
        "  This is",
        "  a paragraph",
        "  without rewrapping.",
        "",
        "  1",
        "   2",
        "    3",
        "",
        "  And this is a paragraph that will be rewrapped again.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_wrapping_long_options_strings(runner):
    @click.group()
    def cli():
        """Top level command"""

    @cli.group()
    def a_very_long():
        """Second level"""

    @a_very_long.command()
    @click.argument("first")
    @click.argument("second")
    @click.argument("third")
    @click.argument("fourth")
    @click.argument("fifth")
    @click.argument("sixth")
    def command():
        """A command."""

    # 54 is chosen as a length where the second line is one character
    # longer than the maximum length.
    result = runner.invoke(cli, ["a-very-long", "command", "--help"], terminal_width=54)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli a-very-long command [OPTIONS] FIRST SECOND",
        "                               THIRD FOURTH FIFTH",
        "                               SIXTH",
        "",
        "  A command.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_wrapping_long_command_name(runner):
    @click.group()
    def cli():
        """Top level command"""

    @cli.group()
    def a_very_very_very_long():
        """Second level"""

    @a_very_very_very_long.command()
    @click.argument("first")
    @click.argument("second")
    @click.argument("third")
    @click.argument("fourth")
    @click.argument("fifth")
    @click.argument("sixth")
    def command():
        """A command."""

    result = runner.invoke(
        cli, ["a-very-very-very-long", "command", "--help"], terminal_width=54
    )
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli a-very-very-very-long command ",
        "           [OPTIONS] FIRST SECOND THIRD FOURTH FIFTH",
        "           SIXTH",
        "",
        "  A command.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_formatting_empty_help_lines(runner):
    @click.command()
    def cli():
        # fmt: off
        """Top level command

        """
        # fmt: on

    result = runner.invoke(cli, ["--help"])
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "  Top level command",
        "",
        "",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_formatting_usage_error(runner):
    @click.command()
    @click.argument("arg")
    def cmd(arg):
        click.echo(f"arg:{arg}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] ARG",
        "Try 'cmd --help' for help.",
        "",
        "Error: Missing argument 'ARG'.",
    ]


def test_formatting_usage_error_metavar_missing_arg(runner):
    """
    :author: @r-m-n
    Including attribution to #612
    """

    @click.command()
    @click.argument("arg", metavar="metavar")
    def cmd(arg):
        pass

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] metavar",
        "Try 'cmd --help' for help.",
        "",
        "Error: Missing argument 'metavar'.",
    ]


def test_formatting_usage_error_metavar_bad_arg(runner):
    @click.command()
    @click.argument("arg", type=click.INT, metavar="metavar")
    def cmd(arg):
        pass

    result = runner.invoke(cmd, ["3.14"])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] metavar",
        "Try 'cmd --help' for help.",
        "",
        "Error: Invalid value for 'metavar': '3.14' is not a valid integer.",
    ]


def test_formatting_usage_error_nested(runner):
    @click.group()
    def cmd():
        pass

    @cmd.command()
    @click.argument("bar")
    def foo(bar):
        click.echo(f"foo:{bar}")

    result = runner.invoke(cmd, ["foo"])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd foo [OPTIONS] BAR",
        "Try 'cmd foo --help' for help.",
        "",
        "Error: Missing argument 'BAR'.",
    ]


def test_formatting_usage_error_no_help(runner):
    @click.command(add_help_option=False)
    @click.argument("arg")
    def cmd(arg):
        click.echo(f"arg:{arg}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] ARG",
        "",
        "Error: Missing argument 'ARG'.",
    ]


def test_formatting_usage_custom_help(runner):
    @click.command(context_settings=dict(help_option_names=["--man"]))
    @click.argument("arg")
    def cmd(arg):
        click.echo(f"arg:{arg}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert result.output.splitlines() == [
        "Usage: cmd [OPTIONS] ARG",
        "Try 'cmd --man' for help.",
        "",
        "Error: Missing argument 'ARG'.",
    ]


def test_formatting_custom_type_metavar(runner):
    class MyType(click.ParamType):
        def get_metavar(self, param: click.Parameter, ctx: click.Context):
            return "MY_TYPE"

    @click.command("foo")
    @click.help_option()
    @click.argument("param", type=MyType())
    def cmd(param):
        pass

    result = runner.invoke(cmd, "--help")
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: foo [OPTIONS] MY_TYPE",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_truncating_docstring(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        """First paragraph.

        This is a very long second
        paragraph and not correctly
        wrapped but it will be rewrapped.
        \f

        :param click.core.Context ctx: Click context.
        """

    result = runner.invoke(cli, ["--help"], terminal_width=60)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "  First paragraph.",
        "",
        "  This is a very long second paragraph and not correctly",
        "  wrapped but it will be rewrapped.",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_truncating_docstring_no_help(runner):
    @click.command()
    @click.pass_context
    def cli(ctx):
        """
        \f

        This text should be truncated.
        """

    result = runner.invoke(cli, ["--help"], terminal_width=60)
    assert not result.exception
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "Options:",
        "  --help  Show this message and exit.",
    ]


def test_removing_multiline_marker(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    def cmd1():
        """\b
        This is command with a multiline help text
        which should not be rewrapped.
        The output of the short help text should
        not contain the multiline marker.
        """
        pass

    result = runner.invoke(cli, ["--help"])
    assert "\b" not in result.output


def test_global_show_default(runner):
    @click.command(context_settings=dict(show_default=True))
    @click.option("-f", "in_file", default="out.txt", help="Output file name")
    def cli():
        pass

    result = runner.invoke(cli, ["--help"])
    # the default to "--help" is not shown because it is False
    assert result.output.splitlines() == [
        "Usage: cli [OPTIONS]",
        "",
        "Options:",
        "  -f TEXT  Output file name  [default: out.txt]",
        "  --help   Show this message and exit.",
    ]


def test_formatting_with_options_metavar_empty(runner):
    cli = click.Command("cli", options_metavar="", params=[click.Argument(["var"])])
    result = runner.invoke(cli, ["--help"])
    assert "Usage: cli VAR\n" in result.output


def test_help_formatter_write_text():
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit"
    formatter = click.HelpFormatter(width=len("  Lorem ipsum dolor sit amet,"))
    formatter.current_indent = 2
    formatter.write_text(text)
    actual = formatter.getvalue()
    expected = "  Lorem ipsum dolor sit amet,\n  consectetur adipiscing elit\n"
    assert actual == expected

```
