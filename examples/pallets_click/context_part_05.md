# Repository Context Part 5/7

Generated for LLM prompt context.

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


def test_unknown_command(runner):
    result = runner.invoke(click.Group(), "unknown")
    assert result.exception
    assert "No such command 'unknown'." in result.output


@pytest.mark.parametrize(
    ("value", "expect"),
    [
        ("pause", "Did you mean 'push'?"),
        ("decline", "(Did you mean one of: 'declare', 'refine'?)"),
    ],
)
def test_suggest_possible_commands(runner, value, expect):
    cli = click.Group()

    @cli.command()
    def push():
        pass

    @cli.command()
    def declare():
        pass

    @cli.command()
    def refine():
        pass

    result = runner.invoke(cli, [value])
    assert expect in result.output

```
---

## tests/test_compat.py

```python
from __future__ import annotations

import sys

import pytest

import click


def test_is_jupyter_kernel_output():
    class JupyterKernelFakeStream:
        pass

    # implementation detail, aka cheapskate test
    JupyterKernelFakeStream.__module__ = "ipykernel.faked"
    assert click._compat._is_jupyter_kernel_output(stream=JupyterKernelFakeStream())


@pytest.mark.parametrize(
    "stream",
    [None, sys.stdin, sys.stderr, sys.stdout],
)
@pytest.mark.parametrize(
    ("color", "expected_override"),
    [
        (True, False),
        (False, True),
        (None, None),
    ],
)
@pytest.mark.parametrize(
    ("isatty", "is_jupyter", "expected"),
    [
        (True, False, False),
        (False, True, False),
        (False, False, True),
    ],
)
def test_should_strip_ansi(
    monkeypatch,
    stream,
    color: bool | None,
    expected_override: bool | None,
    isatty: bool,
    is_jupyter: bool,
    expected: bool,
) -> None:
    monkeypatch.setattr(click._compat, "isatty", lambda x: isatty)
    monkeypatch.setattr(
        click._compat, "_is_jupyter_kernel_output", lambda x: is_jupyter
    )

    if expected_override is not None:
        expected = expected_override
    assert click._compat.should_strip_ansi(stream=stream, color=color) == expected

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
import pytest

import click
from click import UNPROCESSED
from click._utils import UNSET


@pytest.mark.parametrize(
    ("default", "type", "expected_output", "expected_type"),
    [
        (42, click.FLOAT, "42.0", float),
        ("42", click.INT, "42", int),
        (1.5, click.STRING, "1.5", str),
        ("1.5", click.FLOAT, "1.5", float),
        ("true", click.BOOL, "True", bool),
        ("0", click.BOOL, "False", bool),
    ],
)
def test_basic_defaults(runner, default, type, expected_output, expected_type):
    """Smoke test: a single option's default is type-coerced.

    This covers basic single-option default type coercion.
    """

    @click.command()
    @click.option("--foo", default=default, type=type)
    def cli(foo):
        assert isinstance(foo, expected_type)
        click.echo(f"FOO:[{foo}]")

    result = runner.invoke(cli, [])
    assert not result.exception
    assert f"FOO:[{expected_output}]" in result.output


def test_multiple_defaults(runner):
    """Smoke test: each element in a multiple-option default is type-coerced.

    .. hint::
        ``test_options.py::test_good_defaults_for_multiple``
        covers the structural default processing (``list`` to
        ``tuple``, various ``nargs``) exhaustively.

        This test fills the gap of explicit
        ``type=click.FLOAT`` coercion on the elements.
    """

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
    """Smoke test: option with ``nargs=2`` + ``multiple=True`` and a
    tuple-of-tuples default.

    .. hint::
        ``test_options.py::test_good_defaults_for_multiple``
        expands this with many more edge cases with various
        ``nargs``/``multiple``/``default`` combinations.

        An argument-specific equivalent is in
        ``test_arguments.py::test_good_defaults_for_nargs``.
    """

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
    """Default for flags when multiple=True should be empty tuple."""

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
    """The first ``default=True`` wins when multiple ``flag_value`` options share
    a parameter name, regardless of which positional option carries it.

    .. hint::
        ``test_basic.py::test_flag_value_dual_options`` and
        ``test_options.py::test_default_dual_option_callback`` are wider
        parametrized sibling tests covering many more default-value types (``None``,
        ``UNSET``, strings, numbers) but always place the default on the first
        option. This test complements them by exercising both placements.
    """

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


