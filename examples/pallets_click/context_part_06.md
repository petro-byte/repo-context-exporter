# Repository Context Part 6/9

Generated for LLM prompt context.

## src/click/testing.py

```python
from __future__ import annotations

import collections.abc as cabc
import contextlib
import io
import os
import shlex
import sys
import tempfile
import typing as t
from types import TracebackType

from . import _compat
from . import formatting
from . import termui
from . import utils
from ._compat import _find_binary_reader

if t.TYPE_CHECKING:
    from _typeshed import ReadableBuffer

    from .core import Command


class EchoingStdin:
    def __init__(self, input: t.BinaryIO, output: t.BinaryIO) -> None:
        self._input = input
        self._output = output
        self._paused = False

    def __getattr__(self, x: str) -> t.Any:
        return getattr(self._input, x)

    def _echo(self, rv: bytes) -> bytes:
        if not self._paused:
            self._output.write(rv)

        return rv

    def read(self, n: int = -1) -> bytes:
        return self._echo(self._input.read(n))

    def read1(self, n: int = -1) -> bytes:
        return self._echo(self._input.read1(n))  # type: ignore

    def readline(self, n: int = -1) -> bytes:
        return self._echo(self._input.readline(n))

    def readlines(self) -> list[bytes]:
        return [self._echo(x) for x in self._input.readlines()]

    def __iter__(self) -> cabc.Iterator[bytes]:
        return iter(self._echo(x) for x in self._input)

    def __repr__(self) -> str:
        return repr(self._input)


@contextlib.contextmanager
def _pause_echo(stream: EchoingStdin | None) -> cabc.Iterator[None]:
    if stream is None:
        yield
    else:
        stream._paused = True
        yield
        stream._paused = False


class BytesIOCopy(io.BytesIO):
    """Patch ``io.BytesIO`` to let the written stream be copied to another.

    .. versionadded:: 8.2
    """

    def __init__(self, copy_to: io.BytesIO) -> None:
        super().__init__()
        self.copy_to = copy_to

    def flush(self) -> None:
        super().flush()
        self.copy_to.flush()

    def write(self, b: ReadableBuffer) -> int:
        self.copy_to.write(b)
        return super().write(b)


class StreamMixer:
    """Mixes `<stdout>` and `<stderr>` streams.

    The result is available in the ``output`` attribute.

    .. versionadded:: 8.2
    """

    def __init__(self) -> None:
        self.output: io.BytesIO = io.BytesIO()
        self.stdout: io.BytesIO = BytesIOCopy(copy_to=self.output)
        self.stderr: io.BytesIO = BytesIOCopy(copy_to=self.output)

    def __del__(self) -> None:
        """
        Guarantee that embedded file-like objects are closed in a
        predictable order, protecting against races between
        self.output being closed and other streams being flushed on close

        .. versionadded:: 8.2.2
        """
        self.stderr.close()
        self.stdout.close()
        self.output.close()


class _NamedTextIOWrapper(io.TextIOWrapper):
    def __init__(
        self, buffer: t.BinaryIO, name: str, mode: str, **kwargs: t.Any
    ) -> None:
        super().__init__(buffer, **kwargs)
        self._name = name
        self._mode = mode

    @property
    def name(self) -> str:
        return self._name

    @property
    def mode(self) -> str:
        return self._mode


def make_input_stream(
    input: str | bytes | t.IO[t.Any] | None, charset: str
) -> t.BinaryIO:
    # Is already an input stream.
    if hasattr(input, "read"):
        rv = _find_binary_reader(t.cast("t.IO[t.Any]", input))

        if rv is not None:
            return rv

        raise TypeError("Could not find binary reader for input stream.")

    if input is None:
        input = b""
    elif isinstance(input, str):
        input = input.encode(charset)

    return io.BytesIO(input)


class Result:
    """Holds the captured result of an invoked CLI script.

    :param runner: The runner that created the result
    :param stdout_bytes: The standard output as bytes.
    :param stderr_bytes: The standard error as bytes.
    :param output_bytes: A mix of ``stdout_bytes`` and ``stderr_bytes``, as the
        user would see  it in its terminal.
    :param return_value: The value returned from the invoked command.
    :param exit_code: The exit code as integer.
    :param exception: The exception that happened if one did.
    :param exc_info: Exception information (exception type, exception instance,
        traceback type).

    .. versionchanged:: 8.2
        ``stderr_bytes`` no longer optional, ``output_bytes`` introduced and
        ``mix_stderr`` has been removed.

    .. versionadded:: 8.0
        Added ``return_value``.
    """

    def __init__(
        self,
        runner: CliRunner,
        stdout_bytes: bytes,
        stderr_bytes: bytes,
        output_bytes: bytes,
        return_value: t.Any,
        exit_code: int,
        exception: BaseException | None,
        exc_info: tuple[type[BaseException], BaseException, TracebackType]
        | None = None,
    ):
        self.runner = runner
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self.output_bytes = output_bytes
        self.return_value = return_value
        self.exit_code = exit_code
        self.exception = exception
        self.exc_info = exc_info

    @property
    def output(self) -> str:
        """The terminal output as unicode string, as the user would see it.

        .. versionchanged:: 8.2
            No longer a proxy for ``self.stdout``. Now has its own independent stream
            that is mixing `<stdout>` and `<stderr>`, in the order they were written.
        """
        return self.output_bytes.decode(self.runner.charset, "replace").replace(
            "\r\n", "\n"
        )

    @property
    def stdout(self) -> str:
        """The standard output as unicode string."""
        return self.stdout_bytes.decode(self.runner.charset, "replace").replace(
            "\r\n", "\n"
        )

    @property
    def stderr(self) -> str:
        """The standard error as unicode string.

        .. versionchanged:: 8.2
            No longer raise an exception, always returns the `<stderr>` string.
        """
        return self.stderr_bytes.decode(self.runner.charset, "replace").replace(
            "\r\n", "\n"
        )

    def __repr__(self) -> str:
        exc_str = repr(self.exception) if self.exception else "okay"
        return f"<{type(self).__name__} {exc_str}>"


class CliRunner:
    """The CLI runner provides functionality to invoke a Click command line
    script for unittesting purposes in a isolated environment.  This only
    works in single-threaded systems without any concurrency as it changes the
    global interpreter state.

    :param charset: the character set for the input and output data.
    :param env: a dictionary with environment variables for overriding.
    :param echo_stdin: if this is set to `True`, then reading from `<stdin>` writes
                       to `<stdout>`.  This is useful for showing examples in
                       some circumstances.  Note that regular prompts
                       will automatically echo the input.
    :param catch_exceptions: Whether to catch any exceptions other than
                             ``SystemExit`` when running :meth:`~CliRunner.invoke`.

    .. versionchanged:: 8.2
        Added the ``catch_exceptions`` parameter.

    .. versionchanged:: 8.2
        ``mix_stderr`` parameter has been removed.
    """

    def __init__(
        self,
        charset: str = "utf-8",
        env: cabc.Mapping[str, str | None] | None = None,
        echo_stdin: bool = False,
        catch_exceptions: bool = True,
    ) -> None:
        self.charset = charset
        self.env: cabc.Mapping[str, str | None] = env or {}
        self.echo_stdin = echo_stdin
        self.catch_exceptions = catch_exceptions

    def get_default_prog_name(self, cli: Command) -> str:
        """Given a command object it will return the default program name
        for it.  The default is the `name` attribute or ``"root"`` if not
        set.
        """
        return cli.name or "root"

    def make_env(
        self, overrides: cabc.Mapping[str, str | None] | None = None
    ) -> cabc.Mapping[str, str | None]:
        """Returns the environment overrides for invoking a script."""
        rv = dict(self.env)
        if overrides:
            rv.update(overrides)
        return rv

    @contextlib.contextmanager
    def isolation(
        self,
        input: str | bytes | t.IO[t.Any] | None = None,
        env: cabc.Mapping[str, str | None] | None = None,
        color: bool = False,
    ) -> cabc.Iterator[tuple[io.BytesIO, io.BytesIO, io.BytesIO]]:
        """A context manager that sets up the isolation for invoking of a
        command line tool.  This sets up `<stdin>` with the given input data
        and `os.environ` with the overrides from the given dictionary.
        This also rebinds some internals in Click to be mocked (like the
        prompt functionality).

        This is automatically done in the :meth:`invoke` method.

        :param input: the input stream to put into `sys.stdin`.
        :param env: the environment overrides as dictionary.
        :param color: whether the output should contain color codes. The
                      application can still override this explicitly.

        .. versionadded:: 8.2
            An additional output stream is returned, which is a mix of
            `<stdout>` and `<stderr>` streams.

        .. versionchanged:: 8.2
            Always returns the `<stderr>` stream.

        .. versionchanged:: 8.0
            `<stderr>` is opened with ``errors="backslashreplace"``
            instead of the default ``"strict"``.

        .. versionchanged:: 4.0
            Added the ``color`` parameter.
        """
        bytes_input = make_input_stream(input, self.charset)
        echo_input = None

        old_stdin = sys.stdin
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_forced_width = formatting.FORCED_WIDTH
        formatting.FORCED_WIDTH = 80

        env = self.make_env(env)

        stream_mixer = StreamMixer()

        if self.echo_stdin:
            bytes_input = echo_input = t.cast(
                t.BinaryIO, EchoingStdin(bytes_input, stream_mixer.stdout)
            )

        sys.stdin = text_input = _NamedTextIOWrapper(
            bytes_input, encoding=self.charset, name="<stdin>", mode="r"
        )

        if self.echo_stdin:
            # Force unbuffered reads, otherwise TextIOWrapper reads a
            # large chunk which is echoed early.
            text_input._CHUNK_SIZE = 1  # type: ignore

        sys.stdout = _NamedTextIOWrapper(
            stream_mixer.stdout, encoding=self.charset, name="<stdout>", mode="w"
        )

        sys.stderr = _NamedTextIOWrapper(
            stream_mixer.stderr,
            encoding=self.charset,
            name="<stderr>",
            mode="w",
            errors="backslashreplace",
        )

        @_pause_echo(echo_input)  # type: ignore
        def visible_input(prompt: str | None = None) -> str:
            sys.stdout.write(prompt or "")
            try:
                val = next(text_input).rstrip("\r\n")
            except StopIteration as e:
                raise EOFError() from e
            sys.stdout.write(f"{val}\n")
            sys.stdout.flush()
            return val

        @_pause_echo(echo_input)  # type: ignore
        def hidden_input(prompt: str | None = None) -> str:
            sys.stdout.write(f"{prompt or ''}\n")
            sys.stdout.flush()
            try:
                return next(text_input).rstrip("\r\n")
            except StopIteration as e:
                raise EOFError() from e

        @_pause_echo(echo_input)  # type: ignore
        def _getchar(echo: bool) -> str:
            char = sys.stdin.read(1)

            if echo:
                sys.stdout.write(char)

            sys.stdout.flush()
            return char

        default_color = color

        def should_strip_ansi(
            stream: t.IO[t.Any] | None = None, color: bool | None = None
        ) -> bool:
            if color is None:
                return not default_color
            return not color

        old_visible_prompt_func = termui.visible_prompt_func
        old_hidden_prompt_func = termui.hidden_prompt_func
        old__getchar_func = termui._getchar
        old_should_strip_ansi = utils.should_strip_ansi  # type: ignore
        old__compat_should_strip_ansi = _compat.should_strip_ansi
        termui.visible_prompt_func = visible_input
        termui.hidden_prompt_func = hidden_input
        termui._getchar = _getchar
        utils.should_strip_ansi = should_strip_ansi  # type: ignore
        _compat.should_strip_ansi = should_strip_ansi

        old_env = {}
        try:
            for key, value in env.items():
                old_env[key] = os.environ.get(key)
                if value is None:
                    try:
                        del os.environ[key]
                    except Exception:
                        pass
                else:
                    os.environ[key] = value
            yield (stream_mixer.stdout, stream_mixer.stderr, stream_mixer.output)
        finally:
            for key, value in old_env.items():
                if value is None:
                    try:
                        del os.environ[key]
                    except Exception:
                        pass
                else:
                    os.environ[key] = value
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin
            termui.visible_prompt_func = old_visible_prompt_func
            termui.hidden_prompt_func = old_hidden_prompt_func
            termui._getchar = old__getchar_func
            utils.should_strip_ansi = old_should_strip_ansi  # type: ignore
            _compat.should_strip_ansi = old__compat_should_strip_ansi
            formatting.FORCED_WIDTH = old_forced_width

    def invoke(
        self,
        cli: Command,
        args: str | cabc.Sequence[str] | None = None,
        input: str | bytes | t.IO[t.Any] | None = None,
        env: cabc.Mapping[str, str | None] | None = None,
        catch_exceptions: bool | None = None,
        color: bool = False,
        **extra: t.Any,
    ) -> Result:
        """Invokes a command in an isolated environment.  The arguments are
        forwarded directly to the command line script, the `extra` keyword
        arguments are passed to the :meth:`~clickpkg.Command.main` function of
        the command.

        This returns a :class:`Result` object.

        :param cli: the command to invoke
        :param args: the arguments to invoke. It may be given as an iterable
                     or a string. When given as string it will be interpreted
                     as a Unix shell command. More details at
                     :func:`shlex.split`.
        :param input: the input data for `sys.stdin`.
        :param env: the environment overrides.
        :param catch_exceptions: Whether to catch any other exceptions than
                                 ``SystemExit``. If :data:`None`, the value
                                 from :class:`CliRunner` is used.
        :param extra: the keyword arguments to pass to :meth:`main`.
        :param color: whether the output should contain color codes. The
                      application can still override this explicitly.

        .. versionadded:: 8.2
            The result object has the ``output_bytes`` attribute with
            the mix of ``stdout_bytes`` and ``stderr_bytes``, as the user would
            see it in its terminal.

        .. versionchanged:: 8.2
            The result object always returns the ``stderr_bytes`` stream.

        .. versionchanged:: 8.0
            The result object has the ``return_value`` attribute with
            the value returned from the invoked command.

        .. versionchanged:: 4.0
            Added the ``color`` parameter.

        .. versionchanged:: 3.0
            Added the ``catch_exceptions`` parameter.

        .. versionchanged:: 3.0
            The result object has the ``exc_info`` attribute with the
            traceback if available.
        """
        exc_info = None
        if catch_exceptions is None:
            catch_exceptions = self.catch_exceptions

        with self.isolation(input=input, env=env, color=color) as outstreams:
            return_value = None
            exception: BaseException | None = None
            exit_code = 0

            if isinstance(args, str):
                args = shlex.split(args)

            try:
                prog_name = extra.pop("prog_name")
            except KeyError:
                prog_name = self.get_default_prog_name(cli)

            try:
                return_value = cli.main(args=args or (), prog_name=prog_name, **extra)
            except SystemExit as e:
                exc_info = sys.exc_info()
                e_code = t.cast("int | t.Any | None", e.code)

                if e_code is None:
                    e_code = 0

                if e_code != 0:
                    exception = e

                if not isinstance(e_code, int):
                    sys.stdout.write(str(e_code))
                    sys.stdout.write("\n")
                    e_code = 1

                exit_code = e_code

            except Exception as e:
                if not catch_exceptions:
                    raise
                exception = e
                exit_code = 1
                exc_info = sys.exc_info()
            finally:
                sys.stdout.flush()
                sys.stderr.flush()
                stdout = outstreams[0].getvalue()
                stderr = outstreams[1].getvalue()
                output = outstreams[2].getvalue()

        return Result(
            runner=self,
            stdout_bytes=stdout,
            stderr_bytes=stderr,
            output_bytes=output,
            return_value=return_value,
            exit_code=exit_code,
            exception=exception,
            exc_info=exc_info,  # type: ignore
        )

    @contextlib.contextmanager
    def isolated_filesystem(
        self, temp_dir: str | os.PathLike[str] | None = None
    ) -> cabc.Iterator[str]:
        """A context manager that creates a temporary directory and
        changes the current working directory to it. This isolates tests
        that affect the contents of the CWD to prevent them from
        interfering with each other.

        :param temp_dir: Create the temporary directory under this
            directory. If given, the created directory is not removed
            when exiting.

        .. versionchanged:: 8.0
            Added the ``temp_dir`` parameter.
        """
        cwd = os.getcwd()
        dt = tempfile.mkdtemp(dir=temp_dir)
        os.chdir(dt)

        try:
            yield dt
        finally:
            os.chdir(cwd)

            if temp_dir is None:
                import shutil

                try:
                    shutil.rmtree(dt)
                except OSError:
                    pass

```
---

