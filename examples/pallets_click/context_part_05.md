# Repository Context Part 5/6

Generated for LLM prompt context.

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
    "weakref",
}

if WIN:
    ALLOWED_IMPORTS.update(["ctypes", "ctypes.wintypes", "msvcrt", "time"])


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
---

## tests/test_options.py

```python
import enum
import os
import re
import sys
import tempfile
from contextlib import nullcontext
from typing import Literal

if sys.version_info < (3, 11):
    enum.StrEnum = enum.Enum  # type: ignore[assignment]

import pytest

import click
from click import Option
from click import UNPROCESSED
from click._utils import UNSET
from click.testing import CliRunner


def test_prefixes(runner):
    @click.command()
    @click.option("++foo", is_flag=True, help="das foo")
    @click.option("--bar", is_flag=True, help="das bar")
    def cli(foo, bar):
        click.echo(f"foo={foo} bar={bar}")

    result = runner.invoke(cli, ["++foo", "--bar"])
    assert not result.exception
    assert result.output == "foo=True bar=True\n"

    result = runner.invoke(cli, ["--help"])
    assert re.search(r"\+\+foo\s+das foo", result.output) is not None
    assert re.search(r"--bar\s+das bar", result.output) is not None


def test_invalid_option(runner):
    with pytest.raises(TypeError, match="name was passed") as exc_info:
        click.Option(["foo"])

    message = str(exc_info.value)
    assert "name was passed (foo)" in message
    assert "declare an argument" in message
    assert "'--foo'" in message


@pytest.mark.parametrize("deprecated", [True, "USE B INSTEAD"])
def test_deprecated_usage(runner, deprecated):
    @click.command()
    @click.option("--foo", default="bar", deprecated=deprecated)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ["--help"])
    assert "(DEPRECATED" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


@pytest.mark.parametrize("deprecated", [True, "USE B INSTEAD"])
def test_deprecated_warning(runner, deprecated):
    @click.command()
    @click.option(
        "--my-option", required=False, deprecated=deprecated, default="default option"
    )
    def cli(my_option: str):
        click.echo(f"{my_option}")

    # defaults should not give a deprecated warning
    result = runner.invoke(cli, [])
    assert result.exit_code == 0, result.output
    assert "is deprecated" not in result.output

    result = runner.invoke(cli, ["--my-option", "hello"])
    assert result.exit_code == 0, result.output
    assert "option 'my_option' is deprecated" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


def test_deprecated_required(runner):
    with pytest.raises(ValueError, match="is deprecated and still required"):
        click.Option(["--a"], required=True, deprecated=True)


def test_deprecated_prompt(runner):
    with pytest.raises(ValueError, match="`deprecated` options cannot use `prompt`"):
        click.Option(["--a"], prompt=True, deprecated=True)


def test_invalid_nargs(runner):
    with pytest.raises(TypeError, match="nargs=-1 is not supported for options."):

        @click.command()
        @click.option("--foo", nargs=-1)
        def cli(foo):
            pass


def test_nargs_tup_composite_mult(runner):
    @click.command()
    @click.option("--item", type=(str, int), multiple=True)
    def copy(item):
        for name, id in item:
            click.echo(f"name={name} id={id:d}")

    result = runner.invoke(copy, ["--item", "peter", "1", "--item", "max", "2"])
    assert not result.exception
    assert result.output.splitlines() == ["name=peter id=1", "name=max id=2"]


def test_counting(runner):
    @click.command()
    @click.option("-v", count=True, help="Verbosity", type=click.IntRange(0, 3))
    def cli(v):
        click.echo(f"verbosity={v:d}")

    result = runner.invoke(cli, ["-vvv"])
    assert not result.exception
    assert result.output == "verbosity=3\n"

    result = runner.invoke(cli, ["-vvvv"])
    assert result.exception
    assert "Invalid value for '-v': 4 is not in the range 0<=x<=3." in result.output

    result = runner.invoke(cli, [])
    assert not result.exception
    assert result.output == "verbosity=0\n"

    result = runner.invoke(cli, ["--help"])
    assert re.search(r"-v\s+Verbosity", result.output) is not None


@pytest.mark.parametrize("unknown_flag", ["--foo", "-f"])
def test_unknown_options(runner, unknown_flag):
    @click.command()
    def cli():
        pass

    result = runner.invoke(cli, [unknown_flag])
    assert result.exception
    assert f"No such option: {unknown_flag}" in result.output


@pytest.mark.parametrize(
    ("value", "expect"),
    [
        ("--cat", "Did you mean --count?"),
        ("--bounds", "(Possible options: --bound, --count)"),
        ("--bount", "(Possible options: --bound, --count)"),
    ],
)
def test_suggest_possible_options(runner, value, expect):
    cli = click.Command(
        "cli", params=[click.Option(["--bound"]), click.Option(["--count"])]
    )
    result = runner.invoke(cli, [value])
    assert expect in result.output


def test_multiple_required(runner):
    @click.command()
    @click.option("-m", "--message", multiple=True, required=True)
    def cli(message):
        click.echo("\n".join(message))

    result = runner.invoke(cli, ["-m", "foo", "-mbar"])
    assert not result.exception
    assert result.output == "foo\nbar\n"

    result = runner.invoke(cli, [])
    assert result.exception
    assert "Error: Missing option '-m' / '--message'." in result.output


@pytest.mark.parametrize(
    ("multiple", "nargs", "default", "expected"),
    [
        # If multiple values are allowed, defaults should be iterable.
        (True, 1, [], ()),
        (True, 1, (), ()),
        (True, 1, tuple(), ()),
        (True, 1, set(), ()),
        (True, 1, frozenset(), ()),
        (True, 1, {}, ()),
        # Special values.
        (True, 1, None, ()),
        (True, 1, UNSET, ()),
        # Number of values are kept as-is in the default.
        (True, 1, [1], (1,)),
        (True, 1, [1, 2], (1, 2)),
        (True, 1, [1, 2, 3], (1, 2, 3)),
        (True, 1, [1.1, 2.2], (1.1, 2.2)),
        (True, 1, ["1", "2"], ("1", "2")),
        (True, 1, [None, None], (None, None)),
        # Contrary to list or tuples, native Python types not supported by Click are
        # not recognized and are converted to the default format: tuple of strings.
        # Refs: https://github.com/pallets/click/issues/3036
        (True, 1, {1, 2}, ("1", "2")),
        (True, 1, frozenset([1, 2]), ("1", "2")),
        (True, 1, {1: "a", 2: "b"}, ("1", "2")),
        # Multiple values with nargs > 1.
        (True, 2, [], ()),
        (True, 2, (), ()),
        (True, 2, tuple(), ()),
        (True, 2, set(), ()),
        (True, 2, frozenset(), ()),
        (True, 2, {}, ()),
        (True, 2, None, ()),
        (True, 2, UNSET, ()),
        (True, 2, [[1, 2]], ((1, 2),)),
        (True, 2, [[1, 2], [3, 4]], ((1, 2), (3, 4))),
        (True, 2, [[1, 2], [3, 4], [5, 6]], ((1, 2), (3, 4), (5, 6))),
        (True, 2, [[1.1, 2.2], [3.3, 4.4]], ((1.1, 2.2), (3.3, 4.4))),
        (True, 2, [["1", "2"], ["3", "4"]], (("1", "2"), ("3", "4"))),
        (True, 2, [[None, None], [None, None]], ((None, None), (None, None))),
        (True, 2, [[1, 2.2], ["3", None]], ((1, 2.2), (3, None))),
        (True, 2, [[1, 2.2], None], ((1, 2.2), None)),
        # Default of the right length works for non-multiples.
        (False, 2, [1, 2], (1, 2)),
    ],
)
def test_good_defaults_for_multiple(runner, multiple, nargs, default, expected):
    @click.command()
    @click.option("-a", multiple=multiple, nargs=nargs, default=default)
    def cmd(a):
        click.echo(repr(a), nl=False)

    result = runner.invoke(cmd)
    assert result.output == repr(expected)


@pytest.mark.parametrize(
    ("multiple", "nargs", "default", "exception", "message"),
    [
        # Non-iterables defaults.
        (
            True,
            1,
            "Yo",
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        (
            True,
            1,
            "",
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        (
            True,
            1,
            True,
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        (
            True,
            1,
            False,
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        (
            True,
            1,
            12,
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        (
            True,
            1,
            7.9,
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        #
        (
            False,
            2,
            42,
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        (
            True,
            2,
            ["test string which is not a list in the list"],
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        # Multiple options, each with 2 args, but with wrong length.
        (
            True,
            2,
            (1,),
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        (
            True,
            2,
            (1, 2, 3),
            None,
            "Error: Invalid value for '-a': Value must be an iterable.",
        ),
        (
            True,
            2,
            [tuple()],
            ValueError,
            r"'nargs' must be 0 \(or None\) for type <click\.types\.Tuple object at "
            r"0x[0-9A-Fa-f]+>, but it was 2\.",
        ),
        (
            True,
            2,
            [(1,)],
            ValueError,
            r"'nargs' must be 1 \(or None\) for type <click\.types\.Tuple object at "
            r"0x[0-9A-Fa-f]+>, but it was 2\.",
        ),
        (
            True,
            2,
            [(1, 2, 3)],
            ValueError,
            r"'nargs' must be 3 \(or None\) for type <click\.types\.Tuple object at "
            r"0x[0-9A-Fa-f]+>, but it was 2\.",
        ),
        # A mix of valid and invalid defaults.
        (
            True,
            2,
            [[1, 2.2], []],
            None,
            "Error: Invalid value for '-a': 2 values are required, but 0 were given.",
        ),
        # Default values that are iterable but not of the right length.
        (
            False,
            2,
            [1],
            None,
            "Error: Invalid value for '-a': Takes 2 values but 1 was given.",
        ),
        (
            True,
            2,
            [[1]],
            ValueError,
            r"'nargs' must be 1 \(or None\) for type <click\.types\.Tuple object at "
            r"0x[0-9A-Fa-f]+>, but it was 2\.",
        ),
    ],
)
def test_bad_defaults_for_multiple(
    runner, multiple, nargs, default, exception, message
):
    if exception:
        assert issubclass(exception, Exception)
    else:
        assert exception is None

    with (
        pytest.raises(exception, match=re.compile(message))
        if exception
        else nullcontext()
    ):

        @click.command()
        @click.option("-a", multiple=multiple, nargs=nargs, default=default)
        def cmd(a):
            click.echo(repr(a))

        result = runner.invoke(cmd)
        assert message in result.stderr


@pytest.mark.parametrize("env_key", ["MYPATH", "AUTO_MYPATH"])
def test_empty_envvar(runner, env_key):
    @click.command()
    @click.option("--mypath", type=click.Path(exists=True), envvar="MYPATH")
    def cli(mypath):
        click.echo(f"mypath: {mypath}")

    result = runner.invoke(cli, env={env_key: ""}, auto_envvar_prefix="AUTO")
    assert result.exception is None
    assert result.output == "mypath: None\n"


def test_multiple_envvar(runner):
    @click.command()
    @click.option("--arg", multiple=True)
    def cmd(arg):
        click.echo("|".join(arg))

    result = runner.invoke(
        cmd, [], auto_envvar_prefix="TEST", env={"TEST_ARG": "foo bar baz"}
    )
    assert not result.exception
    assert result.output == "foo|bar|baz\n"

    @click.command()
    @click.option("--arg", multiple=True, envvar="X")
    def cmd(arg):
        click.echo("|".join(arg))

    result = runner.invoke(cmd, [], env={"X": "foo bar baz"})
    assert not result.exception
    assert result.output == "foo|bar|baz\n"

    @click.command()
    @click.option("--arg", multiple=True, type=click.Path())
    def cmd(arg):
        click.echo("|".join(arg))

    result = runner.invoke(
        cmd,
        [],
        auto_envvar_prefix="TEST",
        env={"TEST_ARG": f"foo{os.path.pathsep}bar"},
    )
    assert not result.exception
    assert result.output == "foo|bar\n"


@pytest.mark.parametrize(
    ("envvar_name", "envvar_value", "expected"),
    (
        # Lower-cased variations of value.
        ("SHOUT", "true", True),
        ("SHOUT", "false", False),
        # Title-cased variations of value.
        ("SHOUT", "True", True),
        ("SHOUT", "False", False),
        # Upper-cased variations of value.
        ("SHOUT", "TRUE", True),
        ("SHOUT", "FALSE", False),
        # Random-cased variations of value.
        ("SHOUT", "TruE", True),
        ("SHOUT", "truE", True),
        ("SHOUT", "FaLsE", False),
        ("SHOUT", "falsE", False),
        # Extra spaces around the value.
        ("SHOUT", "true    ", True),
        ("SHOUT", "  true  ", True),
        ("SHOUT", "    true", True),
        ("SHOUT", "false   ", False),
        ("SHOUT", "  false ", False),
        ("SHOUT", "   false", False),
        # Integer variations.
        ("SHOUT", "1", True),
        ("SHOUT", "0", False),
        # Alternative states.
        ("SHOUT", "t", True),
        ("SHOUT", "T", True),
        ("SHOUT", "  T  ", True),
        ("SHOUT", "f", False),
        ("SHOUT", "y", True),
        ("SHOUT", "n", False),
        ("SHOUT", "yes", True),
        ("SHOUT", "no", False),
        ("SHOUT", "on", True),
        ("SHOUT", "off", False),
        # Blank value variations.
        ("SHOUT", None, False),
        ("SHOUT", "", False),
        ("SHOUT", " ", False),
        ("SHOUT", "       ", False),
        # Variable names are not stripped of spaces and so don't match the
        # flag, which then naturraly takes its default value.
        ("SHOUT    ", "True", False),
        ("SHOUT    ", "False", False),
        ("  SHOUT  ", "True", False),
        ("  SHOUT  ", "False", False),
        ("    SHOUT", "True", False),
        ("    SHOUT", "False", False),
        ("SH    OUT", "True", False),
        ("SH    OUT", "False", False),
        # Same for random and reverse environment variable names: they are not
        # recognized by the option.
        ("RANDOM", "True", False),
        ("NO_SHOUT", "True", False),
        ("NO_SHOUT", "False", False),
        ("NOSHOUT", "True", False),
        ("NOSHOUT", "False", False),
    ),
)
def test_boolean_flag_envvar(runner, envvar_name, envvar_value, expected):
    assert isinstance(envvar_name, str)
    assert isinstance(envvar_value, str) or envvar_value is None

    @click.command()
    @click.option("--shout/--no-shout", envvar="SHOUT")
    def cli(shout):
        click.echo(repr(shout), nl=False)

    result = runner.invoke(cli, [], env={envvar_name: envvar_value})
    assert result.exit_code == 0
    assert result.output == repr(expected)


@pytest.mark.parametrize(
    "value",
    (
        # Extra spaces inside the value.
        "tr ue",
        "fa lse",
        # Numbers.
        "10",
        "01",
        "00",
        "11",
        "0.0",
        "1.1",
        # Random strings.
        "randomstring",
        "None",
        "'None'",
        "A B",
        " 1 2 ",
        "9.3",
        "a;n",
        "x:y",
        "i/o",
    ),
)
def test_boolean_envvar_bad_values(runner, value):
    @click.command()
    @click.option("--shout/--no-shout", envvar="SHOUT")
    def cli(shout):
        click.echo(shout)

    result = runner.invoke(cli, [], env={"SHOUT": value})
    assert result.exit_code == 2
    assert (
        f"Invalid value for '--shout': {value!r} is not a valid boolean."
        in result.output
    )


def test_multiple_default_help(runner):
    @click.command()
    @click.option("--arg1", multiple=True, default=("foo", "bar"), show_default=True)
    @click.option("--arg2", multiple=True, default=(1, 2), type=int, show_default=True)
    def cmd(arg, arg2):
        pass

    result = runner.invoke(cmd, ["--help"])
    assert not result.exception
    assert "foo, bar" in result.output
    assert "1, 2" in result.output


def test_show_default_default_map(runner):
    @click.command()
    @click.option("--arg", default="a", show_default=True)
    def cmd(arg):
        click.echo(arg)

    result = runner.invoke(cmd, ["--help"], default_map={"arg": "b"})

    assert not result.exception
    assert "[default: b]" in result.output


def test_multiple_default_type():
    opt = click.Option(["-a"], multiple=True, default=(1, 2))
    assert opt.nargs == 1
    assert opt.multiple
    assert opt.type is click.INT
    ctx = click.Context(click.Command("test"))
    assert opt.get_default(ctx) == (1, 2)


def test_multiple_default_composite_type():
    opt = click.Option(["-a"], multiple=True, default=[(1, "a")])
    assert opt.nargs == 2
    assert opt.multiple
    assert isinstance(opt.type, click.Tuple)
    assert opt.type.types == [click.INT, click.STRING]
    ctx = click.Context(click.Command("test"))
    assert opt.type_cast_value(ctx, opt.get_default(ctx)) == ((1, "a"),)


def test_parse_multiple_default_composite_type(runner):
    @click.command()
    @click.option("-a", multiple=True, default=("a", "b"))
    @click.option("-b", multiple=True, default=[(1, "a")])
    def cmd(a, b):
        click.echo(a)
        click.echo(b)

    # result = runner.invoke(cmd, "-a c -a 1 -a d -b 2 two -b 4 four".split())
    # assert result.output == "('c', '1', 'd')\n((2, 'two'), (4, 'four'))\n"
    result = runner.invoke(cmd)
    assert result.output == "('a', 'b')\n((1, 'a'),)\n"


def test_dynamic_default_help_unset(runner):
    @click.command()
    @click.option(
        "--username",
        prompt=True,
        default=lambda: os.environ.get("USER", ""),
        show_default=True,
    )
    def cmd(username):
        print("Hello,", username)

    result = runner.invoke(cmd, ["--help"])
    assert result.exit_code == 0
    assert "--username" in result.output
    assert "lambda" not in result.output
    assert "(dynamic)" in result.output


def test_dynamic_default_help_text(runner):
    @click.command()
    @click.option(
        "--username",
        prompt=True,
        default=lambda: os.environ.get("USER", ""),
        show_default="current user",
    )
    def cmd(username):
        print("Hello,", username)

    result = runner.invoke(cmd, ["--help"])
    assert result.exit_code == 0
    assert "--username" in result.output
    assert "lambda" not in result.output
    assert "(current user)" in result.output


def test_dynamic_default_help_special_method(runner):
    class Value:
        def __call__(self):
            return 42

        def __str__(self):
            return "special value"

    opt = click.Option(["-a"], default=Value(), show_default=True)
    ctx = click.Context(click.Command("cli"))
    assert opt.get_help_extra(ctx) == {"default": "special value"}
    assert "special value" in opt.get_help_record(ctx)[1]


@pytest.mark.parametrize(
    ("type", "expect"),
    [
        (click.IntRange(1, 32), "1<=x<=32"),
        (click.IntRange(1, 32, min_open=True, max_open=True), "1<x<32"),
        (click.IntRange(1), "x>=1"),
        (click.IntRange(max=32), "x<=32"),
    ],
)
def test_intrange_default_help_text(type, expect):
    option = click.Option(["--num"], type=type, show_default=True, default=2)
    context = click.Context(click.Command("test"))
    assert option.get_help_extra(context) == {"default": "2", "range": expect}
    result = option.get_help_record(context)[1]
    assert expect in result


def test_count_default_type_help():
    """A count option with the default type should not show >=0 in help."""
    option = click.Option(["--count"], count=True, help="some words")
    context = click.Context(click.Command("test"))
    assert option.get_help_extra(context) == {}
    result = option.get_help_record(context)[1]
    assert result == "some words"


def test_file_type_help_default():
    """The default for a File type is a filename string. The string
    should be displayed in help, not an open file object.

    Type casting is only applied to defaults in processing, not when
    getting the default value.
    """
    option = click.Option(
        ["--in"], type=click.File(), default=__file__, show_default=True
    )
    context = click.Context(click.Command("test"))
    assert option.get_help_extra(context) == {"default": __file__}
    result = option.get_help_record(context)[1]
    assert __file__ in result


def test_toupper_envvar_prefix(runner):
    @click.command()
    @click.option("--arg")
    def cmd(arg):
        click.echo(arg)

    result = runner.invoke(cmd, [], auto_envvar_prefix="test", env={"TEST_ARG": "foo"})
    assert not result.exception
    assert result.output == "foo\n"


def test_nargs_envvar(runner):
    @click.command()
    @click.option("--arg", nargs=2)
    def cmd(arg):
        click.echo("|".join(arg))

    result = runner.invoke(
        cmd, [], auto_envvar_prefix="TEST", env={"TEST_ARG": "foo bar"}
    )
    assert not result.exception
    assert result.output == "foo|bar\n"

    @click.command()
    @click.option("--arg", nargs=2, multiple=True)
    def cmd(arg):
        for item in arg:
            click.echo("|".join(item))

    result = runner.invoke(
        cmd, [], auto_envvar_prefix="TEST", env={"TEST_ARG": "x 1 y 2"}
    )
    assert not result.exception
    assert result.output == "x|1\ny|2\n"


def test_show_envvar(runner):
    @click.command()
    @click.option("--arg1", envvar="ARG1", show_envvar=True)
    def cmd(arg):
        pass

    result = runner.invoke(cmd, ["--help"])
    assert not result.exception
    assert "ARG1" in result.output


def test_show_envvar_auto_prefix(runner):
    @click.command()
    @click.option("--arg1", show_envvar=True)
    def cmd(arg):
        pass

    result = runner.invoke(cmd, ["--help"], auto_envvar_prefix="TEST")
    assert not result.exception
    assert "TEST_ARG1" in result.output


def test_show_envvar_auto_prefix_dash_in_command(runner):
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--baz", show_envvar=True)
    def foo_bar(baz):
        pass

    result = runner.invoke(cli, ["foo-bar", "--help"], auto_envvar_prefix="TEST")
    assert not result.exception
    assert "TEST_FOO_BAR_BAZ" in result.output


def test_custom_validation(runner):
    def validate_pos_int(ctx, param, value):
        if value < 0:
            raise click.BadParameter("Value needs to be positive")
        return value

    @click.command()
    @click.option("--foo", callback=validate_pos_int, default=1)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ["--foo", "-1"])
    assert "Invalid value for '--foo': Value needs to be positive" in result.output

    result = runner.invoke(cmd, ["--foo", "42"])
    assert result.output == "42\n"


def test_callback_validates_prompt(runner, monkeypatch):
    def validate(ctx, param, value):
        if value < 0:
            raise click.BadParameter("should be positive")

        return value

    @click.command()
    @click.option("-a", type=int, callback=validate, prompt=True)
    def cli(a):
        click.echo(a)

    result = runner.invoke(cli, input="-12\n60\n")
    assert result.output == "A: -12\nError: should be positive\nA: 60\n60\n"


def test_winstyle_options(runner):
    @click.command()
    @click.option("/debug;/no-debug", help="Enables or disables debug mode.")
    def cmd(debug):
        click.echo(debug)

    result = runner.invoke(cmd, ["/debug"], help_option_names=["/?"])
    assert result.output == "True\n"
    result = runner.invoke(cmd, ["/no-debug"], help_option_names=["/?"])
    assert result.output == "False\n"
    result = runner.invoke(cmd, [], help_option_names=["/?"])
    assert result.output == "False\n"
    result = runner.invoke(cmd, ["/?"], help_option_names=["/?"])
    assert "/debug; /no-debug  Enables or disables debug mode." in result.output
    assert "/?                 Show this message and exit." in result.output


def test_legacy_options(runner):
    @click.command()
    @click.option("-whatever")
    def cmd(whatever):
        click.echo(whatever)

    result = runner.invoke(cmd, ["-whatever", "42"])
    assert result.output == "42\n"
    result = runner.invoke(cmd, ["-whatever=23"])
    assert result.output == "23\n"


@pytest.mark.parametrize(
    ("value", "expect_missing", "processed_value"),
    [
        (UNSET, True, None),
        (None, False, None),
        # Default type of the argument is str, so everything is processed as strings.
        ("", False, ""),
        ("  ", False, "  "),
        ("foo", False, "foo"),
        ("12", False, "12"),
        (12, False, "12"),
        (12.1, False, "12.1"),
        (list(), False, "[]"),
        (tuple(), False, "()"),
        (set(), False, "set()"),
        (frozenset(), False, "frozenset()"),
        (dict(), False, "{}"),
    ],
)
def test_required_option(value, expect_missing, processed_value):
    ctx = click.Context(click.Command(""))
    argument = click.Option(["-a"], required=True)

    if expect_missing:
        with pytest.raises(click.MissingParameter) as excinfo:
            argument.process_value(ctx, value)
        assert str(excinfo.value) == "Missing parameter: a"

    else:
        value = argument.process_value(ctx, value)
        assert value == processed_value


def test_missing_required_flag(runner):
    cli = click.Command(
        "cli", params=[click.Option(["--on/--off"], is_flag=True, required=True)]
    )
    result = runner.invoke(cli)
    assert result.exit_code == 2
    assert "Error: Missing option '--on'." in result.output


def test_missing_choice(runner):
    @click.command()
    @click.option("--foo", type=click.Choice(["foo", "bar"]), required=True)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd)
    assert result.exit_code == 2
    error, separator, choices = result.output.partition("Choose from")
    assert "Error: Missing option '--foo'. " in error
    assert "Choose from" in separator
    assert "foo" in choices
    assert "bar" in choices


def test_missing_envvar(runner):
    cli = click.Command(
        "cli", params=[click.Option(["--foo"], envvar="bar", required=True)]
    )
    result = runner.invoke(cli)
    assert result.exit_code == 2
    assert "Error: Missing option '--foo'." in result.output
    cli = click.Command(
        "cli",
        params=[click.Option(["--foo"], envvar="bar", show_envvar=True, required=True)],
    )
    result = runner.invoke(cli)
    assert result.exit_code == 2
    assert "Error: Missing option '--foo' (env var: 'bar')." in result.output

    cli = click.Command(
        "cli", params=[click.Option(["--foo"], show_envvar=True, required=True)]
    )
    result = runner.invoke(cli)
    assert result.exit_code == 2
    assert "Error: Missing option '--foo'." in result.output


def test_case_insensitive_choice(runner):
    @click.command()
    @click.option("--foo", type=click.Choice(["Orange", "Apple"], case_sensitive=False))
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ["--foo", "apple"])
    assert result.exit_code == 0
    assert result.output == "Apple\n"

    result = runner.invoke(cmd, ["--foo", "oRANGe"])
    assert result.exit_code == 0
    assert result.output == "Orange\n"

    result = runner.invoke(cmd, ["--foo", "Apple"])
    assert result.exit_code == 0
    assert result.output == "Apple\n"

    @click.command()
    @click.option("--foo", type=click.Choice(["Orange", "Apple"]))
    def cmd2(foo):
        click.echo(foo)

    result = runner.invoke(cmd2, ["--foo", "apple"])
    assert result.exit_code == 2

    result = runner.invoke(cmd2, ["--foo", "oRANGe"])
    assert result.exit_code == 2

    result = runner.invoke(cmd2, ["--foo", "Apple"])
    assert result.exit_code == 0


def test_case_insensitive_choice_returned_exactly(runner):
    @click.command()
    @click.option("--foo", type=click.Choice(["Orange", "Apple"], case_sensitive=False))
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, ["--foo", "apple"])
    assert result.exit_code == 0
    assert result.output == "Apple\n"


def test_option_help_preserve_paragraphs(runner):
    @click.command()
    @click.option(
        "-C",
        "--config",
        type=click.Path(),
        help="""Configuration file to use.

        If not given, the environment variable CONFIG_FILE is consulted
        and used if set. If neither are given, a default configuration
        file is loaded.""",
    )
    def cmd(config):
        pass

    result = runner.invoke(cmd, ["--help"])
    assert result.exit_code == 0
    i = " " * 21
    assert (
        "  -C, --config PATH  Configuration file to use.\n"
        f"{i}\n"
        f"{i}If not given, the environment variable CONFIG_FILE is\n"
        f"{i}consulted and used if set. If neither are given, a default\n"
        f"{i}configuration file is loaded."
    ) in result.output


def test_argument_custom_class(runner):
    class CustomArgument(click.Argument):
        def get_default(self, ctx, call=True):
            """a dumb override of a default value for testing"""
            return "I am a default"

    @click.command()
    @click.argument("testarg", cls=CustomArgument, default="you wont see me")
    def cmd(testarg):
        click.echo(testarg)

    result = runner.invoke(cmd)
    assert "I am a default" in result.output
    assert "you wont see me" not in result.output


def test_option_custom_class(runner):
    class CustomOption(click.Option):
        def get_help_record(self, ctx):
            """a dumb override of a help text for testing"""
            return ("--help", "I am a help text")

    @click.command()
    @click.option("--testoption", cls=CustomOption, help="you wont see me")
    def cmd(testoption):
        click.echo(testoption)

    result = runner.invoke(cmd, ["--help"])
    assert "I am a help text" in result.output
    assert "you wont see me" not in result.output


@pytest.mark.parametrize(
    ("param_decl", "option_kwargs", "pass_argv"),
    (
        # there is a large potential parameter space to explore here
        # this is just a very small sample of it
        ("--opt", {}, []),
        ("--opt", {"multiple": True}, []),
        ("--opt", {"is_flag": True}, []),
        ("--opt/--no-opt", {"is_flag": True, "default": None}, []),
        ("--req", {"is_flag": True, "required": True}, ["--req"]),
    ),
)
def test_option_custom_class_can_override_type_cast_value_and_never_sees_unset(
    runner, param_decl, option_kwargs, pass_argv
):
    """
    Test that overriding type_cast_value is supported

    In particular, the option is never passed an UNSET sentinel value.
    """

    class CustomOption(click.Option):
        def type_cast_value(self, ctx, value):
            assert value is not UNSET
            return value

    @click.command()
    @click.option("myparam", param_decl, **option_kwargs, cls=CustomOption)
    def cmd(myparam):
        click.echo("ok")

    result = runner.invoke(cmd, pass_argv)
    assert not result.exception
    assert result.exit_code == 0


def test_option_custom_class_reusable(runner):
    """Ensure we can reuse a custom class option. See Issue #926"""

    class CustomOption(click.Option):
        def get_help_record(self, ctx):
            """a dumb override of a help text for testing"""
            return ("--help", "I am a help text")

    # Assign to a variable to re-use the decorator.
    testoption = click.option("--testoption", cls=CustomOption, help="you wont see me")

    @click.command()
    @testoption
    def cmd1(testoption):
        click.echo(testoption)

    @click.command()
    @testoption
    def cmd2(testoption):
        click.echo(testoption)

    # Both of the commands should have the --help option now.
    for cmd in (cmd1, cmd2):
        result = runner.invoke(cmd, ["--help"])
        assert "I am a help text" in result.output
        assert "you wont see me" not in result.output


@pytest.mark.parametrize("custom_class", (True, False))
@pytest.mark.parametrize(
    ("name_specs", "expected"),
    (
        (
            ("-h", "--help"),
            "  -h, --help  Show this message and exit.\n",
        ),
        (
            ("-h",),
            "  -h      Show this message and exit.\n"
            "  --help  Show this message and exit.\n",
        ),
        (
            ("--help",),
            "  --help  Show this message and exit.\n",
        ),
    ),
)
def test_help_option_custom_names_and_class(runner, custom_class, name_specs, expected):
    class CustomHelpOption(click.Option):
        pass

    option_attrs = {}
    if custom_class:
        option_attrs["cls"] = CustomHelpOption

    @click.command()
    @click.help_option(*name_specs, **option_attrs)
    def cmd():
        pass

    for arg in name_specs:
        result = runner.invoke(cmd, [arg])
        assert not result.exception
        assert result.exit_code == 0
        assert expected in result.output


def test_bool_flag_with_type(runner):
    @click.command()
    @click.option("--shout/--no-shout", default=False, type=bool)
    def cmd(shout):
        pass

    result = runner.invoke(cmd)
    assert not result.exception


def test_aliases_for_flags(runner):
    @click.command()
    @click.option("--warnings/--no-warnings", " /-W", default=True)
    def cli(warnings):
        click.echo(warnings)

    result = runner.invoke(cli, ["--warnings"])
    assert result.output == "True\n"
    result = runner.invoke(cli, ["--no-warnings"])
    assert result.output == "False\n"
    result = runner.invoke(cli, ["-W"])
    assert result.output == "False\n"

    @click.command()
    @click.option("--warnings/--no-warnings", "-w", default=True)
    def cli_alt(warnings):
        click.echo(warnings)

    result = runner.invoke(cli_alt, ["--warnings"])
    assert result.output == "True\n"
    result = runner.invoke(cli_alt, ["--no-warnings"])
    assert result.output == "False\n"
    result = runner.invoke(cli_alt, ["-w"])
    assert result.output == "True\n"


@pytest.mark.parametrize(
    "option_args,expected",
    [
        (["--aggressive", "--all", "-a"], "aggressive"),
        (["--first", "--second", "--third", "-a", "-b", "-c"], "first"),
        (["--apple", "--banana", "--cantaloupe", "-a", "-b", "-c"], "apple"),
        (["--cantaloupe", "--banana", "--apple", "-c", "-b", "-a"], "cantaloupe"),
        (["-a", "-b", "-c"], "a"),
        (["-c", "-b", "-a"], "c"),
        (["-a", "--apple", "-b", "--banana", "-c", "--cantaloupe"], "apple"),
        (["-c", "-a", "--cantaloupe", "-b", "--banana", "--apple"], "cantaloupe"),
        (["--from", "-f", "_from"], "_from"),
        (["--return", "-r", "_ret"], "_ret"),
    ],
)
def test_option_names(runner, option_args, expected):
    @click.command()
    @click.option(*option_args, is_flag=True)
    def cmd(**kwargs):
        click.echo(str(kwargs[expected]))

    assert cmd.params[0].name == expected

    for form in option_args:
        if form.startswith("-"):
            result = runner.invoke(cmd, [form])
            assert result.output == "True\n"


def test_flag_duplicate_names(runner):
    with pytest.raises(ValueError, match="cannot use the same flag for true/false"):
        click.Option(["--foo/--foo"], default=False)


@pytest.mark.parametrize(("default", "expect"), [(False, "no-cache"), (True, "cache")])
def test_show_default_boolean_flag_name(runner, default, expect):
    """When a boolean flag has distinct True/False opts, it should show
    the default opt name instead of the default value. It should only
    show one name even if multiple are declared.
    """
    opt = click.Option(
        ("--cache/--no-cache", "--c/--nc"),
        default=default,
        show_default=True,
        help="Enable/Disable the cache.",
    )
    ctx = click.Context(click.Command("test"))
    assert opt.get_help_extra(ctx) == {"default": expect}
    message = opt.get_help_record(ctx)[1]
    assert f"[default: {expect}]" in message


def test_show_true_default_boolean_flag_value(runner):
    """When a boolean flag only has one opt and its default is True,
    it will show the default value, not the opt name.
    """
    opt = click.Option(
        ("--cache",),
        is_flag=True,
        show_default=True,
        default=True,
        help="Enable the cache.",
    )
    ctx = click.Context(click.Command("test"))
    assert opt.get_help_extra(ctx) == {"default": "True"}
    message = opt.get_help_record(ctx)[1]
    assert "[default: True]" in message


@pytest.mark.parametrize("default", [False, None])
def test_hide_false_default_boolean_flag_value(runner, default):
    """When a boolean flag only has one opt and its default is False or
    None, it will not show the default
    """
    opt = click.Option(
        ("--cache",),
        is_flag=True,
        show_default=True,
        default=default,
        help="Enable the cache.",
    )
    ctx = click.Context(click.Command("test"))
    assert opt.get_help_extra(ctx) == {}
    message = opt.get_help_record(ctx)[1]
    assert "[default: " not in message


def test_show_default_string(runner):
    """When show_default is a string show that value as default."""
    opt = click.Option(["--limit"], show_default="unlimited")
    ctx = click.Context(click.Command("cli"))
    assert opt.get_help_extra(ctx) == {"default": "(unlimited)"}
    message = opt.get_help_record(ctx)[1]
    assert "[default: (unlimited)]" in message


def test_show_default_with_empty_string(runner):
    """When show_default is True and default is set to an empty string."""
    opt = click.Option(["--limit"], default="", show_default=True)
    ctx = click.Context(click.Command("cli"))
    message = opt.get_help_record(ctx)[1]
    assert '[default: ""]' in message


def test_do_not_show_no_default(runner):
    """When show_default is True and no default is set do not show None."""
    opt = click.Option(["--limit"], show_default=True)
    ctx = click.Context(click.Command("cli"))
    assert opt.get_help_extra(ctx) == {}
    message = opt.get_help_record(ctx)[1]
    assert "[default: None]" not in message


def test_do_not_show_default_empty_multiple():
    """When show_default is True and multiple=True is set, it should not
    print empty default value in --help output.
    """
    opt = click.Option(["-a"], multiple=True, help="values", show_default=True)
    ctx = click.Context(click.Command("cli"))
    assert opt.get_help_extra(ctx) == {}
    message = opt.get_help_record(ctx)[1]
    assert message == "values"


@pytest.mark.parametrize(
    ("ctx_value", "opt_value", "extra_value", "expect"),
    [
        (None, None, {}, False),
        (None, False, {}, False),
        (None, True, {"default": "1"}, True),
        (False, None, {}, False),
        (False, False, {}, False),
        (False, True, {"default": "1"}, True),
        (True, None, {"default": "1"}, True),
        (True, False, {}, False),
        (True, True, {"default": "1"}, True),
        (False, "one", {"default": "(one)"}, True),
    ],
)
def test_show_default_precedence(ctx_value, opt_value, extra_value, expect):
    ctx = click.Context(click.Command("test"), show_default=ctx_value)
    opt = click.Option("-a", default=1, help="value", show_default=opt_value)
    assert opt.get_help_extra(ctx) == extra_value
    help = opt.get_help_record(ctx)[1]
    assert ("default:" in help) is expect


@pytest.mark.parametrize(
    ("args", "expect"),
    [
        (None, (None, None, ())),
        (["--opt"], ("flag", None, ())),
        (["--opt", "-a", 42], ("flag", "42", ())),
        (["--opt", "test", "-a", 42], ("test", "42", ())),
        (["--opt=test", "-a", 42], ("test", "42", ())),
        (["-o"], ("flag", None, ())),
        (["-o", "-a", 42], ("flag", "42", ())),
        (["-o", "test", "-a", 42], ("test", "42", ())),
        (["-otest", "-a", 42], ("test", "42", ())),
        (["a", "b", "c"], (None, None, ("a", "b", "c"))),
        (["--opt", "a", "b", "c"], ("a", None, ("b", "c"))),
        (["--opt", "test"], ("test", None, ())),
        (["-otest", "a", "b", "c"], ("test", None, ("a", "b", "c"))),
        (["--opt=test", "a", "b", "c"], ("test", None, ("a", "b", "c"))),
    ],
)
def test_option_with_optional_value(runner, args, expect):
    @click.command()
    @click.option("-o", "--opt", is_flag=False, flag_value="flag")
    @click.option("-a")
    @click.argument("b", nargs=-1)
    def cli(opt, a, b):
        return opt, a, b

    result = runner.invoke(cli, args, standalone_mode=False, catch_exceptions=False)
    assert result.return_value == expect


def test_multiple_option_with_optional_value(runner):
    cli = click.Command(
        "cli",
        params=[
            click.Option(["-f"], is_flag=False, flag_value="flag", multiple=True),
            click.Option(["-a"]),
            click.Argument(["b"], nargs=-1),
        ],
        callback=lambda **kwargs: kwargs,
    )
    result = runner.invoke(
        cli,
        ["-f", "-f", "other", "-f", "-a", "1", "a", "b"],
        standalone_mode=False,
        catch_exceptions=False,
    )
    assert result.return_value == {
        "f": ("flag", "other", "flag"),
        "a": "1",
        "b": ("a", "b"),
    }


def test_type_from_flag_value():
    param = click.Option(["-a", "x"], default=True, flag_value=4)
    assert param.type is click.INT
    param = click.Option(["-b", "x"], flag_value=8)
    assert param.type is click.INT


@pytest.mark.parametrize(
    ("opt_params", "args", "expected"),
    [
        # The type passed to the option is responsible to converting the value, whether
        # we pass the option flag or not.
        ({"type": bool}, [], False),
        ({"type": bool}, ["--foo"], True),
        ({"type": click.BOOL}, [], False),
        ({"type": click.BOOL}, ["--foo"], True),
        ({"type": str}, [], None),
        ({"type": str}, ["--foo"], "True"),
        # Default value is given as-is to the --foo option when it is not passed,
        # whatever the type. Now if --foo is passed, the value is always True, whatever
        # the type. In both case the type of the option is responsible for the
        # conversion of the value.
        ({"type": bool, "default": True}, [], True),
        ({"type": bool, "default": True}, ["--foo"], True),
        ({"type": bool, "default": False}, [], False),
        ({"type": bool, "default": False}, ["--foo"], True),
        # ({"type": bool, "default": "foo"}, [], "foo"),
        ({"type": bool, "default": "foo"}, ["--foo"], True),
        ({"type": bool, "default": None}, [], None),
        ({"type": bool, "default": None}, ["--foo"], True),
        ({"type": click.BOOL, "default": True}, [], True),
        ({"type": click.BOOL, "default": True}, ["--foo"], True),
        ({"type": click.BOOL, "default": False}, [], False),
        ({"type": click.BOOL, "default": False}, ["--foo"], True),
        # ({"type": click.BOOL, "default": "foo"}, [], "foo"),
        ({"type": click.BOOL, "default": "foo"}, ["--foo"], True),
        ({"type": click.BOOL, "default": None}, [], None),
        ({"type": click.BOOL, "default": None}, ["--foo"], True),
        ({"type": str, "default": True}, [], "True"),
        ({"type": str, "default": True}, ["--foo"], "True"),
        ({"type": str, "default": False}, [], "False"),
        ({"type": str, "default": False}, ["--foo"], "True"),
        ({"type": str, "default": "foo"}, [], "foo"),
        ({"type": str, "default": "foo"}, ["--foo"], "True"),
        ({"type": str, "default": None}, [], None),
        ({"type": str, "default": None}, ["--foo"], "True"),
        # Flag value is given as-is to the --foo option when it is passed, then
        # converted by the option type.
        ({"type": bool, "flag_value": True}, [], False),
        ({"type": bool, "flag_value": True}, ["--foo"], True),
        ({"type": bool, "flag_value": False}, [], False),
        ({"type": bool, "flag_value": False}, ["--foo"], False),
        ({"type": bool, "flag_value": None}, [], False),
        ({"type": bool, "flag_value": None}, ["--foo"], None),
        ({"type": click.BOOL, "flag_value": True}, [], False),
        ({"type": click.BOOL, "flag_value": True}, ["--foo"], True),
        ({"type": click.BOOL, "flag_value": False}, [], False),
        ({"type": click.BOOL, "flag_value": False}, ["--foo"], False),
        ({"type": click.BOOL, "flag_value": None}, [], False),
        ({"type": click.BOOL, "flag_value": None}, ["--foo"], None),
        ({"type": str, "flag_value": True}, [], None),
        ({"type": str, "flag_value": True}, ["--foo"], "True"),
        ({"type": str, "flag_value": False}, [], None),
        ({"type": str, "flag_value": False}, ["--foo"], "False"),
        ({"type": str, "flag_value": "foo"}, [], None),
        ({"type": str, "flag_value": "foo"}, ["--foo"], "foo"),
        ({"type": str, "flag_value": None}, [], None),
        ({"type": str, "flag_value": None}, ["--foo"], None),
        # Not passing --foo returns the default value as-is, in its Python type, then
        # converted by the option type.
        ({"type": bool, "default": True, "flag_value": True}, [], True),
        ({"type": bool, "default": True, "flag_value": False}, [], False),
        ({"type": bool, "default": False, "flag_value": True}, [], False),
        ({"type": bool, "default": False, "flag_value": False}, [], False),
        ({"type": bool, "default": None, "flag_value": True}, [], None),
        ({"type": bool, "default": None, "flag_value": False}, [], None),
        ({"type": str, "default": True, "flag_value": True}, [], "True"),
        ({"type": str, "default": True, "flag_value": False}, [], "False"),
        ({"type": str, "default": False, "flag_value": True}, [], "False"),
        ({"type": str, "default": False, "flag_value": False}, [], "False"),
        ({"type": str, "default": "foo", "flag_value": True}, [], "foo"),
        ({"type": str, "default": "foo", "flag_value": False}, [], "foo"),
        ({"type": str, "default": "foo", "flag_value": "bar"}, [], "foo"),
        ({"type": str, "default": "foo", "flag_value": None}, [], "foo"),
        ({"type": str, "default": None, "flag_value": True}, [], None),
        ({"type": str, "default": None, "flag_value": False}, [], None),
        # Passing --foo returns the flag_value that was explicitly set by the user,
        # with its Python type, but still converted by the option type.
        ({"type": bool, "default": True, "flag_value": True}, ["--foo"], True),
        ({"type": bool, "default": True, "flag_value": False}, ["--foo"], False),
        ({"type": bool, "default": False, "flag_value": True}, ["--foo"], True),
        ({"type": bool, "default": False, "flag_value": False}, ["--foo"], False),
        ({"type": bool, "default": None, "flag_value": True}, ["--foo"], True),
        ({"type": bool, "default": None, "flag_value": False}, ["--foo"], False),
        ({"type": str, "default": True, "flag_value": True}, ["--foo"], "True"),
        ({"type": str, "default": True, "flag_value": False}, ["--foo"], "False"),
        ({"type": str, "default": False, "flag_value": True}, ["--foo"], "True"),
        ({"type": str, "default": False, "flag_value": False}, ["--foo"], "False"),
        ({"type": str, "default": "foo", "flag_value": True}, ["--foo"], "True"),
        ({"type": str, "default": "foo", "flag_value": False}, ["--foo"], "False"),
        ({"type": str, "default": "foo", "flag_value": "bar"}, ["--foo"], "bar"),
        ({"type": str, "default": "foo", "flag_value": None}, ["--foo"], None),
        ({"type": str, "default": None, "flag_value": True}, ["--foo"], "True"),
        ({"type": str, "default": None, "flag_value": False}, ["--foo"], "False"),
    ],
)
def test_flag_value_and_default(runner, opt_params, args, expected):
    @click.command()
    @click.option("--foo", is_flag=True, **opt_params)
    def cmd(foo):
        click.echo(repr(foo), nl=False)

    result = runner.invoke(cmd, args)
    assert result.output == repr(expected)


@pytest.mark.parametrize(
    ("args", "opts"),
    [
        ([], {"type": bool, "default": "foo"}),
        ([], {"type": click.BOOL, "default": "foo"}),
        (["--foo"], {"type": bool, "flag_value": "foo"}),
        (["--foo"], {"type": click.BOOL, "flag_value": "foo"}),
    ],
)
def test_invalid_flag_definition(runner, args, opts):
    @click.command()
    @click.option("--foo", is_flag=True, **opts)
    def cmd(foo):
        click.echo(foo)

    result = runner.invoke(cmd, args)
    assert (
        "Error: Invalid value for '--foo': 'foo' is not a valid boolean"
        in result.output
    )


@pytest.mark.parametrize(
    ("default", "args", "expected"),
    # These test cases are similar to the ones in
    # tests/test_basic.py::test_flag_value_dual_options, so keep them in sync.
    (
        # Each option is returning its own flag_value, whatever the default is.
        (True, ["--js"], "js"),
        (True, ["--xml"], "xml"),
        (False, ["--js"], "js"),
        (False, ["--xml"], "xml"),
        (None, ["--js"], "js"),
        (None, ["--xml"], "xml"),
        (UNSET, ["--js"], "js"),
        (UNSET, ["--xml"], "xml"),
        # Check that the last option wins when both are specified.
        (True, ["--js", "--xml"], "xml"),
        (True, ["--xml", "--js"], "js"),
        # Check that the default is returned as-is when no option is specified.
        ("js", [], "js"),
        ("xml", [], "xml"),
        ("jS", [], "jS"),
        ("xMl", [], "xMl"),
        (" ᕕ( ᐛ )ᕗ ", [], " ᕕ( ᐛ )ᕗ "),
        (None, [], None),
        # Special case: UNSET is not provided as-is to the callback, but normalized to
        # None.
        (UNSET, [], None),
        # Special case: if default=True and flag_value is set, the value returned is the
        # flag_value, not the True Python value itself.
        (True, [], "js"),
        # Non-string defaults are process as strings by the default Parameter's type.
        (False, [], "False"),
        (42, [], "42"),
        (12.3, [], "12.3"),
    ),
)
def test_default_dual_option_callback(runner, default, args, expected):
    """Check how default is processed by the callback when options compete for the same
    variable name.

    Reproduction of the issue reported in
    https://github.com/pallets/click/pull/3030#discussion_r2271571819
    """

    def _my_func(ctx, param, value):
        # Print the value received by the callback as-is, so we can check for it.
        return f"Callback value: {value!r}"

    @click.command()
    @click.option("--js", "fmt", flag_value="js", callback=_my_func, default=default)
    @click.option("--xml", "fmt", flag_value="xml", callback=_my_func)
    def main(fmt):
        click.secho(fmt, nl=False)

    result = runner.invoke(main, args)
    assert result.output == f"Callback value: {expected!r}"
    assert result.exit_code == 0


@pytest.mark.parametrize(
    ("flag_value", "envvar_value", "expected"),
    [
        # The envvar match exactly the flag value and is case-sensitive.
        ("bar", "bar", "bar"),
        ("BAR", "BAR", "BAR"),
        (" bar ", " bar ", " bar "),
        ("42", "42", "42"),
        ("None", "None", "None"),
        ("True", "True", "True"),
        ("False", "False", "False"),
        ("true", "true", "true"),
        ("false", "false", "false"),
        ("A B", "A B", "A B"),
        (" 1 2 ", " 1 2 ", " 1 2 "),
        ("9.3", "9.3", "9.3"),
        ("a;n", "a;n", "a;n"),
        ("x:y", "x:y", "x:y"),
        ("i/o", "i/o", "i/o"),
        # Empty or absent envvar is consider unset, so the flag default value is
        # returned, which is None in this case.
        ("bar", "", None),
        ("bar", None, None),
        ("BAR", "", None),
        ("BAR", None, None),
        (" bar ", "", None),
        (" bar ", None, None),
        (42, "", None),
        (42, None, None),
        ("42", "", None),
        ("42", None, None),
        (None, "", None),
        (None, None, None),
        ("None", "", None),
        ("None", None, None),
        (True, "", None),
        (True, None, None),
        ("True", "", None),
        ("True", None, None),
        ("true", "", None),
        ("true", None, None),
        (False, "", None),
        (False, None, None),
        ("False", "", None),
        ("False", None, None),
        ("false", "", None),
        ("false", None, None),
        # Activate the flag with a value recognized as True by the envvar, which
        # returns the flag_value.
        ("bar", "True", "bar"),
        ("bar", "true", "bar"),
        ("bar", "trUe", "bar"),
        ("bar", "  TRUE  ", "bar"),
        ("bar", "1", "bar"),
        ("bar", "yes", "bar"),
        ("bar", "on", "bar"),
        ("bar", "t", "bar"),
        ("bar", "y", "bar"),
        # Deactivating the flag with a value recognized as False by the envvar, which
        # explicitly return the 'False' as the option is explicitly declared as a
        # string.
        ("bar", "False", "False"),
        ("bar", "false", "False"),
        ("bar", "faLse", "False"),
        ("bar", "  FALSE  ", "False"),
        ("bar", "0", "False"),
        ("bar", "no", "False"),
        ("bar", "off", "False"),
        ("bar", "f", "False"),
        ("bar", "n", "False"),
        # Any other value than the flag_value, or a recogned True or False value, fails
        # to explicitly activate or deactivate the flag. So the flag default value is
        # returned, which is None in this case.
        ("bar", " bar ", None),
        ("bar", "BAR", None),
        ("bar", "random", None),
        ("bar", "bar random", None),
        ("bar", "random bar", None),
        ("BAR", "bar", None),
        (" bar ", "bar", None),
        (" bar ", "BAR", None),
        (42, "42", None),
        (42, "foo", None),
        (None, "foo", None),
        ("None", "foo", None),
    ],
)
def test_envvar_string_flag_value(runner, flag_value, envvar_value, expected):
    """Ensure that flag_value is recognized by the envvar."""

    @click.command()
    @click.option("--upper", type=str, flag_value=flag_value, envvar="UPPER")
    def cmd(upper):
        click.echo(repr(upper), nl=False)

    result = runner.invoke(cmd, env={"UPPER": envvar_value})
    assert result.exit_code == 0
    assert result.output == repr(expected)


@pytest.mark.parametrize(
    ("opt_decls", "opt_params", "expect_is_flag", "expect_is_bool_flag"),
    [
        # Not boolean flags.
        ("-a", {"type": int}, False, False),
        ("-a", {"type": bool}, False, False),
        ("-a", {"default": True}, False, False),
        ("-a", {"default": False}, False, False),
        ("-a", {"flag_value": 1}, True, False),
        # Boolean flags.
        ("-a", {"is_flag": True}, True, True),
        ("-a/-A", {}, True, True),
        ("-a", {"flag_value": True}, True, True),
        # Non-flag with flag_value.
        ("-a", {"is_flag": False, "flag_value": 1}, False, False),
    ],
)
def test_flag_auto_detection(
    opt_decls, opt_params, expect_is_flag, expect_is_bool_flag
):
    option = Option([opt_decls], **opt_params)
    assert option.is_flag is expect_is_flag
    assert option.is_bool_flag is expect_is_bool_flag


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"count": True, "multiple": True}, "'count' is not valid with 'multiple'."),
        ({"count": True, "is_flag": True}, "'count' is not valid with 'is_flag'."),
    ],
)
def test_invalid_flag_combinations(runner, kwargs, message):
    with pytest.raises(TypeError) as e:
        click.Option(["-a"], **kwargs)

    assert message in str(e.value)


def test_non_flag_with_non_negatable_default(runner):
    class NonNegatable:
        def __bool__(self):
            raise ValueError("Cannot negate this object")

    @click.command()
    @click.option("--foo", default=NonNegatable())
    def cmd(foo):
        pass

    result = runner.invoke(cmd)
    assert result.exit_code == 0


class HashType(enum.Enum):
    MD5 = "MD5"
    SHA1 = "SHA1"
    SHA256 = "SHA-256"


class Number(enum.IntEnum):
    ONE = enum.auto()
    TWO = enum.auto()


class Letter(enum.StrEnum):
    NAME_1 = "Value-1"
    NAME_2 = "Value_2"
    NAME_3 = "42_value"


class Color(enum.Flag):
    RED = enum.auto()
    GREEN = enum.auto()
    BLUE = enum.auto()


class ColorInt(enum.IntFlag):
    RED = enum.auto()
    GREEN = enum.auto()
    BLUE = enum.auto()


@pytest.mark.parametrize(
    ("choices", "metavar"),
    [
        (["foo", "bar"], "[TEXT]"),
        ([1, 2], "[INTEGER]"),
        ([1.0, 2.0], "[FLOAT]"),
        ([True, False], "[BOOLEAN]"),
        (["foo", 1], "[TEXT|INTEGER]"),
        (HashType, "[HASHTYPE]"),
        (Number, "[NUMBER]"),
        (Letter, "[LETTER]"),
        (Color, "[COLOR]"),
        (ColorInt, "[COLORINT]"),
    ],
)
def test_choice_usage_rendering(runner, choices, metavar):
    """BY default ``--help`` prints choice's values in the usage message.

    But ``show_choices=False`` makes ``--help`` prints choice's METAVAR instead of
    values.

    Also check that usage error message always suggests the actual values.
    """

    @click.command()
    @click.option("-g", type=click.Choice(choices))
    def cli_with_choices(g):
        pass

    @click.command()
    @click.option("-g", type=click.Choice(choices), show_choices=False)
    def cli_without_choices(g):
        pass

    display_values = tuple(
        i.name if isinstance(i, enum.Enum) else str(i) for i in choices
    )

    # Check that the choices values are rendered as-is in the usage message.
    result = runner.invoke(cli_with_choices, ["--help"])
    assert f"[{'|'.join(display_values)}]" in result.stdout
    assert not result.stderr
    assert result.exit_code == 0

    # Check that the metavar is rendered instead of the choices values themselves.
    result = runner.invoke(cli_without_choices, ["--help"])
    assert metavar in result.stdout
    assert not result.stderr
    assert result.exit_code == 0

    # Check the usage error message suggests the actual accepted values.
    for cli in (cli_with_choices, cli_without_choices):
        result = runner.invoke(cli, ["-g", "random"])
        assert (
            "\n\nError: Invalid value for '-g': 'random' is not one of "
            f"{', '.join(map(repr, display_values))}.\n" in result.stderr
        )
        assert not result.stdout
        assert result.exit_code == 2


@pytest.mark.parametrize(
    ("choices", "default", "default_string"),
    [
        (["foo", "bar"], "bar", "bar"),
        # The default value is not enforced to be in the choices.
        (["foo", "bar"], "random", "random"),
        # None cannot be a default value as-is: it left the default value as unset.
        (["foo", "bar"], None, None),
        ([0, 1], 0, "0"),
        # Values are not coerced to the type of the choice, even if equivalent.
        ([0, 1], 0.0, "0.0"),
        ([1, 2], 2, "2"),
        ([1.0, 2.0], 2, "2"),
        ([1.0, 2.0], 2.0, "2.0"),
        ([True, False], True, "True"),
        ([True, False], False, "False"),
        (["foo", 1], "foo", "foo"),
        (["foo", 1], 1, "1"),
        # Enum choices are rendered as their names, not values.
        # See: https://github.com/pallets/click/issues/2911
        (HashType, HashType.SHA1, "SHA1"),
        # Enum choices allow defaults strings that are their names.
        (HashType, HashType.SHA256, "SHA256"),
        (HashType, "SHA256", "SHA256"),
        (Number, Number.TWO, "TWO"),
        (Number, "TWO", "TWO"),
        (Letter, Letter.NAME_1, "NAME_1"),
        (Letter, Letter.NAME_2, "NAME_2"),
        (Letter, Letter.NAME_3, "NAME_3"),
        (Letter, "NAME_1", "NAME_1"),
        (Letter, "NAME_2", "NAME_2"),
        (Letter, "NAME_3", "NAME_3"),
        (Color, Color.GREEN, "GREEN"),
        (Color, "GREEN", "GREEN"),
        (ColorInt, ColorInt.GREEN, "GREEN"),
        (ColorInt, "GREEN", "GREEN"),
    ],
)
def test_choice_default_rendering(runner, choices, default, default_string):
    @click.command()
    @click.option("-g", type=click.Choice(choices), default=default, show_default=True)
    def cli_with_choices(g):
        pass

    # Check that the default value is kept normalized to the type of the choice.
    assert cli_with_choices.params[0].default == default

    result = runner.invoke(cli_with_choices, ["--help"])
    extra_usage = f"[default: {default_string}]"
    if default_string is None:
        assert extra_usage not in result.output
    else:
        assert extra_usage in result.output


@pytest.mark.parametrize(
    "opts_one,opts_two",
    [
        # No duplicate shortnames
        (
            ("-a", "--aardvark"),
            ("-a", "--avocado"),
        ),
        # No duplicate long names
        (
            ("-a", "--aardvark"),
            ("-b", "--aardvark"),
        ),
    ],
)
def test_duplicate_names_warning(runner, opts_one, opts_two):
    @click.command()
    @click.option(*opts_one)
    @click.option(*opts_two)
    def cli(one, two):
        pass

    with pytest.warns(UserWarning):
        runner.invoke(cli, [])


OBJECT_SENTINEL = object()
"""An object-based sentinel value."""


class EnumSentinel(enum.Enum):
    FALSY_SENTINEL = object()

    def __bool__(self) -> Literal[False]:
        """Force the sentinel to be falsy to make sure it is not caught by Click
        internal implementation.

        Falsy sentinels have been discussed in:
        https://github.com/pallets/click/pull/3030#pullrequestreview-3106604795
        https://github.com/pallets/click/pull/3030#pullrequestreview-3108471552
        """
        return False


# Any kind of sentinel value is recognized by Click as a valid flag value.
@pytest.mark.parametrize("sentinel", (OBJECT_SENTINEL, EnumSentinel.FALSY_SENTINEL))
@pytest.mark.parametrize(
    ("args", "expected"),
    (
        # Option default to None.
        ([], None),
        # Config has no default value, and no flag value, so it requires an argument.
        (
            ["--config"],
            re.compile(re.escape("Error: Option '--config' requires an argument.\n")),
        ),
        (
            ["--no-config", "--config"],
            re.compile(re.escape("Error: Option '--config' requires an argument.\n")),
        ),
        # Passing --no-config defaults to the sentinel value because of the flag_value,
        # and then the custom type receives that sentinel and returns a message.
        (["--no-config"], "No configuration file provided."),
        # Passing --config with an argument returns the file path.
        (["--config", "foo.conf"], "foo.conf"),
        # An argument is not allowed for --no-config, so it raises an error.
        (
            ["--no-config", "foo.conf"],
            re.compile(
                r"Usage: main \[OPTIONS\]\n"
                r"Try 'main --help' for help.\n"
                r"\n"
                r"Error: Got unexpected extra argument (.+)\n"
            ),
        ),
        # Passing --config with an argument that does not exist raises an error.
        (
            ["--config", "random-file.conf"],
            re.compile(
                r"Usage: main \[OPTIONS\]\n"
                r"Try 'main --help' for help.\n"
                r"\n"
                r"Error: Invalid value for '-c' / '--config': "
                r"File 'random-file.conf' does not exist.\n"
            ),
        ),
        (
            ["--config", "--no-config"],
            re.compile(
                r"Usage: main \[OPTIONS\]\n"
                r"Try 'main --help' for help.\n"
                r"\n"
                r"Error: Invalid value for '-c' / '--config': "
                r"File '--no-config' does not exist.\n"
            ),
        ),
        (
            ["--config", "--no-config", "foo.conf"],
            re.compile(
                r"Usage: main \[OPTIONS\]\n"
                r"Try 'main --help' for help.\n"
                r"\n"
                r"Error: Invalid value for '-c' / '--config': "
                r"File '--no-config' does not exist.\n"
            ),
        ),
        # --config is passed last and overrides the --no-config option.
        (["--no-config", "--config", "foo.conf"], "foo.conf"),
    ),
)
def test_dual_options_custom_type_sentinel_flag_value(runner, sentinel, args, expected):
    """Check that an object-based sentinel, used as a flag value, is returned as-is
    to a custom type that is shared by two options, competing for the same variable
    name.

    A reproduction of
    https://github.com/pallets/click/issues/3024#issuecomment-3146511356
    """

    class ConfigParamType(click.ParamType):
        """A custom type that accepts a file path or a sentinel value."""

        def convert(self, value, param, ctx):
            if value is sentinel:
                return "No configuration file provided."
            else:
                return click.Path(exists=True, dir_okay=False).convert(
                    value, param, ctx
                )

    @click.command()
    @click.option("-c", "--config", type=ConfigParamType())
    @click.option("--no-config", "config", flag_value=sentinel, type=ConfigParamType())
    def main(config):
        click.echo(repr(config), nl=False)

    with tempfile.NamedTemporaryFile(mode="w") as named_tempfile:
        if "foo.conf" in args:
            named_tempfile.write("Blah blah")
            named_tempfile.flush()
            args = [named_tempfile.name if a == "foo.conf" else a for a in args]

        result = runner.invoke(main, args)

        if isinstance(expected, re.Pattern):
            assert re.match(expected, result.output)
        else:
            assert result.output == repr(
                named_tempfile.name if expected == "foo.conf" else expected
            )


class EngineType(enum.Enum):
    OSS = enum.auto()
    PRO = enum.auto()
    MAX = enum.auto()


class Class1:
    pass


class Class2:
    pass


@pytest.mark.parametrize(
    ("opt_params", "args", "expected"),
    [
        # Check that the flag value is returned as-is when the option is passed, and
        # not normalized to a boolean, even if it is explicitly declared as a flag.
        ({"type": EngineType, "flag_value": None}, ["--pro"], None),
        (
            {"type": EngineType, "is_flag": True, "flag_value": None},
            ["--pro"],
            None,
        ),
        ({"type": EngineType, "flag_value": EngineType.OSS}, ["--pro"], EngineType.OSS),
        (
            {"type": EngineType, "is_flag": True, "flag_value": EngineType.OSS},
            ["--pro"],
            EngineType.OSS,
        ),
        (
            {"type": EngineType, "is_flag": True, "default": EngineType.OSS},
            ["--pro"],
            EngineType.OSS,
        ),
        # The default value is returned as-is when the option is not passed, whatever
        # the flag value.
        ({"type": EngineType, "flag_value": None}, [], None),
        ({"type": EngineType, "is_flag": True, "flag_value": None}, [], None),
        ({"type": EngineType, "flag_value": EngineType.OSS}, [], None),
        (
            {"type": EngineType, "is_flag": True, "flag_value": EngineType.OSS},
            [],
            None,
        ),
        (
            {"type": EngineType, "is_flag": True, "default": EngineType.OSS},
            [],
            EngineType.OSS,
        ),
        # The option has not enough parameters to be detected as flag-like, so it
        # requires an argument.
        (
            {"type": EngineType, "default": EngineType.OSS},
            ["--pro"],
            re.compile(re.escape("Error: Option '--pro' requires an argument.\n")),
        ),
        ({"type": EngineType, "default": EngineType.OSS}, [], EngineType.OSS),
        # If a flag value is set, it is returned instead of the default value.
        (
            {"type": EngineType, "flag_value": EngineType.OSS, "default": True},
            ["--pro"],
            EngineType.OSS,
        ),
        (
            {"type": EngineType, "flag_value": EngineType.OSS, "default": True},
            [],
            EngineType.OSS,
        ),
        # Type is not specified and default to string, so the default value is
        # returned as a string, even if it is a boolean. Also, defaults to the
        # flag_value instead of the default value to support legacy behavior.
        ({"flag_value": "1", "default": True}, [], "1"),
        ({"flag_value": "1", "default": 42}, [], "42"),
        ({"flag_value": EngineType.OSS, "default": True}, [], "EngineType.OSS"),
        ({"flag_value": EngineType.OSS, "default": 42}, [], "42"),
        # See: the result is the same if we force the type to be str.
        ({"type": str, "flag_value": 1, "default": True}, [], "1"),
        ({"type": str, "flag_value": 1, "default": 42}, [], "42"),
        ({"type": str, "flag_value": "1", "default": True}, [], "1"),
        ({"type": str, "flag_value": "1", "default": 42}, [], "42"),
        (
            {"type": str, "flag_value": EngineType.OSS, "default": True},
            [],
            "EngineType.OSS",
        ),
        ({"type": str, "flag_value": EngineType.OSS, "default": 42}, [], "42"),
        # But having the flag value set to integer is automaticcally recognized by
        # Click.
        ({"flag_value": 1, "default": True}, [], 1),
        ({"flag_value": 1, "default": 42}, [], 42),
        ({"type": int, "flag_value": 1, "default": True}, [], 1),
        ({"type": int, "flag_value": 1, "default": 42}, [], 42),
        ({"type": int, "flag_value": "1", "default": True}, [], 1),
        ({"type": int, "flag_value": "1", "default": 42}, [], 42),
    ],
)
def test_custom_type_flag_value_standalone_option(runner, opt_params, args, expected):
    """Test how the type and flag_value influence the returned value.

    Cover cases reported in:
    https://github.com/pallets/click/issues/3024#issuecomment-3146480714
    https://github.com/pallets/click/issues/2012#issuecomment-892437060
    """

    @click.command()
    @click.option("--pro", **opt_params)
    def scan(pro):
        click.echo(repr(pro), nl=False)

    result = runner.invoke(scan, args)
    if isinstance(expected, re.Pattern):
        assert re.match(expected, result.output)
    else:
        assert result.output == repr(expected)


@pytest.mark.parametrize(
    ("opt1_params", "opt2_params", "args", "expected"),
    [
        # Dual options sharing the same variable name, are not competitive, and the
        # flag value is returned as-is. Especially when the type is force to be
        # unprocessed.
        (
            {"flag_value": EngineType.OSS, "type": UNPROCESSED},
            {"flag_value": EngineType.PRO, "type": UNPROCESSED},
            [],
            None,
        ),
        (
            {"flag_value": EngineType.OSS, "type": UNPROCESSED},
            {"flag_value": EngineType.PRO, "type": UNPROCESSED},
            ["--opt1"],
            EngineType.OSS,
        ),
        (
            {"flag_value": EngineType.OSS, "type": UNPROCESSED},
            {"flag_value": EngineType.PRO, "type": UNPROCESSED},
            ["--opt2"],
            EngineType.PRO,
        ),
        # Check that passing exotic flag values like classes is supported, but are
        # rendered to strings when the type is not specified.
        (
            {"flag_value": Class1, "default": True},
            {"flag_value": Class2},
            [],
            re.compile(r"'<test_options.Class1 object at 0x[0-9A-Fa-f]+>'"),
        ),
        (
            {"flag_value": Class1, "default": True},
            {"flag_value": Class2},
            ["--opt1"],
            "<class 'test_options.Class1'>",
        ),
        (
            {"flag_value": Class1, "default": True},
            {"flag_value": Class2},
            ["--opt2"],
            "<class 'test_options.Class2'>",
        ),
        # Even the default is processed as a string.
        ({"flag_value": Class1, "default": "True"}, {"flag_value": Class2}, [], "True"),
        ({"flag_value": Class1, "default": None}, {"flag_value": Class2}, [], None),
        # To get the classes as-is, we need to specify the type as UNPROCESSED.
        (
            {"flag_value": Class1, "type": UNPROCESSED, "default": True},
            {"flag_value": Class2, "type": UNPROCESSED},
            [],
            re.compile(r"<test_options.Class1 object at 0x[0-9A-Fa-f]+>"),
        ),
        (
            {"flag_value": Class1, "type": UNPROCESSED, "default": True},
            {"flag_value": Class2, "type": UNPROCESSED},
            ["--opt1"],
            Class1,
        ),
        (
            {"flag_value": Class1, "type": UNPROCESSED, "default": True},
            {"flag_value": Class2, "type": UNPROCESSED},
            ["--opt2"],
            Class2,
        ),
        # Setting the default to a class, an instance of the class is returned instead
        # of the class itself, because the default is allowed to be callable (and
        # consummd). And this happens whatever the type is.
        (
            {"flag_value": Class1, "default": Class1},
            {"flag_value": Class2},
            [],
            re.compile(r"'<test_options.Class1 object at 0x[0-9A-Fa-f]+>'"),
        ),
        (
            {"flag_value": Class1, "default": Class2},
            {"flag_value": Class2},
            [],
            re.compile(r"'<test_options.Class2 object at 0x[0-9A-Fa-f]+>'"),
        ),
        (
            {"flag_value": Class1, "type": UNPROCESSED, "default": Class1},
            {"flag_value": Class2, "type": UNPROCESSED},
            [],
            re.compile(r"<test_options.Class1 object at 0x[0-9A-Fa-f]+>"),
        ),
        (
            {"flag_value": Class1, "type": UNPROCESSED, "default": Class2},
            {"flag_value": Class2, "type": UNPROCESSED},
            [],
            re.compile(r"<test_options.Class2 object at 0x[0-9A-Fa-f]+>"),
        ),
        # Having the flag value set to integer is automaticcally recognized by Click.
        (
            {"flag_value": 1, "default": True},
            {"flag_value": "1"},
            [],
            1,
        ),
        (
            {"flag_value": 1, "type": int, "default": True},
            {"flag_value": "1", "type": int},
            [],
            1,
        ),
    ],
)
def test_custom_type_flag_value_dual_options(
    runner, opt1_params, opt2_params, args, expected
):
    """Test how flag values are processed with dual options competing for the same
    variable name.

    Reproduce issues reported in:
    https://github.com/pallets/click/issues/3024#issuecomment-3146508536
    https://github.com/pallets/click/issues/2012#issue-946471049
    https://github.com/pallets/click/issues/2012#issuecomment-892437060
    """

    @click.command()
    @click.option("--opt1", "dual_option", **opt1_params)
    @click.option("--opt2", "dual_option", **opt2_params)
    def cli(dual_option):
        click.echo(repr(dual_option), nl=False)

    result = runner.invoke(cli, args)
    if isinstance(expected, re.Pattern):
        assert re.match(expected, result.output)
    else:
        assert result.output == repr(expected)


def test_custom_type_frozenset_flag_value(runner):
    """Check that frozenset is correctly handled as a type, a flag value and a default.

    Reproduces https://github.com/pallets/click/issues/2610
    """

    @click.command()
    @click.option(
        "--without-scm-ignore-files",
        "scm_ignore_files",
        is_flag=True,
        type=frozenset,
        flag_value=frozenset(),
        default=frozenset(["git"]),
    )
    def rcli(scm_ignore_files):
        click.echo(repr(scm_ignore_files), nl=False)

    result = runner.invoke(rcli)
    assert result.stdout == "frozenset({'git'})"
    assert result.exit_code == 0

    result = runner.invoke(rcli, ["--without-scm-ignore-files"])
    assert result.stdout == "frozenset()"
    assert result.exit_code == 0


@pytest.mark.parametrize(
    ("flag_type", "args", "expect_output"),
    [
        (str, [], "Default\n"),
        (str, ["--theflag"], "FlagValue\n"),
        (str, ["--theflag", "value"], "value\n"),
        (int, [], "0\n"),
        (int, ["--theflag"], "1\n"),
        (int, ["--theflag", "2"], "2\n"),
    ],
)
def test_flag_value_on_option_with_zero_or_one_args(flag_type, args, expect_output):
    """An option with flag_value and is_flag=False can be
    omitted or used with 0 or 1 args.

    Regression test for https://github.com/pallets/click/issues/3084
    """
    if flag_type is str:
        flagopt = click.option(
            "--theflag",
            type=str,
            is_flag=False,
            flag_value="FlagValue",
            default="Default",
        )
    elif flag_type is int:
        flagopt = click.option(
            "--theflag", type=int, is_flag=False, flag_value=1, default=0
        )
    else:
        raise NotImplementedError(flag_type)

    @click.command()
    @flagopt
    def cmd(theflag):
        click.echo(theflag)

    runner = CliRunner()
    result = runner.invoke(cmd, args)
    assert result.exit_code == 0
    assert result.output == expect_output

```
---