@pytest.mark.parametrize(
    ("default_map", "key", "expected"),
    [
        # Key present in default_map.
        ({"email": "a@b.com"}, "email", "a@b.com"),
        # Key missing from default_map.
        ({"email": "a@b.com"}, "nonexistent", None),
        # No default_map at all / empty default_map.
        (None, "anything", None),
        ({}, "anything", None),
        # Falsy values are returned as-is.
        ({"key": None}, "key", None),
        ({"key": 0}, "key", 0),
        ({"key": ""}, "key", ""),
        ({"key": False}, "key", False),
    ],
)
def test_lookup_default_returns_hides_sentinel(default_map, key, expected):
    """``lookup_default()`` should return ``None`` for missing keys, not :attr:`UNSET`.

    Regression test for https://github.com/pallets/click/issues/3145.
    """
    cmd = click.Command("test")
    ctx = click.Context(cmd)
    if default_map is not None:
        ctx.default_map = default_map
    assert ctx.lookup_default(key) == expected


def test_lookup_default_callable_in_default_map(runner):
    """A callable in ``default_map`` is invoked with ``call=True``
    (the default) and returned as-is with ``call=False``.

    Click uses both paths internally:
    - ``get_default()`` passes ``call=False``,
    - ``resolve_ctx()`` passes ``call=True``.
    """
    factory = lambda: "lazy-value"  # noqa: E731

    # Unit-level: call=True invokes, call=False returns as-is.
    cmd = click.Command("test")
    ctx = click.Context(cmd)
    ctx.default_map = {"name": factory}
    assert ctx.lookup_default("name", call=True) == "lazy-value"
    assert ctx.lookup_default("name", call=False) is factory

    # Integration: the callable is invoked during value resolution.
    @click.command()
    @click.option("--name", default="original", show_default=True)
    @click.pass_context
    def cli(ctx, name):
        click.echo(f"name={name!r}")

    result = runner.invoke(cli, [], default_map={"name": factory})
    assert not result.exception
    assert "name='lazy-value'" in result.output

    # Help rendering gets the callable via call=False, so it
    # shows "(dynamic)" rather than invoking it.
    result = runner.invoke(cli, ["--help"], default_map={"name": factory})
    assert not result.exception
    assert "(dynamic)" in result.output


@pytest.mark.parametrize(
    ("args", "default_map", "expected_value", "expected_source"),
    [
        # CLI arg wins over everything.
        (["--name", "cli"], {"name": "mapped"}, "cli", "COMMANDLINE"),
        # default_map overrides parameter default.
        ([], {"name": "mapped"}, "mapped", "DEFAULT_MAP"),
        # Explicit None in default_map still counts as DEFAULT_MAP.
        ([], {"name": None}, None, "DEFAULT_MAP"),
        # Falsy values in default_map are not confused with missing keys.
        ([], {"name": ""}, "", "DEFAULT_MAP"),
        ([], {"name": 0}, "0", "DEFAULT_MAP"),
        # No default_map falls back to parameter default.
        ([], None, "original", "DEFAULT"),
    ],
)
def test_default_map_source(runner, args, default_map, expected_value, expected_source):
    """``get_parameter_source()`` reports the correct origin for a parameter
    value across the resolution chain: CLI > default_map > parameter default.
    """

    @click.command()
    @click.option("--name", default="original")
    @click.pass_context
    def cli(ctx, name):
        source = ctx.get_parameter_source("name")
        click.echo(f"name={name!r} source={source.name}")

    kwargs = {}
    if default_map is not None:
        kwargs["default_map"] = default_map
    result = runner.invoke(cli, args, **kwargs)
    assert not result.exception
    assert f"name={expected_value!r}" in result.output
    assert f"source={expected_source}" in result.output