## src/click/types.py

```python
from __future__ import annotations

import collections.abc as cabc
import enum
import os
import stat
import sys
import typing as t
from datetime import datetime
from gettext import gettext as _
from gettext import ngettext

from ._compat import _get_argv_encoding
from ._compat import open_stream
from .exceptions import BadParameter
from .utils import format_filename
from .utils import LazyFile
from .utils import safecall

if t.TYPE_CHECKING:
    import typing_extensions as te

    from .core import Context
    from .core import Parameter
    from .shell_completion import CompletionItem

ParamTypeValue = t.TypeVar("ParamTypeValue")


class ParamType:
    """Represents the type of a parameter. Validates and converts values
    from the command line or Python into the correct type.

    To implement a custom type, subclass and implement at least the
    following:

    -   The :attr:`name` class attribute must be set.
    -   Calling an instance of the type with ``None`` must return
        ``None``. This is already implemented by default.
    -   :meth:`convert` must convert string values to the correct type.
    -   :meth:`convert` must accept values that are already the correct
        type.
    -   It must be able to convert a value if the ``ctx`` and ``param``
        arguments are ``None``. This can occur when converting prompt
        input.
    """

    is_composite: t.ClassVar[bool] = False
    arity: t.ClassVar[int] = 1

    #: the descriptive name of this type
    name: str

    #: if a list of this type is expected and the value is pulled from a
    #: string environment variable, this is what splits it up.  `None`
    #: means any whitespace.  For all parameters the general rule is that
    #: whitespace splits them up.  The exception are paths and files which
    #: are split by ``os.path.pathsep`` by default (":" on Unix and ";" on
    #: Windows).
    envvar_list_splitter: t.ClassVar[str | None] = None

    def to_info_dict(self) -> dict[str, t.Any]:
        """Gather information that could be useful for a tool generating
        user-facing documentation.

        Use :meth:`click.Context.to_info_dict` to traverse the entire
        CLI structure.

        .. versionadded:: 8.0
        """
        # The class name without the "ParamType" suffix.
        param_type = type(self).__name__.partition("ParamType")[0]
        param_type = param_type.partition("ParameterType")[0]

        # Custom subclasses might not remember to set a name.
        if hasattr(self, "name"):
            name = self.name
        else:
            name = param_type

        return {"param_type": param_type, "name": name}

    def __call__(
        self,
        value: t.Any,
        param: Parameter | None = None,
        ctx: Context | None = None,
    ) -> t.Any:
        if value is not None:
            return self.convert(value, param, ctx)

    def get_metavar(self, param: Parameter, ctx: Context) -> str | None:
        """Returns the metavar default for this param if it provides one."""

    def get_missing_message(self, param: Parameter, ctx: Context | None) -> str | None:
        """Optionally might return extra information about a missing
        parameter.

        .. versionadded:: 2.0
        """

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        """Convert the value to the correct type. This is not called if
        the value is ``None`` (the missing value).

        This must accept string values from the command line, as well as
        values that are already the correct type. It may also convert
        other compatible types.

        The ``param`` and ``ctx`` arguments may be ``None`` in certain
        situations, such as when converting prompt input.

        If the value cannot be converted, call :meth:`fail` with a
        descriptive message.

        :param value: The value to convert.
        :param param: The parameter that is using this type to convert
            its value. May be ``None``.
        :param ctx: The current context that arrived at this value. May
            be ``None``.
        """
        return value

    def split_envvar_value(self, rv: str) -> cabc.Sequence[str]:
        """Given a value from an environment variable this splits it up
        into small chunks depending on the defined envvar list splitter.

        If the splitter is set to `None`, which means that whitespace splits,
        then leading and trailing whitespace is ignored.  Otherwise, leading
        and trailing splitters usually lead to empty items being included.
        """
        return (rv or "").split(self.envvar_list_splitter)

    def fail(
        self,
        message: str,
        param: Parameter | None = None,
        ctx: Context | None = None,
    ) -> t.NoReturn:
        """Helper method to fail with an invalid value message."""
        raise BadParameter(message, ctx=ctx, param=param)

    def shell_complete(
        self, ctx: Context, param: Parameter, incomplete: str
    ) -> list[CompletionItem]:
        """Return a list of
        :class:`~click.shell_completion.CompletionItem` objects for the
        incomplete value. Most types do not provide completions, but
        some do, and this allows custom types to provide custom
        completions as well.

        :param ctx: Invocation context for this command.
        :param param: The parameter that is requesting completion.
        :param incomplete: Value being completed. May be empty.

        .. versionadded:: 8.0
        """
        return []


class CompositeParamType(ParamType):
    is_composite = True

    @property
    def arity(self) -> int:  # type: ignore
        raise NotImplementedError()


class FuncParamType(ParamType):
    def __init__(self, func: t.Callable[[t.Any], t.Any]) -> None:
        self.name: str = func.__name__
        self.func = func

    def to_info_dict(self) -> dict[str, t.Any]:
        info_dict = super().to_info_dict()
        info_dict["func"] = self.func
        return info_dict

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        try:
            return self.func(value)
        except ValueError:
            try:
                value = str(value)
            except UnicodeError:
                value = value.decode("utf-8", "replace")

            self.fail(value, param, ctx)


class UnprocessedParamType(ParamType):
    name = "text"

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        return value

    def __repr__(self) -> str:
        return "UNPROCESSED"


class StringParamType(ParamType):
    name = "text"

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        if isinstance(value, bytes):
            enc = _get_argv_encoding()
            try:
                value = value.decode(enc)
            except UnicodeError:
                fs_enc = sys.getfilesystemencoding()
                if fs_enc != enc:
                    try:
                        value = value.decode(fs_enc)
                    except UnicodeError:
                        value = value.decode("utf-8", "replace")
                else:
                    value = value.decode("utf-8", "replace")
            return value
        return str(value)

    def __repr__(self) -> str:
        return "STRING"


class Choice(ParamType, t.Generic[ParamTypeValue]):
    """The choice type allows a value to be checked against a fixed set
    of supported values.

    You may pass any iterable value which will be converted to a tuple
    and thus will only be iterated once.

    The resulting value will always be one of the originally passed choices.
    See :meth:`normalize_choice` for more info on the mapping of strings
    to choices. See :ref:`choice-opts` for an example.

    :param case_sensitive: Set to false to make choices case
        insensitive. Defaults to true.

    .. versionchanged:: 8.2.0
        Non-``str`` ``choices`` are now supported. It can additionally be any
        iterable. Before you were not recommended to pass anything but a list or
        tuple.

    .. versionadded:: 8.2.0
        Choice normalization can be overridden via :meth:`normalize_choice`.
    """

    name = "choice"

    def __init__(
        self, choices: cabc.Iterable[ParamTypeValue], case_sensitive: bool = True
    ) -> None:
        self.choices: cabc.Sequence[ParamTypeValue] = tuple(choices)
        self.case_sensitive = case_sensitive

    def to_info_dict(self) -> dict[str, t.Any]:
        info_dict = super().to_info_dict()
        info_dict["choices"] = self.choices
        info_dict["case_sensitive"] = self.case_sensitive
        return info_dict

    def _normalized_mapping(
        self, ctx: Context | None = None
    ) -> cabc.Mapping[ParamTypeValue, str]:
        """
        Returns mapping where keys are the original choices and the values are
        the normalized values that are accepted via the command line.

        This is a simple wrapper around :meth:`normalize_choice`, use that
        instead which is supported.
        """
        return {
            choice: self.normalize_choice(
                choice=choice,
                ctx=ctx,
            )
            for choice in self.choices
        }

    def normalize_choice(self, choice: ParamTypeValue, ctx: Context | None) -> str:
        """
        Normalize a choice value, used to map a passed string to a choice.
        Each choice must have a unique normalized value.

        By default uses :meth:`Context.token_normalize_func` and if not case
        sensitive, convert it to a casefolded value.

        .. versionadded:: 8.2.0
        """
        normed_value = choice.name if isinstance(choice, enum.Enum) else str(choice)

        if ctx is not None and ctx.token_normalize_func is not None:
            normed_value = ctx.token_normalize_func(normed_value)

        if not self.case_sensitive:
            normed_value = normed_value.casefold()

        return normed_value

    def get_metavar(self, param: Parameter, ctx: Context) -> str | None:
        if param.param_type_name == "option" and not param.show_choices:  # type: ignore
            choice_metavars = [
                convert_type(type(choice)).name.upper() for choice in self.choices
            ]
            choices_str = "|".join([*dict.fromkeys(choice_metavars)])
        else:
            choices_str = "|".join(
                [str(i) for i in self._normalized_mapping(ctx=ctx).values()]
            )

        # Use curly braces to indicate a required argument.
        if param.required and param.param_type_name == "argument":
            return f"{{{choices_str}}}"

        # Use square braces to indicate an option or optional argument.
        return f"[{choices_str}]"

    def get_missing_message(self, param: Parameter, ctx: Context | None) -> str:
        """
        Message shown when no choice is passed.

        .. versionchanged:: 8.2.0 Added ``ctx`` argument.
        """
        return _("Choose from:\n\t{choices}").format(
            choices=",\n\t".join(self._normalized_mapping(ctx=ctx).values())
        )

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> ParamTypeValue:
        """
        For a given value from the parser, normalize it and find its
        matching normalized value in the list of choices. Then return the
        matched "original" choice.
        """
        normed_value = self.normalize_choice(choice=value, ctx=ctx)
        normalized_mapping = self._normalized_mapping(ctx=ctx)

        try:
            return next(
                original
                for original, normalized in normalized_mapping.items()
                if normalized == normed_value
            )
        except StopIteration:
            self.fail(
                self.get_invalid_choice_message(value=value, ctx=ctx),
                param=param,
                ctx=ctx,
            )

    def get_invalid_choice_message(self, value: t.Any, ctx: Context | None) -> str:
        """Get the error message when the given choice is invalid.

        :param value: The invalid value.

        .. versionadded:: 8.2
        """
        choices_str = ", ".join(map(repr, self._normalized_mapping(ctx=ctx).values()))
        return ngettext(
            "{value!r} is not {choice}.",
            "{value!r} is not one of {choices}.",
            len(self.choices),
        ).format(value=value, choice=choices_str, choices=choices_str)

    def __repr__(self) -> str:
        return f"Choice({list(self.choices)})"

    def shell_complete(
        self, ctx: Context, param: Parameter, incomplete: str
    ) -> list[CompletionItem]:
        """Complete choices that start with the incomplete value.

        :param ctx: Invocation context for this command.
        :param param: The parameter that is requesting completion.
        :param incomplete: Value being completed. May be empty.

        .. versionadded:: 8.0
        """
        from click.shell_completion import CompletionItem

        str_choices = map(str, self.choices)

        if self.case_sensitive:
            matched = (c for c in str_choices if c.startswith(incomplete))
        else:
            incomplete = incomplete.lower()
            matched = (c for c in str_choices if c.lower().startswith(incomplete))

        return [CompletionItem(c) for c in matched]


class DateTime(ParamType):
    """The DateTime type converts date strings into `datetime` objects.

    The format strings which are checked are configurable, but default to some
    common (non-timezone aware) ISO 8601 formats.

    When specifying *DateTime* formats, you should only pass a list or a tuple.
    Other iterables, like generators, may lead to surprising results.

    The format strings are processed using ``datetime.strptime``, and this
    consequently defines the format strings which are allowed.

    Parsing is tried using each format, in order, and the first format which
    parses successfully is used.

    :param formats: A list or tuple of date format strings, in the order in
                    which they should be tried. Defaults to
                    ``'%Y-%m-%d'``, ``'%Y-%m-%dT%H:%M:%S'``,
                    ``'%Y-%m-%d %H:%M:%S'``.
    """

    name = "datetime"

    def __init__(self, formats: cabc.Sequence[str] | None = None):
        self.formats: cabc.Sequence[str] = formats or [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

    def to_info_dict(self) -> dict[str, t.Any]:
        info_dict = super().to_info_dict()
        info_dict["formats"] = self.formats
        return info_dict

    def get_metavar(self, param: Parameter, ctx: Context) -> str | None:
        return f"[{'|'.join(self.formats)}]"

    def _try_to_convert_date(self, value: t.Any, format: str) -> datetime | None:
        try:
            return datetime.strptime(value, format)
        except ValueError:
            return None

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        if isinstance(value, datetime):
            return value

        for format in self.formats:
            converted = self._try_to_convert_date(value, format)

            if converted is not None:
                return converted

        formats_str = ", ".join(map(repr, self.formats))
        self.fail(
            ngettext(
                "{value!r} does not match the format {format}.",
                "{value!r} does not match the formats {formats}.",
                len(self.formats),
            ).format(value=value, format=formats_str, formats=formats_str),
            param,
            ctx,
        )

    def __repr__(self) -> str:
        return "DateTime"


class _NumberParamTypeBase(ParamType):
    _number_class: t.ClassVar[type[t.Any]]

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        try:
            return self._number_class(value)
        except ValueError:
            self.fail(
                _("{value!r} is not a valid {number_type}.").format(
                    value=value, number_type=self.name
                ),
                param,
                ctx,
            )


class _NumberRangeBase(_NumberParamTypeBase):
    def __init__(
        self,
        min: float | None = None,
        max: float | None = None,
        min_open: bool = False,
        max_open: bool = False,
        clamp: bool = False,
    ) -> None:
        self.min = min
        self.max = max
        self.min_open = min_open
        self.max_open = max_open
        self.clamp = clamp

    def to_info_dict(self) -> dict[str, t.Any]:
        info_dict = super().to_info_dict()
        info_dict.update(
            min=self.min,
            max=self.max,
            min_open=self.min_open,
            max_open=self.max_open,
            clamp=self.clamp,
        )
        return info_dict

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        import operator

        rv = super().convert(value, param, ctx)
        lt_min: bool = self.min is not None and (
            operator.le if self.min_open else operator.lt
        )(rv, self.min)
        gt_max: bool = self.max is not None and (
            operator.ge if self.max_open else operator.gt
        )(rv, self.max)

        if self.clamp:
            if lt_min:
                return self._clamp(self.min, 1, self.min_open)  # type: ignore

            if gt_max:
                return self._clamp(self.max, -1, self.max_open)  # type: ignore

        if lt_min or gt_max:
            self.fail(
                _("{value} is not in the range {range}.").format(
                    value=rv, range=self._describe_range()
                ),
                param,
                ctx,
            )

        return rv

    def _clamp(self, bound: float, dir: t.Literal[1, -1], open: bool) -> float:
        """Find the valid value to clamp to bound in the given
        direction.

        :param bound: The boundary value.
        :param dir: 1 or -1 indicating the direction to move.
        :param open: If true, the range does not include the bound.
        """
        raise NotImplementedError

    def _describe_range(self) -> str:
        """Describe the range for use in help text."""
        if self.min is None:
            op = "<" if self.max_open else "<="
            return f"x{op}{self.max}"

        if self.max is None:
            op = ">" if self.min_open else ">="
            return f"x{op}{self.min}"

        lop = "<" if self.min_open else "<="
        rop = "<" if self.max_open else "<="
        return f"{self.min}{lop}x{rop}{self.max}"

    def __repr__(self) -> str:
        clamp = " clamped" if self.clamp else ""
        return f"<{type(self).__name__} {self._describe_range()}{clamp}>"


class IntParamType(_NumberParamTypeBase):
    name = "integer"
    _number_class = int

    def __repr__(self) -> str:
        return "INT"


class IntRange(_NumberRangeBase, IntParamType):
    """Restrict an :data:`click.INT` value to a range of accepted
    values. See :ref:`ranges`.

    If ``min`` or ``max`` are not passed, any value is accepted in that
    direction. If ``min_open`` or ``max_open`` are enabled, the
    corresponding boundary is not included in the range.

    If ``clamp`` is enabled, a value outside the range is clamped to the
    boundary instead of failing.

    .. versionchanged:: 8.0
        Added the ``min_open`` and ``max_open`` parameters.
    """

    name = "integer range"

    def _clamp(  # type: ignore
        self, bound: int, dir: t.Literal[1, -1], open: bool
    ) -> int:
        if not open:
            return bound

        return bound + dir


class FloatParamType(_NumberParamTypeBase):
    name = "float"
    _number_class = float

    def __repr__(self) -> str:
        return "FLOAT"


class FloatRange(_NumberRangeBase, FloatParamType):
    """Restrict a :data:`click.FLOAT` value to a range of accepted
    values. See :ref:`ranges`.

    If ``min`` or ``max`` are not passed, any value is accepted in that
    direction. If ``min_open`` or ``max_open`` are enabled, the
    corresponding boundary is not included in the range.

    If ``clamp`` is enabled, a value outside the range is clamped to the
    boundary instead of failing. This is not supported if either
    boundary is marked ``open``.

    .. versionchanged:: 8.0
        Added the ``min_open`` and ``max_open`` parameters.
    """

    name = "float range"

    def __init__(
        self,
        min: float | None = None,
        max: float | None = None,
        min_open: bool = False,
        max_open: bool = False,
        clamp: bool = False,
    ) -> None:
        super().__init__(
            min=min, max=max, min_open=min_open, max_open=max_open, clamp=clamp
        )

        if (min_open or max_open) and clamp:
            raise TypeError("Clamping is not supported for open bounds.")

    def _clamp(self, bound: float, dir: t.Literal[1, -1], open: bool) -> float:
        if not open:
            return bound

        # Could use math.nextafter here, but clamping an
        # open float range doesn't seem to be particularly useful. It's
        # left up to the user to write a callback to do it if needed.
        raise RuntimeError("Clamping is not supported for open bounds.")


class BoolParamType(ParamType):
    name = "boolean"

    bool_states: dict[str, bool] = {
        "1": True,
        "0": False,
        "yes": True,
        "no": False,
        "true": True,
        "false": False,
        "on": True,
        "off": False,
        "t": True,
        "f": False,
        "y": True,
        "n": False,
        # Absence of value is considered False.
        "": False,
    }
    """A mapping of string values to boolean states.

    Mapping is inspired by :py:attr:`configparser.ConfigParser.BOOLEAN_STATES`
    and extends it.

    .. caution::
        String values are lower-cased, as the ``str_to_bool`` comparison function
        below is case-insensitive.

    .. warning::
        The mapping is not exhaustive, and does not cover all possible boolean strings
        representations. It will remains as it is to avoid endless bikeshedding.

        Future work my be considered to make this mapping user-configurable from public
        API.
    """

    @staticmethod
    def str_to_bool(value: str | bool) -> bool | None:
        """Convert a string to a boolean value.

        If the value is already a boolean, it is returned as-is. If the value is a
        string, it is stripped of whitespaces and lower-cased, then checked against
        the known boolean states pre-defined in the `BoolParamType.bool_states` mapping
        above.

        Returns `None` if the value does not match any known boolean state.
        """
        if isinstance(value, bool):
            return value
        return BoolParamType.bool_states.get(value.strip().lower())

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> bool:
        normalized = self.str_to_bool(value)
        if normalized is None:
            self.fail(
                _(
                    "{value!r} is not a valid boolean. Recognized values: {states}"
                ).format(value=value, states=", ".join(sorted(self.bool_states))),
                param,
                ctx,
            )
        return normalized

    def __repr__(self) -> str:
        return "BOOL"


class UUIDParameterType(ParamType):
    name = "uuid"

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        import uuid

        if isinstance(value, uuid.UUID):
            return value

        value = value.strip()

        try:
            return uuid.UUID(value)
        except ValueError:
            self.fail(
                _("{value!r} is not a valid UUID.").format(value=value), param, ctx
            )

    def __repr__(self) -> str:
        return "UUID"


class File(ParamType):
    """Declares a parameter to be a file for reading or writing.  The file
    is automatically closed once the context tears down (after the command
    finished working).

    Files can be opened for reading or writing.  The special value ``-``
    indicates stdin or stdout depending on the mode.

    By default, the file is opened for reading text data, but it can also be
    opened in binary mode or for writing.  The encoding parameter can be used
    to force a specific encoding.

    The `lazy` flag controls if the file should be opened immediately or upon
    first IO. The default is to be non-lazy for standard input and output
    streams as well as files opened for reading, `lazy` otherwise. When opening a
    file lazily for reading, it is still opened temporarily for validation, but
    will not be held open until first IO. lazy is mainly useful when opening
    for writing to avoid creating the file until it is needed.

    Files can also be opened atomically in which case all writes go into a
    separate file in the same folder and upon completion the file will
    be moved over to the original location.  This is useful if a file
    regularly read by other users is modified.

    See :ref:`file-args` for more information.

    .. versionchanged:: 2.0
        Added the ``atomic`` parameter.
    """

    name = "filename"
    envvar_list_splitter: t.ClassVar[str] = os.path.pathsep

    def __init__(
        self,
        mode: str = "r",
        encoding: str | None = None,
        errors: str | None = "strict",
        lazy: bool | None = None,
        atomic: bool = False,
    ) -> None:
        self.mode = mode
        self.encoding = encoding
        self.errors = errors
        self.lazy = lazy
        self.atomic = atomic

    def to_info_dict(self) -> dict[str, t.Any]:
        info_dict = super().to_info_dict()
        info_dict.update(mode=self.mode, encoding=self.encoding)
        return info_dict

    def resolve_lazy_flag(self, value: str | os.PathLike[str]) -> bool:
        if self.lazy is not None:
            return self.lazy
        if os.fspath(value) == "-":
            return False
        elif "w" in self.mode:
            return True
        return False

    def convert(
        self,
        value: str | os.PathLike[str] | t.IO[t.Any],
        param: Parameter | None,
        ctx: Context | None,
    ) -> t.IO[t.Any]:
        if _is_file_like(value):
            return value

        value = t.cast("str | os.PathLike[str]", value)

        try:
            lazy = self.resolve_lazy_flag(value)

            if lazy:
                lf = LazyFile(
                    value, self.mode, self.encoding, self.errors, atomic=self.atomic
                )

                if ctx is not None:
                    ctx.call_on_close(lf.close_intelligently)

                return t.cast("t.IO[t.Any]", lf)

            f, should_close = open_stream(
                value, self.mode, self.encoding, self.errors, atomic=self.atomic
            )

            # If a context is provided, we automatically close the file
            # at the end of the context execution (or flush out).  If a
            # context does not exist, it's the caller's responsibility to
            # properly close the file.  This for instance happens when the
            # type is used with prompts.
            if ctx is not None:
                if should_close:
                    ctx.call_on_close(safecall(f.close))
                else:
                    ctx.call_on_close(safecall(f.flush))

            return f
        except OSError as e:
            self.fail(f"'{format_filename(value)}': {e.strerror}", param, ctx)

    def shell_complete(
        self, ctx: Context, param: Parameter, incomplete: str
    ) -> list[CompletionItem]:
        """Return a special completion marker that tells the completion
        system to use the shell to provide file path completions.

        :param ctx: Invocation context for this command.
        :param param: The parameter that is requesting completion.
        :param incomplete: Value being completed. May be empty.

        .. versionadded:: 8.0
        """
        from click.shell_completion import CompletionItem

        return [CompletionItem(incomplete, type="file")]


def _is_file_like(value: t.Any) -> te.TypeGuard[t.IO[t.Any]]:
    return hasattr(value, "read") or hasattr(value, "write")


class Path(ParamType):
    """The ``Path`` type is similar to the :class:`File` type, but
    returns the filename instead of an open file. Various checks can be
    enabled to validate the type of file and permissions.

    :param exists: The file or directory needs to exist for the value to
        be valid. If this is not set to ``True``, and the file does not
        exist, then all further checks are silently skipped.
    :param file_okay: Allow a file as a value.
    :param dir_okay: Allow a directory as a value.
    :param readable: if true, a readable check is performed.
    :param writable: if true, a writable check is performed.
    :param executable: if true, an executable check is performed.
    :param resolve_path: Make the value absolute and resolve any
        symlinks. A ``~`` is not expanded, as this is supposed to be
        done by the shell only.
    :param allow_dash: Allow a single dash as a value, which indicates
        a standard stream (but does not open it). Use
        :func:`~click.open_file` to handle opening this value.
    :param path_type: Convert the incoming path value to this type. If
        ``None``, keep Python's default, which is ``str``. Useful to
        convert to :class:`pathlib.Path`.

    .. versionchanged:: 8.1
        Added the ``executable`` parameter.

    .. versionchanged:: 8.0
        Allow passing ``path_type=pathlib.Path``.

    .. versionchanged:: 6.0
        Added the ``allow_dash`` parameter.
    """

    envvar_list_splitter: t.ClassVar[str] = os.path.pathsep

    def __init__(
        self,
        exists: bool = False,
        file_okay: bool = True,
        dir_okay: bool = True,
        writable: bool = False,
        readable: bool = True,
        resolve_path: bool = False,
        allow_dash: bool = False,
        path_type: type[t.Any] | None = None,
        executable: bool = False,
    ):
        self.exists = exists
        self.file_okay = file_okay
        self.dir_okay = dir_okay
        self.readable = readable
        self.writable = writable
        self.executable = executable
        self.resolve_path = resolve_path
        self.allow_dash = allow_dash
        self.type = path_type

        if self.file_okay and not self.dir_okay:
            self.name: str = _("file")
        elif self.dir_okay and not self.file_okay:
            self.name = _("directory")
        else:
            self.name = _("path")

    def to_info_dict(self) -> dict[str, t.Any]:
        info_dict = super().to_info_dict()
        info_dict.update(
            exists=self.exists,
            file_okay=self.file_okay,
            dir_okay=self.dir_okay,
            writable=self.writable,
            readable=self.readable,
            allow_dash=self.allow_dash,
        )
        return info_dict

    def coerce_path_result(
        self, value: str | os.PathLike[str]
    ) -> str | bytes | os.PathLike[str]:
        if self.type is not None and not isinstance(value, self.type):
            if self.type is str:
                return os.fsdecode(value)
            elif self.type is bytes:
                return os.fsencode(value)
            else:
                return t.cast("os.PathLike[str]", self.type(value))

        return value

    def convert(
        self,
        value: str | os.PathLike[str],
        param: Parameter | None,
        ctx: Context | None,
    ) -> str | bytes | os.PathLike[str]:
        rv = value

        is_dash = self.file_okay and self.allow_dash and rv in (b"-", "-")

        if not is_dash:
            if self.resolve_path:
                rv = os.path.realpath(rv)

            try:
                st = os.stat(rv)
            except OSError:
                if not self.exists:
                    return self.coerce_path_result(rv)
                self.fail(
                    _("{name} {filename!r} does not exist.").format(
                        name=self.name.title(), filename=format_filename(value)
                    ),
                    param,
                    ctx,
                )

            if not self.file_okay and stat.S_ISREG(st.st_mode):
                self.fail(
                    _("{name} {filename!r} is a file.").format(
                        name=self.name.title(), filename=format_filename(value)
                    ),
                    param,
                    ctx,
                )
            if not self.dir_okay and stat.S_ISDIR(st.st_mode):
                self.fail(
                    _("{name} {filename!r} is a directory.").format(
                        name=self.name.title(), filename=format_filename(value)
                    ),
                    param,
                    ctx,
                )

            if self.readable and not os.access(rv, os.R_OK):
                self.fail(
                    _("{name} {filename!r} is not readable.").format(
                        name=self.name.title(), filename=format_filename(value)
                    ),
                    param,
                    ctx,
                )

            if self.writable and not os.access(rv, os.W_OK):
                self.fail(
                    _("{name} {filename!r} is not writable.").format(
                        name=self.name.title(), filename=format_filename(value)
                    ),
                    param,
                    ctx,
                )

            if self.executable and not os.access(value, os.X_OK):
                self.fail(
                    _("{name} {filename!r} is not executable.").format(
                        name=self.name.title(), filename=format_filename(value)
                    ),
                    param,
                    ctx,
                )

        return self.coerce_path_result(rv)

    def shell_complete(
        self, ctx: Context, param: Parameter, incomplete: str
    ) -> list[CompletionItem]:
        """Return a special completion marker that tells the completion
        system to use the shell to provide path completions for only
        directories or any paths.

        :param ctx: Invocation context for this command.
        :param param: The parameter that is requesting completion.
        :param incomplete: Value being completed. May be empty.

        .. versionadded:: 8.0
        """
        from click.shell_completion import CompletionItem

        type = "dir" if self.dir_okay and not self.file_okay else "file"
        return [CompletionItem(incomplete, type=type)]


class Tuple(CompositeParamType):
    """The default behavior of Click is to apply a type on a value directly.
    This works well in most cases, except for when `nargs` is set to a fixed
    count and different types should be used for different items.  In this
    case the :class:`Tuple` type can be used.  This type can only be used
    if `nargs` is set to a fixed number.

    For more information see :ref:`tuple-type`.

    This can be selected by using a Python tuple literal as a type.

    :param types: a list of types that should be used for the tuple items.
    """

    def __init__(self, types: cabc.Sequence[type[t.Any] | ParamType]) -> None:
        self.types: cabc.Sequence[ParamType] = [convert_type(ty) for ty in types]

    def to_info_dict(self) -> dict[str, t.Any]:
        info_dict = super().to_info_dict()
        info_dict["types"] = [t.to_info_dict() for t in self.types]
        return info_dict

    @property
    def name(self) -> str:  # type: ignore
        return f"<{' '.join(ty.name for ty in self.types)}>"

    @property
    def arity(self) -> int:  # type: ignore
        return len(self.types)

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        len_type = len(self.types)
        len_value = len(value)

        if len_value != len_type:
            self.fail(
                ngettext(
                    "{len_type} values are required, but {len_value} was given.",
                    "{len_type} values are required, but {len_value} were given.",
                    len_value,
                ).format(len_type=len_type, len_value=len_value),
                param=param,
                ctx=ctx,
            )

        return tuple(
            ty(x, param, ctx) for ty, x in zip(self.types, value, strict=False)
        )


def convert_type(ty: t.Any | None, default: t.Any | None = None) -> ParamType:
    """Find the most appropriate :class:`ParamType` for the given Python
    type. If the type isn't provided, it can be inferred from a default
    value.
    """
    guessed_type = False

    if ty is None and default is not None:
        if isinstance(default, (tuple, list)):
            # If the default is empty, ty will remain None and will
            # return STRING.
            if default:
                item = default[0]

                # A tuple of tuples needs to detect the inner types.
                # Can't call convert recursively because that would
                # incorrectly unwind the tuple to a single type.
                if isinstance(item, (tuple, list)):
                    ty = tuple(map(type, item))
                else:
                    ty = type(item)
        else:
            ty = type(default)

        guessed_type = True

    if isinstance(ty, tuple):
        return Tuple(ty)

    if isinstance(ty, ParamType):
        return ty

    if ty is str or ty is None:
        return STRING

    if ty is int:
        return INT

    if ty is float:
        return FLOAT

    if ty is bool:
        return BOOL

    if guessed_type:
        return STRING

    if __debug__:
        try:
            if issubclass(ty, ParamType):
                raise AssertionError(
                    f"Attempted to use an uninstantiated parameter type ({ty})."
                )
        except TypeError:
            # ty is an instance (correct), so issubclass fails.
            pass

    return FuncParamType(ty)


#: A dummy parameter type that just does nothing.  From a user's
#: perspective this appears to just be the same as `STRING` but
#: internally no string conversion takes place if the input was bytes.
#: This is usually useful when working with file paths as they can
#: appear in bytes and unicode.
#:
#: For path related uses the :class:`Path` type is a better choice but
#: there are situations where an unprocessed type is useful which is why
#: it is is provided.
#:
#: .. versionadded:: 4.0
UNPROCESSED = UnprocessedParamType()

#: A unicode string parameter type which is the implicit default.  This
#: can also be selected by using ``str`` as type.
STRING = StringParamType()

#: An integer parameter.  This can also be selected by using ``int`` as
#: type.
INT = IntParamType()

#: A floating point value parameter.  This can also be selected by using
#: ``float`` as type.
FLOAT = FloatParamType()

#: A boolean parameter.  This is the default for boolean flags.  This can
#: also be selected by using ``bool`` as a type.
BOOL = BoolParamType()

#: A UUID parameter.
UUID = UUIDParameterType()


class OptionHelpExtra(t.TypedDict, total=False):
    envvars: tuple[str, ...]
    default: str
    range: str
    required: str

```
---