## tests/test_parser.py

```python
import pytest

import click
from click.parser import _OptionParser
from click.shell_completion import split_arg_string


@pytest.mark.parametrize(
    ("value", "expect"),
    [
        ("cli a b c", ["cli", "a", "b", "c"]),
        ("cli 'my file", ["cli", "my file"]),
        ("cli 'my file'", ["cli", "my file"]),
        ("cli my\\", ["cli", "my"]),
        ("cli my\\ file", ["cli", "my file"]),
    ],
)
def test_split_arg_string(value, expect):
    assert split_arg_string(value) == expect


def test_parser_default_prefixes():
    parser = _OptionParser()
    assert parser._opt_prefixes == {"-", "--"}


def test_parser_collects_prefixes():
    ctx = click.Context(click.Command("test"))
    parser = _OptionParser(ctx)
    click.Option("+p", is_flag=True).add_to_parser(parser, ctx)
    click.Option("!e", is_flag=True).add_to_parser(parser, ctx)
    assert parser._opt_prefixes == {"-", "--", "+", "!"}

```
---

## tests/test_shell_completion.py

```python
import textwrap
import warnings
from collections.abc import Mapping

import pytest

import click.shell_completion
from click.core import Argument
from click.core import Command
from click.core import Group
from click.core import Option
from click.shell_completion import add_completion_class
from click.shell_completion import CompletionItem
from click.shell_completion import ShellComplete
from click.types import Choice
from click.types import File
from click.types import Path


def _get_completions(cli, args, incomplete):
    comp = ShellComplete(cli, {}, cli.name, "_CLICK_COMPLETE")
    return comp.get_completions(args, incomplete)


def _get_words(cli, args, incomplete):
    return [c.value for c in _get_completions(cli, args, incomplete)]


def test_command():
    cli = Command("cli", params=[Option(["-t", "--test"])])
    assert _get_words(cli, [], "") == []
    assert _get_words(cli, [], "-") == ["-t", "--test", "--help"]
    assert _get_words(cli, [], "--") == ["--test", "--help"]
    assert _get_words(cli, [], "--t") == ["--test"]
    # -t has been seen, so --test isn't suggested
    assert _get_words(cli, ["-t", "a"], "-") == ["--help"]


def test_group():
    cli = Group("cli", params=[Option(["-a"])], commands=[Command("x"), Command("y")])
    assert _get_words(cli, [], "") == ["x", "y"]
    assert _get_words(cli, [], "-") == ["-a", "--help"]


@pytest.mark.parametrize(
    ("args", "word", "expect"),
    [
        ([], "", ["get"]),
        (["get"], "", ["full"]),
        (["get", "full"], "", ["data"]),
        (["get", "full"], "-", ["--verbose", "--help"]),
        (["get", "full", "data"], "", []),
        (["get", "full", "data"], "-", ["-a", "--help"]),
    ],
)
def test_nested_group(args: list[str], word: str, expect: list[str]) -> None:
    cli = Group(
        "cli",
        commands=[
            Group(
                "get",
                commands=[
                    Group(
                        "full",
                        params=[Option(["--verbose"])],
                        commands=[Command("data", params=[Option(["-a"])])],
                    )
                ],
            )
        ],
    )
    assert _get_words(cli, args, word) == expect


def test_group_command_same_option():
    cli = Group(
        "cli", params=[Option(["-a"])], commands=[Command("x", params=[Option(["-a"])])]
    )
    assert _get_words(cli, [], "-") == ["-a", "--help"]
    assert _get_words(cli, ["-a", "a"], "-") == ["--help"]
    assert _get_words(cli, ["-a", "a", "x"], "-") == ["-a", "--help"]
    assert _get_words(cli, ["-a", "a", "x", "-a", "a"], "-") == ["--help"]


def test_chained():
    cli = Group(
        "cli",
        chain=True,
        commands=[
            Command("set", params=[Option(["-y"])]),
            Command("start"),
            Group("get", commands=[Command("full")]),
        ],
    )
    assert _get_words(cli, [], "") == ["get", "set", "start"]
    assert _get_words(cli, [], "s") == ["set", "start"]
    assert _get_words(cli, ["set", "start"], "") == ["get"]
    # subcommands and parent subcommands
    assert _get_words(cli, ["get"], "") == ["full", "set", "start"]
    assert _get_words(cli, ["get", "full"], "") == ["set", "start"]
    assert _get_words(cli, ["get"], "s") == ["set", "start"]


def test_help_option():
    cli = Group("cli", commands=[Command("with"), Command("no", add_help_option=False)])
    assert _get_words(cli, ["with"], "--") == ["--help"]
    assert _get_words(cli, ["no"], "--") == []


def test_argument_order():
    cli = Command(
        "cli",
        params=[
            Argument(["plain"]),
            Argument(["c1"], type=Choice(["a1", "a2", "b"])),
            Argument(["c2"], type=Choice(["c1", "c2", "d"])),
        ],
    )
    # first argument has no completions
    assert _get_words(cli, [], "") == []
    assert _get_words(cli, [], "a") == []
    # first argument filled, now completion can happen
    assert _get_words(cli, ["x"], "a") == ["a1", "a2"]
    assert _get_words(cli, ["x", "b"], "d") == ["d"]


def test_argument_default():
    cli = Command(
        "cli",
        add_help_option=False,
        params=[
            Argument(["a"], type=Choice(["a"]), default="a"),
            Argument(["b"], type=Choice(["b"]), default="b"),
        ],
    )
    assert _get_words(cli, [], "") == ["a"]
    assert _get_words(cli, ["a"], "b") == ["b"]
    # ignore type validation
    assert _get_words(cli, ["x"], "b") == ["b"]


def test_type_choice():
    cli = Command("cli", params=[Option(["-c"], type=Choice(["a1", "a2", "b"]))])
    assert _get_words(cli, ["-c"], "") == ["a1", "a2", "b"]
    assert _get_words(cli, ["-c"], "a") == ["a1", "a2"]
    assert _get_words(cli, ["-c"], "a2") == ["a2"]


def test_choice_special_characters():
    cli = Command("cli", params=[Option(["-c"], type=Choice(["!1", "!2", "+3"]))])
    assert _get_words(cli, ["-c"], "") == ["!1", "!2", "+3"]
    assert _get_words(cli, ["-c"], "!") == ["!1", "!2"]
    assert _get_words(cli, ["-c"], "!2") == ["!2"]


def test_choice_conflicting_prefix():
    cli = Command(
        "cli",
        params=[
            Option(["-c"], type=Choice(["!1", "!2", "+3"])),
            Option(["+p"], is_flag=True),
        ],
    )
    assert _get_words(cli, ["-c"], "") == ["!1", "!2", "+3"]
    assert _get_words(cli, ["-c"], "+") == ["+p"]


def test_option_count():
    cli = Command("cli", params=[Option(["-c"], count=True)])
    assert _get_words(cli, ["-c"], "") == []
    assert _get_words(cli, ["-c"], "-") == ["--help"]


def test_option_optional():
    cli = Command(
        "cli",
        add_help_option=False,
        params=[
            Option(["--name"], is_flag=False, flag_value="value"),
            Option(["--flag"], is_flag=True),
        ],
    )
    assert _get_words(cli, ["--name"], "") == []
    assert _get_words(cli, ["--name"], "-") == ["--flag"]
    assert _get_words(cli, ["--name", "--flag"], "-") == []


@pytest.mark.parametrize(
    ("type", "expect"),
    [(File(), "file"), (Path(), "file"), (Path(file_okay=False), "dir")],
)
def test_path_types(type, expect):
    cli = Command("cli", params=[Option(["-f"], type=type)])
    out = _get_completions(cli, ["-f"], "ab")
    assert len(out) == 1
    c = out[0]
    assert c.value == "ab"
    assert c.type == expect


def test_absolute_path():
    cli = Command("cli", params=[Option(["-f"], type=Path())])
    out = _get_completions(cli, ["-f"], "/ab")
    assert len(out) == 1
    c = out[0]
    assert c.value == "/ab"


def test_option_flag():
    cli = Command(
        "cli",
        add_help_option=False,
        params=[
            Option(["--on/--off"]),
            Argument(["a"], type=Choice(["a1", "a2", "b"])),
        ],
    )
    assert _get_words(cli, [], "--") == ["--on", "--off"]
    # flag option doesn't take value, use choice argument
    assert _get_words(cli, ["--on"], "a") == ["a1", "a2"]


def test_flag_option_with_nargs_option():
    cli = Command(
        "cli",
        add_help_option=False,
        params=[
            Argument(["a"], type=Choice(["a1", "a2", "b"])),
            Option(["--flag"], is_flag=True),
            Option(["-c"], type=Choice(["p", "q"]), nargs=2),
        ],
    )
    assert _get_words(cli, ["a1", "--flag", "-c"], "") == ["p", "q"]


def test_option_custom():
    def custom(ctx, param, incomplete):
        return [incomplete.upper()]

    cli = Command(
        "cli",
        params=[
            Argument(["x"]),
            Argument(["y"]),
            Argument(["z"], shell_complete=custom),
        ],
    )
    assert _get_words(cli, ["a", "b"], "") == [""]
    assert _get_words(cli, ["a", "b"], "c") == ["C"]


def test_option_multiple():
    cli = Command(
        "type",
        params=[Option(["-m"], type=Choice(["a", "b"]), multiple=True), Option(["-f"])],
    )
    assert _get_words(cli, ["-m"], "") == ["a", "b"]
    assert "-m" in _get_words(cli, ["-m", "a"], "-")
    assert _get_words(cli, ["-m", "a", "-m"], "") == ["a", "b"]
    # used single options aren't suggested again
    assert "-c" not in _get_words(cli, ["-c", "f"], "-")


def test_option_nargs():
    cli = Command("cli", params=[Option(["-c"], type=Choice(["a", "b"]), nargs=2)])
    assert _get_words(cli, ["-c"], "") == ["a", "b"]
    assert _get_words(cli, ["-c", "a"], "") == ["a", "b"]
    assert _get_words(cli, ["-c", "a", "b"], "") == []


def test_argument_nargs():
    cli = Command(
        "cli",
        params=[
            Argument(["x"], type=Choice(["a", "b"]), nargs=2),
            Argument(["y"], type=Choice(["c", "d"]), nargs=-1),
            Option(["-z"]),
        ],
    )
    assert _get_words(cli, [], "") == ["a", "b"]
    assert _get_words(cli, ["a"], "") == ["a", "b"]
    assert _get_words(cli, ["a", "b"], "") == ["c", "d"]
    assert _get_words(cli, ["a", "b", "c"], "") == ["c", "d"]
    assert _get_words(cli, ["a", "b", "c", "d"], "") == ["c", "d"]
    assert _get_words(cli, ["a", "-z", "1"], "") == ["a", "b"]
    assert _get_words(cli, ["a", "-z", "1", "b"], "") == ["c", "d"]


def test_double_dash():
    cli = Command(
        "cli",
        add_help_option=False,
        params=[
            Option(["--opt"]),
            Argument(["name"], type=Choice(["name", "--", "-o", "--opt"])),
        ],
    )
    assert _get_words(cli, [], "-") == ["--opt"]
    assert _get_words(cli, ["value"], "-") == ["--opt"]
    assert _get_words(cli, [], "") == ["name", "--", "-o", "--opt"]
    assert _get_words(cli, ["--"], "") == ["name", "--", "-o", "--opt"]


def test_hidden():
    cli = Group(
        "cli",
        commands=[
            Command(
                "hidden",
                add_help_option=False,
                hidden=True,
                params=[
                    Option(["-a"]),
                    Option(["-b"], type=Choice(["a", "b"]), hidden=True),
                ],
            )
        ],
    )
    assert "hidden" not in _get_words(cli, [], "")
    assert "hidden" not in _get_words(cli, [], "hidden")
    assert _get_words(cli, ["hidden"], "-") == ["-a"]
    assert _get_words(cli, ["hidden", "-b"], "") == ["a", "b"]


def test_add_different_name():
    cli = Group("cli", commands={"renamed": Command("original")})
    words = _get_words(cli, [], "")
    assert "renamed" in words
    assert "original" not in words


def test_completion_item_data():
    c = CompletionItem("test", a=1)
    assert c.a == 1
    assert c.b is None


@pytest.fixture()
def _patch_for_completion(monkeypatch):
    monkeypatch.setattr(
        "click.shell_completion.BashComplete._check_version", lambda self: True
    )


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
@pytest.mark.usefixtures("_patch_for_completion")
def test_full_source(runner, shell):
    cli = Group("cli", commands=[Command("a"), Command("b")])
    result = runner.invoke(cli, env={"_CLI_COMPLETE": f"{shell}_source"})
    assert f"_CLI_COMPLETE={shell}_complete" in result.output


@pytest.mark.parametrize(
    ("shell", "env", "expect"),
    [
        ("bash", {"COMP_WORDS": "", "COMP_CWORD": "0"}, "plain,a\nplain,b\n"),
        ("bash", {"COMP_WORDS": "a b", "COMP_CWORD": "1"}, "plain,b\n"),
        ("zsh", {"COMP_WORDS": "", "COMP_CWORD": "0"}, "plain\na\n_\nplain\nb\nbee\n"),
        ("zsh", {"COMP_WORDS": "a b", "COMP_CWORD": "1"}, "plain\nb\nbee\n"),
        ("fish", {"COMP_WORDS": "", "COMP_CWORD": ""}, "plain,a\nplain,b\tbee\n"),
        ("fish", {"COMP_WORDS": "a b", "COMP_CWORD": "b"}, "plain,b\tbee\n"),
        ("fish", {"COMP_WORDS": 'a "b', "COMP_CWORD": '"b'}, "plain,b\tbee\n"),
    ],
)
@pytest.mark.usefixtures("_patch_for_completion")
def test_full_complete(runner, shell, env, expect):
    cli = Group("cli", commands=[Command("a"), Command("b", help="bee")])
    env["_CLI_COMPLETE"] = f"{shell}_complete"
    result = runner.invoke(cli, env=env)
    assert result.output == expect


@pytest.mark.parametrize(
    ("env", "expect"),
    [
        (
            {"COMP_WORDS": "", "COMP_CWORD": "0"},
            textwrap.dedent(
                """\
                    plain
                    a
                    _
                    plain
                    b
                    bee
                    plain
                    c\\:d
                    cee:dee
                    plain
                    c:e
                    _
                """
            ),
        ),
        (
            {"COMP_WORDS": "a c", "COMP_CWORD": "1"},
            textwrap.dedent(
                """\
                    plain
                    c\\:d
                    cee:dee
                    plain
                    c:e
                    _
                """
            ),
        ),
        (
            {"COMP_WORDS": "a c:", "COMP_CWORD": "1"},
            textwrap.dedent(
                """\
                    plain
                    c\\:d
                    cee:dee
                    plain
                    c:e
                    _
                """
            ),
        ),
    ],
)
@pytest.mark.usefixtures("_patch_for_completion")
def test_zsh_full_complete_with_colons(
    runner, env: Mapping[str, str], expect: str
) -> None:
    cli = Group(
        "cli",
        commands=[
            Command("a"),
            Command("b", help="bee"),
            Command("c:d", help="cee:dee"),
            Command("c:e"),
        ],
    )
    result = runner.invoke(
        cli,
        env={
            **env,
            "_CLI_COMPLETE": "zsh_complete",
        },
    )
    assert result.output == expect


@pytest.mark.usefixtures("_patch_for_completion")
def test_context_settings(runner):
    def complete(ctx, param, incomplete):
        return ctx.obj["choices"]

    cli = Command("cli", params=[Argument("x", shell_complete=complete)])
    result = runner.invoke(
        cli,
        obj={"choices": ["a", "b"]},
        env={"COMP_WORDS": "", "COMP_CWORD": "0", "_CLI_COMPLETE": "bash_complete"},
    )
    assert result.output == "plain,a\nplain,b\n"


@pytest.mark.parametrize(("value", "expect"), [(False, ["Au", "al"]), (True, ["al"])])
def test_choice_case_sensitive(value, expect):
    cli = Command(
        "cli",
        params=[Option(["-a"], type=Choice(["Au", "al", "Bc"], case_sensitive=value))],
    )
    completions = _get_words(cli, ["-a"], "a")
    assert completions == expect


@pytest.fixture()
def _restore_available_shells(tmpdir):
    prev_available_shells = click.shell_completion._available_shells.copy()
    click.shell_completion._available_shells.clear()
    yield
    click.shell_completion._available_shells.clear()
    click.shell_completion._available_shells.update(prev_available_shells)


@pytest.mark.usefixtures("_restore_available_shells")
def test_add_completion_class():
    # At first, "mysh" is not in available shells
    assert "mysh" not in click.shell_completion._available_shells

    class MyshComplete(ShellComplete):
        name = "mysh"
        source_template = "dummy source"

    # "mysh" still not in available shells because it is not registered
    assert "mysh" not in click.shell_completion._available_shells

    # Adding a completion class should return that class
    assert add_completion_class(MyshComplete) is MyshComplete

    # Now, "mysh" is finally in available shells
    assert "mysh" in click.shell_completion._available_shells
    assert click.shell_completion._available_shells["mysh"] is MyshComplete


@pytest.mark.usefixtures("_restore_available_shells")
def test_add_completion_class_with_name():
    # At first, "mysh" is not in available shells
    assert "mysh" not in click.shell_completion._available_shells
    assert "not_mysh" not in click.shell_completion._available_shells

    class MyshComplete(ShellComplete):
        name = "not_mysh"
        source_template = "dummy source"

    # "mysh" and "not_mysh" are still not in available shells because
    # it is not registered yet
    assert "mysh" not in click.shell_completion._available_shells
    assert "not_mysh" not in click.shell_completion._available_shells

    # Adding a completion class should return that class.
    # Because we are using the "name" parameter, the name isn't taken
    # from the class.
    assert add_completion_class(MyshComplete, name="mysh") is MyshComplete

    # Now, "mysh" is finally in available shells
    assert "mysh" in click.shell_completion._available_shells
    assert "not_mysh" not in click.shell_completion._available_shells
    assert click.shell_completion._available_shells["mysh"] is MyshComplete


@pytest.mark.usefixtures("_restore_available_shells")
def test_add_completion_class_decorator():
    # At first, "mysh" is not in available shells
    assert "mysh" not in click.shell_completion._available_shells

    @add_completion_class
    class MyshComplete(ShellComplete):
        name = "mysh"
        source_template = "dummy source"

    # Using `add_completion_class` as a decorator adds the new shell immediately
    assert "mysh" in click.shell_completion._available_shells
    assert click.shell_completion._available_shells["mysh"] is MyshComplete


# Don't make the ResourceWarning give an error
@pytest.mark.filterwarnings("default")
def test_files_closed(runner) -> None:
    with runner.isolated_filesystem():
        config_file = "foo.txt"
        with open(config_file, "w") as f:
            f.write("bar")

        @click.group()
        @click.option(
            "--config-file",
            default=config_file,
            type=click.File(mode="r"),
        )
        @click.pass_context
        def cli(ctx, config_file):
            pass

        with warnings.catch_warnings(record=True) as current_warnings:
            assert not current_warnings, "There should be no warnings to start"
            _get_completions(cli, args=[], incomplete="")
            assert not current_warnings, "There should be no warnings after either"

```
---

## tests/test_termui.py

```python
import platform
import tempfile
import time

import pytest

import click._termui_impl
from click._compat import WIN
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

        # We need ot reopen the file as it becomes unreadable after the edit.
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
    ({"prompt": True, "default": True, "flag_value": False}, [], "[y/N]", "", False),
    ({"prompt": True, "default": True, "flag_value": False}, [], "[y/N]", "y", True),
    ({"prompt": True, "default": True, "flag_value": False}, [], "[y/N]", "n", False),
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

```
---

## tests/test_testing.py

```python
import os
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
    # The spacial case is seen with rootless Podman. The root cause is most
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