def test_lookup_default_override_respected(runner):
    """A subclass override of ``lookup_default()`` should be called by Click
    internals, not bypassed by a private method.

    Reproduce exactly https://github.com/pallets/click/issues/3145 in which a
    subclass that falls back to prefix-based lookup when the parent returns
    ``None``.

    Previous attempts in https://github.com/pallets/click/pr/3199 were entirely
    bypassing the user's overridden method.
    """

    class CustomContext(click.Context):
        def lookup_default(self, name, call=True):
            default = super().lookup_default(name, call=call)

            if default is not None:
                return default

            # Prefix-based fallback: look up "app" sub-dict for "app_email".
            prefix = name.split("_", 1)[0]
            group = getattr(self, "default_map", None) or {}
            sub = group.get(prefix)
            if isinstance(sub, dict):
                return sub.get(name)
            return default

    @click.command("get-views")
    @click.option("--app-email", default="original", show_default=True)
    @click.pass_context
    def cli(ctx, app_email):
        click.echo(f"app_email={app_email!r}")

    cli.context_class = CustomContext
    default_map = {"app": {"app_email": "prefix@example.com"}}

    # resolve_ctx path: the override provides the runtime value.
    result = runner.invoke(cli, [], default_map=default_map)
    assert not result.exception
    assert "app_email='prefix@example.com'" in result.output

    # get_default path: the override is also used when
    # rendering --help with show_default=True.
    result = runner.invoke(cli, ["--help"], default_map=default_map)
    assert not result.exception
    assert "prefix@example.com" in result.output


class _Marker:
    """Dummy callable used as a flag_value in default tests."""

    pass


@pytest.mark.parametrize(
    ("default_map", "args", "expected"),
    [
        # No default_map: auto-aligned default returns the class, not an instance.
        (None, [], _Marker),
        # CLI flag always returns the class.
        (None, ["--opt"], _Marker),
        # Static value in default_map overrides the auto-aligned flag_value.
        ({"value": "from-map"}, [], "from-map"),
        # Callable in default_map is still invoked (not suppressed by the fix).
        ({"value": lambda: "lazy-map"}, [], "lazy-map"),
        # None in default_map overrides the flag_value.
        ({"value": None}, [], None),
        # CLI arg wins over default_map.
        ({"value": "from-map"}, ["--opt"], _Marker),
    ],
)
def test_default_map_with_callable_flag_value(runner, default_map, args, expected):
    """``default_map`` entries should override the auto-aligned callable ``flag_value``,
    and callable entries in ``default_map`` should still be invoked.

    Verifies the fix for https://github.com/pallets/click/issues/3121 does not
    break ``default_map`` precedence.
    """

    @click.command()
    @click.option("--opt", "value", flag_value=_Marker, type=UNPROCESSED, default=True)
    def cli(value):
        click.echo(repr(value), nl=False)

    kwargs = {}
    if default_map is not None:
        kwargs["default_map"] = default_map
    result = runner.invoke(cli, args, **kwargs)
    assert result.exit_code == 0
    assert result.output == repr(expected)


@pytest.mark.parametrize(
    ("default_map", "option_kwargs", "cli_args", "expected"),
    [
        # String is split for nargs=2 option.
        ({"point": "3 4"}, {"nargs": 2, "type": int}, [], (3, 4)),
        # String is split for explicit Tuple type.
        ({"point": "hello world"}, {"type": (str, str)}, [], ("hello", "world")),
        # Already-structured tuple passes through unchanged.
        ({"point": ("a", "b")}, {"nargs": 2}, [], ("a", "b")),
        # Already-structured list passes through unchanged.
        ({"point": [5, 6]}, {"nargs": 2, "type": int}, [], (5, 6)),
        # CLI args override default_map for nargs > 1.
        (
            {"point": "3 4"},
            {"nargs": 2, "type": int},
            ["--point", "10", "20"],
            (10, 20),
        ),
    ],
)
def test_default_map_nargs(runner, default_map, option_kwargs, cli_args, expected):
    """A string in ``default_map`` for an option with ``nargs > 1`` should be
    split the same way an environment variable string is split.

    Regression test for https://github.com/pallets/click/issues/2745.
    """

    @click.command()
    @click.option("--point", **option_kwargs)
    def cli(point):
        click.echo(repr(point))

    result = runner.invoke(cli, cli_args, default_map=default_map)
    assert result.exit_code == 0
    assert result.output.strip() == repr(expected)