## src/click/utils.py

```python
from __future__ import annotations

import collections.abc as cabc
import os
import re
import sys
import typing as t
from functools import update_wrapper
from types import ModuleType
from types import TracebackType

from ._compat import _default_text_stderr
from ._compat import _default_text_stdout
from ._compat import _find_binary_writer
from ._compat import auto_wrap_for_ansi
from ._compat import binary_streams
from ._compat import open_stream
from ._compat import should_strip_ansi
from ._compat import strip_ansi
from ._compat import text_streams
from ._compat import WIN
from .globals import resolve_color_default

if t.TYPE_CHECKING:
    import typing_extensions as te

    P = te.ParamSpec("P")

R = t.TypeVar("R")


def _posixify(name: str) -> str:
    return "-".join(name.split()).lower()


def safecall(func: t.Callable[P, R]) -> t.Callable[P, R | None]:
    """Wraps a function so that it swallows exceptions."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        try:
            return func(*args, **kwargs)
        except Exception:
            pass
        return None

    return update_wrapper(wrapper, func)


def make_str(value: t.Any) -> str:
    """Converts a value into a valid string."""
    if isinstance(value, bytes):
        try:
            return value.decode(sys.getfilesystemencoding())
        except UnicodeError:
            return value.decode("utf-8", "replace")
    return str(value)


def make_default_short_help(help: str, max_length: int = 45) -> str:
    """Returns a condensed version of help string."""
    # Consider only the first paragraph.
    paragraph_end = help.find("\n\n")

    if paragraph_end != -1:
        help = help[:paragraph_end]

    # Collapse newlines, tabs, and spaces.
    words = help.split()

    if not words:
        return ""

    # The first paragraph started with a "no rewrap" marker, ignore it.
    if words[0] == "\b":
        words = words[1:]

    total_length = 0
    last_index = len(words) - 1

    for i, word in enumerate(words):
        total_length += len(word) + (i > 0)

        if total_length > max_length:  # too long, truncate
            break

        if word[-1] == ".":  # sentence end, truncate without "..."
            return " ".join(words[: i + 1])

        if total_length == max_length and i != last_index:
            break  # not at sentence end, truncate with "..."
    else:
        return " ".join(words)  # no truncation needed

    # Account for the length of the suffix.
    total_length += len("...")

    # remove words until the length is short enough
    while i > 0:
        total_length -= len(words[i]) + (i > 0)

        if total_length <= max_length:
            break

        i -= 1

    return " ".join(words[:i]) + "..."


class LazyFile:
    """A lazy file works like a regular file but it does not fully open
    the file but it does perform some basic checks early to see if the
    filename parameter does make sense.  This is useful for safely opening
    files for writing.
    """

    def __init__(
        self,
        filename: str | os.PathLike[str],
        mode: str = "r",
        encoding: str | None = None,
        errors: str | None = "strict",
        atomic: bool = False,
    ):
        self.name: str = os.fspath(filename)
        self.mode = mode
        self.encoding = encoding
        self.errors = errors
        self.atomic = atomic
        self._f: t.IO[t.Any] | None
        self.should_close: bool

        if self.name == "-":
            self._f, self.should_close = open_stream(filename, mode, encoding, errors)
        else:
            if "r" in mode:
                # Open and close the file in case we're opening it for
                # reading so that we can catch at least some errors in
                # some cases early.
                open(filename, mode).close()
            self._f = None
            self.should_close = True

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self.open(), name)

    def __repr__(self) -> str:
        if self._f is not None:
            return repr(self._f)
        return f"<unopened file '{format_filename(self.name)}' {self.mode}>"

    def open(self) -> t.IO[t.Any]:
        """Opens the file if it's not yet open.  This call might fail with
        a :exc:`FileError`.  Not handling this error will produce an error
        that Click shows.
        """
        if self._f is not None:
            return self._f
        try:
            rv, self.should_close = open_stream(
                self.name, self.mode, self.encoding, self.errors, atomic=self.atomic
            )
        except OSError as e:
            from .exceptions import FileError

            raise FileError(self.name, hint=e.strerror) from e
        self._f = rv
        return rv

    def close(self) -> None:
        """Closes the underlying file, no matter what."""
        if self._f is not None:
            self._f.close()

    def close_intelligently(self) -> None:
        """This function only closes the file if it was opened by the lazy
        file wrapper.  For instance this will never close stdin.
        """
        if self.should_close:
            self.close()

    def __enter__(self) -> LazyFile:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close_intelligently()

    def __iter__(self) -> cabc.Iterator[t.AnyStr]:
        self.open()
        return iter(self._f)  # type: ignore


class KeepOpenFile:
    def __init__(self, file: t.IO[t.Any]) -> None:
        self._file: t.IO[t.Any] = file

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self._file, name)

    def __enter__(self) -> KeepOpenFile:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    def __repr__(self) -> str:
        return repr(self._file)

    def __iter__(self) -> cabc.Iterator[t.AnyStr]:
        return iter(self._file)


def echo(
    message: t.Any | None = None,
    file: t.IO[t.Any] | None = None,
    nl: bool = True,
    err: bool = False,
    color: bool | None = None,
) -> None:
    """Print a message and newline to stdout or a file. This should be
    used instead of :func:`print` because it provides better support
    for different data, files, and environments.

    Compared to :func:`print`, this does the following:

    -   Ensures that the output encoding is not misconfigured on Linux.
    -   Supports Unicode in the Windows console.
    -   Supports writing to binary outputs, and supports writing bytes
        to text outputs.
    -   Supports colors and styles on Windows.
    -   Removes ANSI color and style codes if the output does not look
        like an interactive terminal.
    -   Always flushes the output.

    :param message: The string or bytes to output. Other objects are
        converted to strings.
    :param file: The file to write to. Defaults to ``stdout``.
    :param err: Write to ``stderr`` instead of ``stdout``.
    :param nl: Print a newline after the message. Enabled by default.
    :param color: Force showing or hiding colors and other styles. By
        default Click will remove color if the output does not look like
        an interactive terminal.

    .. versionchanged:: 6.0
        Support Unicode output on the Windows console. Click does not
        modify ``sys.stdout``, so ``sys.stdout.write()`` and ``print()``
        will still not support Unicode.

    .. versionchanged:: 4.0
        Added the ``color`` parameter.

    .. versionadded:: 3.0
        Added the ``err`` parameter.

    .. versionchanged:: 2.0
        Support colors on Windows if colorama is installed.
    """
    if file is None:
        if err:
            file = _default_text_stderr()
        else:
            file = _default_text_stdout()

        # There are no standard streams attached to write to. For example,
        # pythonw on Windows.
        if file is None:
            return

    # Convert non bytes/text into the native string type.
    if message is not None and not isinstance(message, (str, bytes, bytearray)):
        out: str | bytes | bytearray | None = str(message)
    else:
        out = message

    if nl:
        out = out or ""
        if isinstance(out, str):
            out += "\n"
        else:
            out += b"\n"

    if not out:
        file.flush()
        return

    # If there is a message and the value looks like bytes, we manually
    # need to find the binary stream and write the message in there.
    # This is done separately so that most stream types will work as you
    # would expect. Eg: you can write to StringIO for other cases.
    if isinstance(out, (bytes, bytearray)):
        binary_file = _find_binary_writer(file)

        if binary_file is not None:
            file.flush()
            binary_file.write(out)
            binary_file.flush()
            return

    # ANSI style code support. For no message or bytes, nothing happens.
    # When outputting to a file instead of a terminal, strip codes.
    else:
        color = resolve_color_default(color)

        if should_strip_ansi(file, color):
            out = strip_ansi(out)
        elif WIN:
            if auto_wrap_for_ansi is not None:
                file = auto_wrap_for_ansi(file, color)  # type: ignore
            elif not color:
                out = strip_ansi(out)

    file.write(out)  # type: ignore
    file.flush()


def get_binary_stream(name: t.Literal["stdin", "stdout", "stderr"]) -> t.BinaryIO:
    """Returns a system stream for byte processing.

    :param name: the name of the stream to open.  Valid names are ``'stdin'``,
                 ``'stdout'`` and ``'stderr'``
    """
    opener = binary_streams.get(name)
    if opener is None:
        raise TypeError(f"Unknown standard stream '{name}'")
    return opener()


def get_text_stream(
    name: t.Literal["stdin", "stdout", "stderr"],
    encoding: str | None = None,
    errors: str | None = "strict",
) -> t.TextIO:
    """Returns a system stream for text processing.  This usually returns
    a wrapped stream around a binary stream returned from
    :func:`get_binary_stream` but it also can take shortcuts for already
    correctly configured streams.

    :param name: the name of the stream to open.  Valid names are ``'stdin'``,
                 ``'stdout'`` and ``'stderr'``
    :param encoding: overrides the detected default encoding.
    :param errors: overrides the default error mode.
    """
    opener = text_streams.get(name)
    if opener is None:
        raise TypeError(f"Unknown standard stream '{name}'")
    return opener(encoding, errors)


def open_file(
    filename: str | os.PathLike[str],
    mode: str = "r",
    encoding: str | None = None,
    errors: str | None = "strict",
    lazy: bool = False,
    atomic: bool = False,
) -> t.IO[t.Any]:
    """Open a file, with extra behavior to handle ``'-'`` to indicate
    a standard stream, lazy open on write, and atomic write. Similar to
    the behavior of the :class:`~click.File` param type.

    If ``'-'`` is given to open ``stdout`` or ``stdin``, the stream is
    wrapped so that using it in a context manager will not close it.
    This makes it possible to use the function without accidentally
    closing a standard stream:

    .. code-block:: python

        with open_file(filename) as f:
            ...

    :param filename: The name or Path of the file to open, or ``'-'`` for
        ``stdin``/``stdout``.
    :param mode: The mode in which to open the file.
    :param encoding: The encoding to decode or encode a file opened in
        text mode.
    :param errors: The error handling mode.
    :param lazy: Wait to open the file until it is accessed. For read
        mode, the file is temporarily opened to raise access errors
        early, then closed until it is read again.
    :param atomic: Write to a temporary file and replace the given file
        on close.

    .. versionadded:: 3.0
    """
    if lazy:
        return t.cast(
            "t.IO[t.Any]", LazyFile(filename, mode, encoding, errors, atomic=atomic)
        )

    f, should_close = open_stream(filename, mode, encoding, errors, atomic=atomic)

    if not should_close:
        f = t.cast("t.IO[t.Any]", KeepOpenFile(f))

    return f


def format_filename(
    filename: str | bytes | os.PathLike[str] | os.PathLike[bytes],
    shorten: bool = False,
) -> str:
    """Format a filename as a string for display. Ensures the filename can be
    displayed by replacing any invalid bytes or surrogate escapes in the name
    with the replacement character ``�``.

    Invalid bytes or surrogate escapes will raise an error when written to a
    stream with ``errors="strict"``. This will typically happen with ``stdout``
    when the locale is something like ``en_GB.UTF-8``.

    Many scenarios *are* safe to write surrogates though, due to PEP 538 and
    PEP 540, including:

    -   Writing to ``stderr``, which uses ``errors="backslashreplace"``.
    -   The system has ``LANG=C.UTF-8``, ``C``, or ``POSIX``. Python opens
        stdout and stderr with ``errors="surrogateescape"``.
    -   None of ``LANG/LC_*`` are set. Python assumes ``LANG=C.UTF-8``.
    -   Python is started in UTF-8 mode  with  ``PYTHONUTF8=1`` or ``-X utf8``.
        Python opens stdout and stderr with ``errors="surrogateescape"``.

    :param filename: formats a filename for UI display.  This will also convert
                     the filename into unicode without failing.
    :param shorten: this optionally shortens the filename to strip of the
                    path that leads up to it.
    """
    if shorten:
        filename = os.path.basename(filename)
    else:
        filename = os.fspath(filename)

    if isinstance(filename, bytes):
        filename = filename.decode(sys.getfilesystemencoding(), "replace")
    else:
        filename = filename.encode("utf-8", "surrogateescape").decode(
            "utf-8", "replace"
        )

    return filename


def get_app_dir(app_name: str, roaming: bool = True, force_posix: bool = False) -> str:
    r"""Returns the config folder for the application.  The default behavior
    is to return whatever is most appropriate for the operating system.

    To give you an idea, for an app called ``"Foo Bar"``, something like
    the following folders could be returned:

    Mac OS X:
      ``~/Library/Application Support/Foo Bar``
    Mac OS X (POSIX):
      ``~/.foo-bar``
    Unix:
      ``~/.config/foo-bar``
    Unix (POSIX):
      ``~/.foo-bar``
    Windows (roaming):
      ``C:\Users\<user>\AppData\Roaming\Foo Bar``
    Windows (not roaming):
      ``C:\Users\<user>\AppData\Local\Foo Bar``

    .. versionadded:: 2.0

    :param app_name: the application name.  This should be properly capitalized
                     and can contain whitespace.
    :param roaming: controls if the folder should be roaming or not on Windows.
                    Has no effect otherwise.
    :param force_posix: if this is set to `True` then on any POSIX system the
                        folder will be stored in the home folder with a leading
                        dot instead of the XDG config home or darwin's
                        application support folder.
    """
    if WIN:
        key = "APPDATA" if roaming else "LOCALAPPDATA"
        folder = os.environ.get(key)
        if folder is None:
            folder = os.path.expanduser("~")
        return os.path.join(folder, app_name)
    if force_posix:
        return os.path.join(os.path.expanduser(f"~/.{_posixify(app_name)}"))
    if sys.platform == "darwin":
        return os.path.join(
            os.path.expanduser("~/Library/Application Support"), app_name
        )
    return os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        _posixify(app_name),
    )


class PacifyFlushWrapper:
    """This wrapper is used to catch and suppress BrokenPipeErrors resulting
    from ``.flush()`` being called on broken pipe during the shutdown/final-GC
    of the Python interpreter. Notably ``.flush()`` is always called on
    ``sys.stdout`` and ``sys.stderr``. So as to have minimal impact on any
    other cleanup code, and the case where the underlying file is not a broken
    pipe, all calls and attributes are proxied.
    """

    def __init__(self, wrapped: t.IO[t.Any]) -> None:
        self.wrapped = wrapped

    def flush(self) -> None:
        try:
            self.wrapped.flush()
        except OSError as e:
            import errno

            if e.errno != errno.EPIPE:
                raise

    def __getattr__(self, attr: str) -> t.Any:
        return getattr(self.wrapped, attr)


def _detect_program_name(
    path: str | None = None, _main: ModuleType | None = None
) -> str:
    """Determine the command used to run the program, for use in help
    text. If a file or entry point was executed, the file name is
    returned. If ``python -m`` was used to execute a module or package,
    ``python -m name`` is returned.

    This doesn't try to be too precise, the goal is to give a concise
    name for help text. Files are only shown as their name without the
    path. ``python`` is only shown for modules, and the full path to
    ``sys.executable`` is not shown.

    :param path: The Python file being executed. Python puts this in
        ``sys.argv[0]``, which is used by default.
    :param _main: The ``__main__`` module. This should only be passed
        during internal testing.

    .. versionadded:: 8.0
        Based on command args detection in the Werkzeug reloader.

    :meta private:
    """
    if _main is None:
        _main = sys.modules["__main__"]

    if not path:
        path = sys.argv[0]

    # The value of __package__ indicates how Python was called. It may
    # not exist if a setuptools script is installed as an egg. It may be
    # set incorrectly for entry points created with pip on Windows.
    # It is set to "" inside a Shiv or PEX zipapp.
    if getattr(_main, "__package__", None) in {None, ""} or (
        os.name == "nt"
        and _main.__package__ == ""
        and not os.path.exists(path)
        and os.path.exists(f"{path}.exe")
    ):
        # Executed a file, like "python app.py".
        return os.path.basename(path)

    # Executed a module, like "python -m example".
    # Rewritten by Python from "-m script" to "/path/to/script.py".
    # Need to look at main module to determine how it was executed.
    py_module = t.cast(str, _main.__package__)
    name = os.path.splitext(os.path.basename(path))[0]

    # A submodule like "example.cli".
    if name != "__main__":
        py_module = f"{py_module}.{name}"

    return f"python -m {py_module.lstrip('.')}"


def _expand_args(
    args: cabc.Iterable[str],
    *,
    user: bool = True,
    env: bool = True,
    glob_recursive: bool = True,
) -> list[str]:
    """Simulate Unix shell expansion with Python functions.

    See :func:`glob.glob`, :func:`os.path.expanduser`, and
    :func:`os.path.expandvars`.

    This is intended for use on Windows, where the shell does not do any
    expansion. It may not exactly match what a Unix shell would do.

    :param args: List of command line arguments to expand.
    :param user: Expand user home directory.
    :param env: Expand environment variables.
    :param glob_recursive: ``**`` matches directories recursively.

    .. versionchanged:: 8.1
        Invalid glob patterns are treated as empty expansions rather
        than raising an error.

    .. versionadded:: 8.0

    :meta private:
    """
    from glob import glob

    out = []

    for arg in args:
        if user:
            arg = os.path.expanduser(arg)

        if env:
            arg = os.path.expandvars(arg)

        try:
            matches = glob(arg, recursive=glob_recursive)
        except re.error:
            matches = []

        if not matches:
            out.append(arg)
        else:
            out.extend(matches)

    return out

```
---