def test_unset_in_default_map(runner):
    """An ``UNSET`` value in ``default_map`` should be treated as if
    the key is absent, and so fallback to the parameter's own default.

    Refs: https://github.com/pallets/click/pull/3224#issuecomment-3968643305
    """

    @click.command(
        context_settings={"default_map": {"port": UNSET}},
    )
    @click.option("--port", default=8000)
    def cli(port):
        click.echo(f"port={port}")

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output.strip() == "port=8000"

```
---

## tests/test_formatting.py

```python
import pytest

import click
from click._compat import strip_ansi


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


@pytest.mark.parametrize(
    ("help_names", "extra_options", "expected_hint"),
    [
        # No shadowing, longest name is picked.
        (["-h", "--help"], [], "Try 'cli foo --help' for help."),
        # -h shadowed by a subcommand option, --help still available.
        (
            ["-h", "--help"],
            [click.option("--host", "-h")],
            "Try 'cli foo --help' for help.",
        ),
        # --help shadowed, -h still available.
        (
            ["-h", "--help"],
            [click.option("--help-file", "--help")],
            "Try 'cli foo -h' for help.",
        ),
        # Both names shadowed: no hint line at all.
        (
            ["-h", "--help"],
            [click.option("--host", "-h"), click.option("--help-file", "--help")],
            None,
        ),
        # Single custom help name, not shadowed.
        (["--man"], [], "Try 'cli foo --man' for help."),
        # Three help names, one shadowed, longest survivor picked.
        (
            ["-h", "--help", "--info"],
            [click.option("--info-file", "--info")],
            "Try 'cli foo --help' for help.",
        ),
    ],
)
def test_formatting_usage_error_help_hint(
    runner, help_names, extra_options, expected_hint
):
    """The error hint should only show non-shadowed help option names,
    picking the longest for readability.

    https://github.com/pallets/click/issues/2790
    """

    @click.group(context_settings={"help_option_names": help_names})
    def cli():
        pass

    @cli.command()
    @click.argument("required_arg")
    def foo(required_arg, **kwargs):
        pass

    for option in extra_options:
        option(foo)

    result = runner.invoke(cli, ["foo"])
    assert result.exit_code == 2
    lines = result.output.splitlines()
    assert lines[0] == "Usage: cli foo [OPTIONS] REQUIRED_ARG"
    assert lines[-1] == "Error: Missing argument 'REQUIRED_ARG'."
    if expected_hint is not None:
        assert expected_hint in lines
    else:
        assert not any(line.startswith("Try ") for line in lines)


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


@pytest.mark.parametrize(
    ("body", "width", "initial_indent"),
    [
        # Styled ``initial_indent`` must be measured by visible width, so the
        # ``Usage:`` prefix shouldn't push ``[OPTIONS]`` to the second line.
        # Regression for the asymmetry between ``HelpFormatter.write_usage``
        # (which sized the prefix with ``term_len``) and ``wrap_text``
        # (which previously used raw ``len``).
        pytest.param(
            "[OPTIONS]",
            30,
            "\x1b[38;2;38;139;210m\x1b[1mUsage:\x1b[0m ",
            id="styled-initial-indent-does-not-break-body",
        ),
        # Styled chunks in the body itself wrap on visible width.
        pytest.param(
            "\x1b[31malpha\x1b[0m \x1b[31mbeta\x1b[0m"
            " \x1b[31mgamma\x1b[0m \x1b[31mdelta\x1b[0m",
            15,
            "",
            id="styled-body-wraps-on-visible-width",
        ),
        # ``_handle_long_word`` cuts a styled token between visible
        # characters; the ANSI escape sequence must not be split.
        pytest.param(
            "\x1b[31mabcdefghij\x1b[0m",
            5,
            "",
            id="styled-long-word-breaks-on-visible-width",
        ),
    ],
)
def test_wrap_text_visible_width(body, width, initial_indent):
    """``wrap_text`` of styled input produces the same line layout as
    ``wrap_text`` of the ANSI-stripped input.

    ANSI escape bytes must not count toward the width budget, regardless
    of whether they appear in the body, in ``initial_indent``, or when a
    styled token has to be broken in the middle.
    """
    styled = click.formatting.wrap_text(
        body, width=width, initial_indent=initial_indent
    )
    plain = click.formatting.wrap_text(
        strip_ansi(body), width=width, initial_indent=strip_ansi(initial_indent)
    )

    styled_visible = [strip_ansi(line) for line in styled.splitlines()]
    assert styled_visible == plain.splitlines()


def test_write_usage_styled_prefix_keeps_options_on_one_line():
    """End-to-end: a downstream-styled ``Usage:`` prefix should not split
    ``[OPTIONS]`` across two lines.
    """
    styled_prefix = "\x1b[38;2;38;139;210m\x1b[1mUsage:\x1b[0m "

    formatter = click.HelpFormatter(width=40)
    formatter.write_usage("cli", "[OPTIONS]", prefix=styled_prefix)
    rendered = formatter.getvalue()

    visible = strip_ansi(rendered)
    assert visible == "Usage: cli [OPTIONS]\n"


@pytest.mark.parametrize(
    ("formatter_kwargs", "current_indent", "prog", "args", "prefix", "expected"),
    [
        # Issue #3360: the default prefix used to emit only
        # a blank line because ``wrap_text("", initial_indent=usage_prefix)``
        # returned ``""`` and discarded the prefix.
        pytest.param(
            {},
            0,
            "Program",
            "",
            None,
            "Usage: Program\n",
            id="empty-args-default-prefix",
        ),
        # A caller-supplied prefix is preserved verbatim.
        pytest.param(
            {},
            0,
            "Program",
            "",
            "Run: ",
            "Run: Program\n",
            id="empty-args-custom-prefix",
        ),
        # ``current_indent`` is preserved even with no args to render.
        pytest.param(
            {},
            4,
            "Program",
            "",
            None,
            "Usage: Program\n",
            id="empty-args-indented",
        ),
        # Prog too long to share a line with args: the wrap branch must not
        # emit a second line.
        pytest.param(
            {"width": 20},
            0,
            "VeryLongProgramName",
            "",
            None,
            "Usage: VeryLongProgramName\n",
            id="empty-args-long-prog",
        ),
        # With non-empty args, the separator space between prog and args is preserved.
        pytest.param(
            {},
            0,
            "Program",
            "[OPTIONS]",
            None,
            "Usage: Program [OPTIONS]\n",
            id="with-args-default-prefix",
        ),
    ],
)
def test_help_formatter_write_usage(
    formatter_kwargs, current_indent, prog, args, prefix, expected
):
    """``HelpFormatter.write_usage`` renders a single usage line whose
    trailing separator tracks whether ``args`` is non-empty.
    """
    f = click.HelpFormatter(**formatter_kwargs)
    f.current_indent = current_indent
    if prefix is None:
        f.write_usage(prog, args)
    else:
        f.write_usage(prog, args, prefix=prefix)
    assert f.getvalue() == expected


def test_help_formatter_write_usage_without_args_styled_prefix():
    """A downstream-styled prefix is preserved when ``args`` is empty:
    the ANSI escape sequences survive, only the trailing separator is
    removed.
    """
    styled_prefix = "\x1b[38;2;38;139;210m\x1b[1mUsage:\x1b[0m "
    f = click.HelpFormatter()
    f.write_usage("cli", prefix=styled_prefix)
    rendered = f.getvalue()
    assert strip_ansi(rendered) == "Usage: cli\n"
    assert "\x1b[" in rendered