## tests/conftest.py

```python
import pytest

from click.testing import CliRunner


@pytest.fixture(scope="function")
def runner(request):
    return CliRunner()

```
---

## tests/test_arguments.py

```python
import sys
from unittest import mock

import pytest

import click
from click._utils import UNSET


def test_nargs_star(runner):
    @click.command()
    @click.argument("src", nargs=-1)
    @click.argument("dst")
    def copy(src, dst):
        click.echo(f"src={'|'.join(src)}")
        click.echo(f"dst={dst}")

    result = runner.invoke(copy, ["foo.txt", "bar.txt", "dir"])
    assert not result.exception
    assert result.output.splitlines() == ["src=foo.txt|bar.txt", "dst=dir"]


def test_nargs_tup(runner):
    @click.command()
    @click.argument("name", nargs=1)
    @click.argument("point", nargs=2, type=click.INT)
    def copy(name, point):
        click.echo(f"name={name}")
        x, y = point
        click.echo(f"point={x}/{y}")

    result = runner.invoke(copy, ["peter", "1", "2"])
    assert not result.exception
    assert result.output.splitlines() == ["name=peter", "point=1/2"]


@pytest.mark.parametrize(
    "opts",
    [
        dict(type=(str, int)),
        dict(type=click.Tuple([str, int])),
        dict(nargs=2, type=click.Tuple([str, int])),
        dict(nargs=2, type=(str, int)),
    ],
)
def test_nargs_tup_composite(runner, opts):
    @click.command()
    @click.argument("item", **opts)
    def copy(item):
        name, id = item
        click.echo(f"name={name} id={id:d}")

    result = runner.invoke(copy, ["peter", "1"])
    assert result.exception is None
    assert result.output.splitlines() == ["name=peter id=1"]


def test_nargs_mismatch_with_tuple_type():
    with pytest.raises(ValueError, match="nargs.*must be 2.*but it was 3"):

        @click.command()
        @click.argument("test", type=(str, int), nargs=3)
        def cli(_):
            pass


def test_nargs_err(runner):
    @click.command()
    @click.argument("x")
    def copy(x):
        click.echo(x)

    result = runner.invoke(copy, ["foo"])
    assert not result.exception
    assert result.output == "foo\n"

    result = runner.invoke(copy, ["foo", "bar"])
    assert result.exit_code == 2
    assert "Got unexpected extra argument (bar)" in result.output


def test_bytes_args(runner, monkeypatch):
    @click.command()
    @click.argument("arg")
    def from_bytes(arg):
        assert isinstance(arg, str), (
            "UTF-8 encoded argument should be implicitly converted to Unicode"
        )

    # Simulate empty locale environment variables
    monkeypatch.setattr(sys, "getfilesystemencoding", lambda: "utf-8")
    monkeypatch.setattr(sys, "getdefaultencoding", lambda: "utf-8")
    # sys.stdin.encoding is readonly, needs some extra effort to patch.
    stdin = mock.Mock(wraps=sys.stdin)
    stdin.encoding = "utf-8"
    monkeypatch.setattr(sys, "stdin", stdin)

    runner.invoke(
        from_bytes,
        ["Something outside of ASCII range: 林".encode()],
        catch_exceptions=False,
    )


def test_file_args(runner):
    @click.command()
    @click.argument("input", type=click.File("rb"))
    @click.argument("output", type=click.File("wb"))
    def inout(input, output):
        while True:
            chunk = input.read(1024)
            if not chunk:
                break
            output.write(chunk)

    with runner.isolated_filesystem():
        result = runner.invoke(inout, ["-", "hello.txt"], input="Hey!")
        assert result.output == ""
        assert result.exit_code == 0
        with open("hello.txt", "rb") as f:
            assert f.read() == b"Hey!"

        result = runner.invoke(inout, ["hello.txt", "-"])
        assert result.output == "Hey!"
        assert result.exit_code == 0


def test_path_allow_dash(runner):
    @click.command()
    @click.argument("input", type=click.Path(allow_dash=True))
    def foo(input):
        click.echo(input)

    result = runner.invoke(foo, ["-"])
    assert result.output == "-\n"
    assert result.exit_code == 0


def test_file_atomics(runner):
    @click.command()
    @click.argument("output", type=click.File("wb", atomic=True))
    def inout(output):
        output.write(b"Foo bar baz\n")
        output.flush()
        with open(output.name, "rb") as f:
            old_content = f.read()
            assert old_content == b"OLD\n"

    with runner.isolated_filesystem():
        with open("foo.txt", "wb") as f:
            f.write(b"OLD\n")
        result = runner.invoke(inout, ["foo.txt"], input="Hey!", catch_exceptions=False)
        assert result.output == ""
        assert result.exit_code == 0
        with open("foo.txt", "rb") as f:
            assert f.read() == b"Foo bar baz\n"


def test_stdout_default(runner):
    @click.command()
    @click.argument("output", type=click.File("w"), default="-")
    def inout(output):
        output.write("Foo bar baz\n")
        output.flush()

    result = runner.invoke(inout, [])
    assert not result.exception
    assert result.output == "Foo bar baz\n"
    assert result.stdout == "Foo bar baz\n"
    assert not result.stderr


@pytest.mark.parametrize(
    ("nargs", "value", "expect"),
    [
        (2, "", None),
        (2, "a", "Takes 2 values but 1 was given."),
        (2, "a b", ("a", "b")),
        (2, "a b c", "Takes 2 values but 3 were given."),
        (-1, "a b c", ("a", "b", "c")),
        (-1, "", ()),
    ],
)
def test_nargs_envvar(runner, nargs, value, expect):
    if nargs == -1:
        param = click.argument("arg", envvar="X", nargs=nargs)
    else:
        param = click.option("--arg", envvar="X", nargs=nargs)

    @click.command()
    @param
    def cmd(arg):
        return arg

    result = runner.invoke(cmd, env={"X": value}, standalone_mode=False)

    if isinstance(expect, str):
        assert isinstance(result.exception, click.BadParameter)
        assert expect in result.exception.format_message()
    else:
        assert result.return_value == expect


def test_nargs_envvar_only_if_values_empty(runner):
    @click.command()
    @click.argument("arg", envvar="X", nargs=-1)
    def cli(arg):
        return arg

    result = runner.invoke(cli, ["a", "b"], standalone_mode=False)
    assert result.return_value == ("a", "b")

    result = runner.invoke(cli, env={"X": "a"}, standalone_mode=False)
    assert result.return_value == ("a",)


def test_empty_nargs(runner):
    @click.command()
    @click.argument("arg", nargs=-1)
    def cmd(arg):
        click.echo(f"arg:{'|'.join(arg)}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 0
    assert result.output == "arg:\n"

    @click.command()
    @click.argument("arg", nargs=-1, required=True)
    def cmd2(arg):
        click.echo(f"arg:{'|'.join(arg)}")

    result = runner.invoke(cmd2, [])
    assert result.exit_code == 2
    assert "Missing argument 'ARG...'" in result.output


def test_missing_arg(runner):
    @click.command()
    @click.argument("arg")
    def cmd(arg):
        click.echo(f"arg:{arg}")

    result = runner.invoke(cmd, [])
    assert result.exit_code == 2
    assert "Missing argument 'ARG'." in result.output


@pytest.mark.parametrize(
    ("value", "expect_missing", "processed_value"),
    [
        # Unspecified type of the argument fallback to string, so everything is
        # processed the click.STRING type.
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
        # None is a value that is allowed to be processed by a required argument
        # because at this stage, the process_value method happens after the default is
        # applied.
        (None, False, None),
        # An UNSET required argument will raise MissingParameter.
        (UNSET, True, None),
    ],
)
def test_required_argument(value, expect_missing, processed_value):
    """Test how a required argument is processing the provided values."""
    ctx = click.Context(click.Command(""))
    argument = click.Argument(["a"], required=True)

    if expect_missing:
        with pytest.raises(click.MissingParameter) as excinfo:
            argument.process_value(ctx, value)
        assert str(excinfo.value) == "Missing parameter: a"

    else:
        value = argument.process_value(ctx, value)
        assert value == processed_value


def test_implicit_non_required(runner):
    @click.command()
    @click.argument("f", default="test")
    def cli(f):
        click.echo(f)

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output == "test\n"


def test_deprecated_usage(runner):
    @click.command()
    @click.argument("f", required=False, deprecated=True)
    def cli(f):
        click.echo(f)

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output
    assert "[F!]" in result.output


@pytest.mark.parametrize("deprecated", [True, "USE B INSTEAD"])
def test_deprecated_warning(runner, deprecated):
    @click.command()
    @click.argument(
        "my-argument", required=False, deprecated=deprecated, default="default argument"
    )
    def cli(my_argument: str):
        click.echo(f"{my_argument}")

    # defaults should not give a deprecated warning
    result = runner.invoke(cli, [])
    assert result.exit_code == 0, result.output
    assert "is deprecated" not in result.output

    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0, result.output
    assert "argument 'MY_ARGUMENT' is deprecated" in result.output

    if isinstance(deprecated, str):
        assert deprecated in result.output


def test_deprecated_required(runner):
    with pytest.raises(ValueError, match="is deprecated and still required"):
        click.Argument(["a"], required=True, deprecated=True)


def test_eat_options(runner):
    @click.command()
    @click.option("-f")
    @click.argument("files", nargs=-1)
    def cmd(f, files):
        for filename in files:
            click.echo(filename)
        click.echo(f)

    result = runner.invoke(cmd, ["--", "-foo", "bar"])
    assert result.output.splitlines() == ["-foo", "bar", ""]

    result = runner.invoke(cmd, ["-f", "-x", "--", "-foo", "bar"])
    assert result.output.splitlines() == ["-foo", "bar", "-x"]


def test_nargs_star_ordering(runner):
    @click.command()
    @click.argument("a", nargs=-1)
    @click.argument("b")
    @click.argument("c")
    def cmd(a, b, c):
        for arg in (a, b, c):
            click.echo(arg)

    result = runner.invoke(cmd, ["a", "b", "c"])
    assert result.output.splitlines() == ["('a',)", "b", "c"]


def test_nargs_specified_plus_star_ordering(runner):
    @click.command()
    @click.argument("a", nargs=-1)
    @click.argument("b")
    @click.argument("c", nargs=2)
    def cmd(a, b, c):
        for arg in (a, b, c):
            click.echo(arg)

    result = runner.invoke(cmd, ["a", "b", "c", "d", "e", "f"])
    assert result.output.splitlines() == ["('a', 'b', 'c')", "d", "('e', 'f')"]


@pytest.mark.parametrize(
    ("argument_params", "args", "expected"),
    [
        # Any iterable with the same number of arguments as nargs is valid.
        [{"nargs": 2, "default": (1, 2)}, [], (1, 2)],
        [{"nargs": 2, "default": (1.1, 2.2)}, [], (1, 2)],
        [{"nargs": 2, "default": ("1", "2")}, [], (1, 2)],
        [{"nargs": 2, "default": (None, None)}, [], (None, None)],
        [{"nargs": 2, "default": [1, 2]}, [], (1, 2)],
        [{"nargs": 2, "default": {1, 2}}, [], (1, 2)],
        [{"nargs": 2, "default": frozenset([1, 2])}, [], (1, 2)],
        [{"nargs": 2, "default": {1: "a", 2: "b"}}, [], (1, 2)],
        # Empty iterable is valid if default is None.
        [{"nargs": 2, "default": None}, [], None],
        # Arguments overrides the default.
        [{"nargs": 2, "default": (1, 2)}, ["3", "4"], (3, 4)],
        # Unbounded arguments are allowed to have a default.
        # See: https://github.com/pallets/click/issues/2164
        [{"nargs": -1, "default": [42]}, [], (42,)],
        [{"nargs": -1, "default": None}, [], ()],
        [{"nargs": -1, "default": {1, 2, 3, 4, 5}}, [], (1, 2, 3, 4, 5)],
    ],
)
def test_good_defaults_for_nargs(runner, argument_params, args, expected):
    @click.command()
    @click.argument("a", type=int, **argument_params)
    def cmd(a):
        click.echo(repr(a), nl=False)

    result = runner.invoke(cmd, args)
    assert result.output == repr(expected)


@pytest.mark.parametrize(
    ("default", "message"),
    [
        # Non-iterables defaults.
        ["Yo", "Error: Invalid value for '[A]...': Value must be an iterable."],
        ["", "Error: Invalid value for '[A]...': Value must be an iterable."],
        [True, "Error: Invalid value for '[A]...': Value must be an iterable."],
        [False, "Error: Invalid value for '[A]...': Value must be an iterable."],
        [12, "Error: Invalid value for '[A]...': Value must be an iterable."],
        [7.9, "Error: Invalid value for '[A]...': Value must be an iterable."],
        # Generator default.
        [(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        # Unset default.
        [UNSET, "Error: Missing argument 'A...'."],
        # Tuples defaults with wrong length.
        [
            tuple(),
            "Error: Invalid value for '[A]...': Takes 2 values but 0 were given.",
        ],
        [(1,), "Error: Invalid value for '[A]...': Takes 2 values but 1 was given."],
        [
            (1, 2, 3),
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Lists defaults with wrong length.
        [list(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        [[1], "Error: Invalid value for '[A]...': Takes 2 values but 1 was given."],
        [
            [1, 2, 3],
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Sets defaults with wrong length.
        [set(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        [
            set([1]),
            "Error: Invalid value for '[A]...': Takes 2 values but 1 was given.",
        ],
        [
            set([1, 2, 3]),
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Frozensets defaults with wrong length.
        [
            frozenset(),
            "Error: Invalid value for '[A]...': Takes 2 values but 0 were given.",
        ],
        [
            frozenset([1]),
            "Error: Invalid value for '[A]...': Takes 2 values but 1 was given.",
        ],
        [
            frozenset([1, 2, 3]),
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
        # Dictionaries defaults with wrong length.
        [dict(), "Error: Invalid value for '[A]...': Takes 2 values but 0 were given."],
        [
            {1: "a"},
            "Error: Invalid value for '[A]...': Takes 2 values but 1 was given.",
        ],
        [
            {1: "a", 2: "b", 3: "c"},
            "Error: Invalid value for '[A]...': Takes 2 values but 3 were given.",
        ],
    ],
)
def test_bad_defaults_for_nargs(runner, default, message):
    """Some defaults are not valid when nargs is set."""

    @click.command()
    @click.argument("a", nargs=2, type=int, default=default)
    def cmd(a):
        click.echo(repr(a))

    result = runner.invoke(cmd, [])
    assert message in result.stderr


def test_multiple_param_decls_not_allowed(runner):
    with pytest.raises(TypeError):

        @click.command()
        @click.argument("x", click.Choice(["a", "b"]))
        def copy(x):
            click.echo(x)


def test_multiple_not_allowed():
    with pytest.raises(TypeError, match="multiple"):
        click.Argument(["a"], multiple=True)


def test_subcommand_help(runner):
    @click.group()
    @click.argument("name")
    @click.argument("val")
    @click.option("--opt")
    @click.pass_context
    def cli(ctx, name, val, opt):
        ctx.obj = dict(name=name, val=val)

    @cli.command()
    @click.pass_obj
    def cmd(obj):
        click.echo(f"CMD for {obj['name']} with value {obj['val']}")

    result = runner.invoke(cli, ["foo", "bar", "cmd", "--help"])
    assert not result.exception
    assert "Usage: cli NAME VAL cmd [OPTIONS]" in result.output


def test_nested_subcommand_help(runner):
    @click.group()
    @click.argument("arg1")
    @click.option("--opt1")
    def cli(arg1, opt1):
        pass

    @cli.group()
    @click.argument("arg2")
    @click.option("--opt2")
    def cmd(arg2, opt2):
        pass

    @cmd.command()
    def subcmd():
        click.echo("subcommand")

    result = runner.invoke(cli, ["arg1", "cmd", "arg2", "subcmd", "--help"])
    assert not result.exception
    assert "Usage: cli ARG1 cmd ARG2 subcmd [OPTIONS]" in result.output


def test_when_argument_decorator_is_used_multiple_times_cls_is_preserved():
    class CustomArgument(click.Argument):
        pass

    reusable_argument = click.argument("art", cls=CustomArgument)

    @click.command()
    @reusable_argument
    def foo(arg):
        pass

    @click.command()
    @reusable_argument
    def bar(arg):
        pass

    assert isinstance(foo.params[0], CustomArgument)
    assert isinstance(bar.params[0], CustomArgument)


@pytest.mark.parametrize(
    "args_one,args_two",
    [
        (
            ("aardvark",),
            ("aardvark",),
        ),
    ],
)
def test_duplicate_names_warning(runner, args_one, args_two):
    @click.command()
    @click.argument(*args_one)
    @click.argument(*args_two)
    def cli(one, two):
        pass

    with pytest.warns(UserWarning):
        runner.invoke(cli, [])


@pytest.mark.parametrize(
    ("argument_kwargs", "pass_argv"),
    (
        # there is a large potential parameter space to explore here
        # this is just a very small sample of it
        ({}, ["myvalue"]),
        ({"nargs": -1}, []),
        ({"nargs": -1}, ["myvalue"]),
        ({"default": None}, ["myvalue"]),
        ({"required": False}, []),
        ({"required": False}, ["myvalue"]),
    ),
)
def test_argument_custom_class_can_override_type_cast_value_and_never_sees_unset(
    runner, argument_kwargs, pass_argv
):
    """
    Test that overriding type_cast_value is supported

    In particular, the argument is never passed an UNSET sentinel value.
    """

    class CustomArgument(click.Argument):
        def type_cast_value(self, ctx, value):
            assert value is not UNSET
            return value

    @click.command()
    @click.argument("myarg", **argument_kwargs, cls=CustomArgument)
    def cmd(myarg):
        click.echo("ok")

    result = runner.invoke(cmd, pass_argv)
    assert not result.exception
    assert result.exit_code == 0

```