@pytest.mark.parametrize(
    ("command_kwargs", "expected_usage_line"),
    [
        # End-to-end regression for #3360: an empty ``options_metavar`` with
        # no parameters used to render a blank usage line.
        pytest.param(
            {"options_metavar": ""},
            "Usage: cli",
            id="empty-options-metavar-no-params",
        ),
        # End-to-end regression: ``options_metavar=None`` is the documented
        # way to suppress the ``[OPTIONS]`` slot entirely.
        pytest.param(
            {"options_metavar": None},
            "Usage: cli",
            id="none-options-metavar-no-params",
        ),
    ],
)
def test_command_write_usage_no_args(runner, command_kwargs, expected_usage_line):
    """End-to-end: a command with no parameters and an empty or absent
    ``options_metavar`` renders a usage line with just the program name,
    no trailing space.
    """
    cli = click.Command("cli", **command_kwargs)
    result = runner.invoke(cli, ["--help"])
    assert result.output.splitlines()[0] == expected_usage_line

```
---

## tests/test_imports.py

```python
import json
import subprocess
import sys

from click._compat import WIN

IMPORT_TEST = b"""\
import builtins

found_imports = set()
real_import = builtins.__import__
import sys

def tracking_import(module, locals=None, globals=None, fromlist=None,
                    level=0):
    rv = real_import(module, locals, globals, fromlist, level)
    if globals and globals['__name__'].startswith('click') and level == 0:
        found_imports.add(module)
    return rv
builtins.__import__ = tracking_import

import click
rv = list(found_imports)
import json
click.echo(json.dumps(rv))
"""

ALLOWED_IMPORTS = {
    "__future__",
    "abc",
    "codecs",
    "collections",
    "collections.abc",
    "configparser",
    "contextlib",
    "datetime",
    "enum",
    "errno",
    "fcntl",
    "functools",
    "gettext",
    "inspect",
    "io",
    "itertools",
    "os",
    "re",
    "stat",
    "struct",
    "sys",
    "threading",
    "types",
    "typing",
    "uuid",
    "weakref",
}

if WIN:
    ALLOWED_IMPORTS.update(
        {
            "ctypes",
            "ctypes._layout",
            "ctypes.wintypes",
            "msvcrt",
            "time",
        }
    )


def test_light_imports():
    c = subprocess.Popen(
        [sys.executable, "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE
    )
    rv = c.communicate(IMPORT_TEST)[0]
    rv = rv.decode("utf-8")
    imported = json.loads(rv)

    for module in imported:
        if module == "click" or module.startswith("click."):
            continue
        assert module in ALLOWED_IMPORTS

```
---

## tests/test_info_dict.py

```python
import pytest

import click.types

# Common (obj, expect) pairs used to construct multiple tests.
STRING_PARAM_TYPE = (click.STRING, {"param_type": "String", "name": "text"})
INT_PARAM_TYPE = (click.INT, {"param_type": "Int", "name": "integer"})
BOOL_PARAM_TYPE = (click.BOOL, {"param_type": "Bool", "name": "boolean"})
HELP_OPTION = (
    None,
    {
        "name": "help",
        "param_type_name": "option",
        "opts": ["--help"],
        "secondary_opts": [],
        "type": BOOL_PARAM_TYPE[1],
        "required": False,
        "nargs": 1,
        "multiple": False,
        "default": False,
        "envvar": None,
        "help": "Show this message and exit.",
        "prompt": None,
        "is_flag": True,
        "flag_value": True,
        "count": False,
        "hidden": False,
    },
)
NAME_ARGUMENT = (
    click.Argument(["name"]),
    {
        "name": "name",
        "param_type_name": "argument",
        "opts": ["name"],
        "secondary_opts": [],
        "type": STRING_PARAM_TYPE[1],
        "required": True,
        "nargs": 1,
        "multiple": False,
        "default": None,
        "envvar": None,
    },
)
NUMBER_OPTION = (
    click.Option(["-c", "--count", "number"], default=1),
    {
        "name": "number",
        "param_type_name": "option",
        "opts": ["-c", "--count"],
        "secondary_opts": [],
        "type": INT_PARAM_TYPE[1],
        "required": False,
        "nargs": 1,
        "multiple": False,
        "default": 1,
        "envvar": None,
        "help": None,
        "prompt": None,
        "is_flag": False,
        "flag_value": None,
        "count": False,
        "hidden": False,
    },
)
HELLO_COMMAND = (
    click.Command("hello", params=[NUMBER_OPTION[0]]),
    {
        "name": "hello",
        "params": [NUMBER_OPTION[1], HELP_OPTION[1]],
        "help": None,
        "epilog": None,
        "short_help": None,
        "hidden": False,
        "deprecated": False,
    },
)
HELLO_GROUP = (
    click.Group("cli", [HELLO_COMMAND[0]]),
    {
        "name": "cli",
        "params": [HELP_OPTION[1]],
        "help": None,
        "epilog": None,
        "short_help": None,
        "hidden": False,
        "deprecated": False,
        "commands": {"hello": HELLO_COMMAND[1]},
        "chain": False,
    },
)


@pytest.mark.parametrize(
    ("obj", "expect"),
    [
        pytest.param(
            click.types.FuncParamType(range),
            {"param_type": "Func", "name": "range", "func": range},
            id="Func ParamType",
        ),
        pytest.param(
            click.UNPROCESSED,
            {"param_type": "Unprocessed", "name": "text"},
            id="UNPROCESSED ParamType",
        ),
        pytest.param(*STRING_PARAM_TYPE, id="STRING ParamType"),
        pytest.param(
            click.Choice(("a", "b")),
            {
                "param_type": "Choice",
                "name": "choice",
                "choices": ("a", "b"),
                "case_sensitive": True,
            },
            id="Choice ParamType",
        ),
        pytest.param(
            click.DateTime(["%Y-%m-%d"]),
            {"param_type": "DateTime", "name": "datetime", "formats": ["%Y-%m-%d"]},
            id="DateTime ParamType",
        ),
        pytest.param(*INT_PARAM_TYPE, id="INT ParamType"),
        pytest.param(
            click.IntRange(0, 10, clamp=True),
            {
                "param_type": "IntRange",
                "name": "integer range",
                "min": 0,
                "max": 10,
                "min_open": False,
                "max_open": False,
                "clamp": True,
            },
            id="IntRange ParamType",
        ),
        pytest.param(
            click.FLOAT, {"param_type": "Float", "name": "float"}, id="FLOAT ParamType"
        ),
        pytest.param(
            click.FloatRange(-0.5, 0.5),
            {
                "param_type": "FloatRange",
                "name": "float range",
                "min": -0.5,
                "max": 0.5,
                "min_open": False,
                "max_open": False,
                "clamp": False,
            },
            id="FloatRange ParamType",
        ),
        pytest.param(*BOOL_PARAM_TYPE, id="Bool ParamType"),
        pytest.param(
            click.UUID, {"param_type": "UUID", "name": "uuid"}, id="UUID ParamType"
        ),
        pytest.param(
            click.File(),
            {"param_type": "File", "name": "filename", "mode": "r", "encoding": None},
            id="File ParamType",
        ),
        pytest.param(
            click.Path(),
            {
                "param_type": "Path",
                "name": "path",
                "exists": False,
                "file_okay": True,
                "dir_okay": True,
                "writable": False,
                "readable": True,
                "allow_dash": False,
            },
            id="Path ParamType",
        ),
        pytest.param(
            click.Tuple((click.STRING, click.INT)),
            {
                "param_type": "Tuple",
                "name": "<text integer>",
                "types": [STRING_PARAM_TYPE[1], INT_PARAM_TYPE[1]],
            },
            id="Tuple ParamType",
        ),
        pytest.param(*NUMBER_OPTION, id="Option"),
        pytest.param(
            click.Option(["--cache/--no-cache", "-c/-u"]),
            {
                "name": "cache",
                "param_type_name": "option",
                "opts": ["--cache", "-c"],
                "secondary_opts": ["--no-cache", "-u"],
                "type": BOOL_PARAM_TYPE[1],
                "required": False,
                "nargs": 1,
                "multiple": False,
                "default": False,
                "envvar": None,
                "help": None,
                "prompt": None,
                "is_flag": True,
                "flag_value": True,
                "count": False,
                "hidden": False,
            },
            id="Flag Option",
        ),
        pytest.param(*NAME_ARGUMENT, id="Argument"),
    ],
)
def test_parameter(obj, expect):
    out = obj.to_info_dict()
    assert out == expect


@pytest.mark.parametrize(
    ("obj", "expect"),
    [
        pytest.param(*HELLO_COMMAND, id="Command"),
        pytest.param(*HELLO_GROUP, id="Group"),
        pytest.param(
            click.Group(
                "base",
                [click.Command("test", params=[NAME_ARGUMENT[0]]), HELLO_GROUP[0]],
            ),
            {
                "name": "base",
                "params": [HELP_OPTION[1]],
                "help": None,
                "epilog": None,
                "short_help": None,
                "hidden": False,
                "deprecated": False,
                "commands": {
                    "cli": HELLO_GROUP[1],
                    "test": {
                        "name": "test",
                        "params": [NAME_ARGUMENT[1], HELP_OPTION[1]],
                        "help": None,
                        "epilog": None,
                        "short_help": None,
                        "hidden": False,
                        "deprecated": False,
                    },
                },
                "chain": False,
            },
            id="Nested Group",
        ),
    ],
)
def test_command(obj, expect):
    ctx = click.Context(obj)
    out = obj.to_info_dict(ctx)
    assert out == expect


def test_context():
    ctx = click.Context(HELLO_COMMAND[0])
    out = ctx.to_info_dict()
    assert out == {
        "command": HELLO_COMMAND[1],
        "info_name": None,
        "allow_extra_args": False,
        "allow_interspersed_args": True,
        "ignore_unknown_options": False,
        "auto_envvar_prefix": None,
    }


def test_paramtype_no_name():
    class TestType(click.ParamType):
        pass

    assert TestType().to_info_dict()["name"] == "TestType"

```
---

## tests/test_normalization.py

```python
import click

CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())


def test_option_normalization(runner):
    @click.command(context_settings=CONTEXT_SETTINGS)
    @click.option("--foo")
    @click.option("-x")
    def cli(foo, x):
        click.echo(foo)
        click.echo(x)

    result = runner.invoke(cli, ["--FOO", "42", "-X", 23])
    assert result.output == "42\n23\n"


def test_choice_normalization(runner):
    @click.command(context_settings=CONTEXT_SETTINGS)
    @click.option(
        "--method",
        type=click.Choice(
            ["SCREAMING_SNAKE_CASE", "snake_case", "PascalCase", "kebab-case"],
            case_sensitive=False,
        ),
    )
    def cli(method):
        click.echo(method)

    result = runner.invoke(cli, ["--METHOD=snake_case"])
    assert not result.exception, result.output
    assert result.output == "snake_case\n"

    # Even though it's case sensitive, the choice's original value is preserved
    result = runner.invoke(cli, ["--method=pascalcase"])
    assert not result.exception, result.output
    assert result.output == "PascalCase\n"

    result = runner.invoke(cli, ["--method=meh"])
    assert result.exit_code == 2
    assert (
        "Invalid value for '--method': 'meh' is not one of "
        "'screaming_snake_case', 'snake_case', 'pascalcase', 'kebab-case'."
    ) in result.output

    result = runner.invoke(cli, ["--help"])
    assert (
        "--method [screaming_snake_case|snake_case|pascalcase|kebab-case]"
        in result.output
    )


def test_command_normalization(runner):
    @click.group(context_settings=CONTEXT_SETTINGS)
    def cli():
        pass

    @cli.command()
    def foo():
        click.echo("here!")

    result = runner.invoke(cli, ["FOO"])
    assert result.output == "here!\n"

```
