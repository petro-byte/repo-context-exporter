# Repository Context Part 4/7

Generated for LLM prompt context.

## src/click/shell_completion.py

```python
from __future__ import annotations

import collections.abc as cabc
import os
import re
import typing as t
from gettext import gettext as _

from .core import Argument
from .core import Command
from .core import Context
from .core import Group
from .core import Option
from .core import Parameter
from .core import ParameterSource
from .utils import echo


def shell_complete(
    cli: Command,
    ctx_args: cabc.MutableMapping[str, t.Any],
    prog_name: str,
    complete_var: str,
    instruction: str,
) -> int:
    """Perform shell completion for the given CLI program.

    :param cli: Command being called.
    :param ctx_args: Extra arguments to pass to
        ``cli.make_context``.
    :param prog_name: Name of the executable in the shell.
    :param complete_var: Name of the environment variable that holds
        the completion instruction.
    :param instruction: Value of ``complete_var`` with the completion
        instruction and shell, in the form ``instruction_shell``.
    :return: Status code to exit with.
    """
    shell, _, instruction = instruction.partition("_")
    comp_cls = get_completion_class(shell)

    if comp_cls is None:
        return 1

    comp = comp_cls(cli, ctx_args, prog_name, complete_var)

    # Write bytes, otherwise Windows text stdout translates LF to CRLF and breaks.
    if instruction == "source":
        echo(comp.source().encode(), nl=False)
        return 0

    if instruction == "complete":
        echo(comp.complete().encode())
        return 0

    return 1


class CompletionItem:
    """Represents a completion value and metadata about the value. The
    default metadata is ``type`` to indicate special shell handling,
    and ``help`` if a shell supports showing a help string next to the
    value.

    Arbitrary parameters can be passed when creating the object, and
    accessed using ``item.attr``. If an attribute wasn't passed,
    accessing it returns ``None``.

    :param value: The completion suggestion.
    :param type: Tells the shell script to provide special completion
        support for the type. Click uses ``"dir"`` and ``"file"``.
    :param help: String shown next to the value if supported.
    :param kwargs: Arbitrary metadata. The built-in implementations
        don't use this, but custom type completions paired with custom
        shell support could use it.
    """

    __slots__ = ("value", "type", "help", "_info")

    def __init__(
        self,
        value: t.Any,
        type: str = "plain",
        help: str | None = None,
        **kwargs: t.Any,
    ) -> None:
        self.value: t.Any = value
        self.type: str = type
        self.help: str | None = help
        self._info = kwargs

    def __getattr__(self, name: str) -> t.Any:
        return self._info.get(name)


# Only Bash >= 4.4 has the nosort option.
_SOURCE_BASH = """\
%(complete_func)s() {
    local IFS=$'\\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD \
%(complete_var)s=bash_complete $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

%(complete_func)s_setup() {
    complete -o nosort -F %(complete_func)s %(prog_name)s
}

%(complete_func)s_setup;
"""

# See ZshComplete.format_completion below, and issue #2703, before
# changing this script.
#
# (TL;DR: _describe is picky about the format, but this Zsh script snippet
# is already widely deployed.  So freeze this script, and use clever-ish
# handling of colons in ZshComplet.format_completion.)
_SOURCE_ZSH = """\
#compdef %(prog_name)s

%(complete_func)s() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[%(prog_name)s] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) \
%(complete_var)s=zsh_complete %(prog_name)s)}")

    for type key descr in ${response}; do
        if [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
            fi
        elif [[ "$type" == "dir" ]]; then
            _path_files -/
        elif [[ "$type" == "file" ]]; then
            _path_files -f
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
    # autoload from fpath, call function directly
    %(complete_func)s "$@"
else
    # eval/source/. command, register function for later
    compdef %(complete_func)s %(prog_name)s
fi
"""

_SOURCE_FISH = """\
function %(complete_func)s;
    set -l response (env %(complete_var)s=fish_complete COMP_WORDS=(commandline -cp) \
COMP_CWORD=(commandline -t) %(prog_name)s);

    for completion in $response;
        set -l metadata (string split \n $completion);

        if test $metadata[1] = "dir";
            __fish_complete_directories $metadata[2];
        else if test $metadata[1] = "file";
            __fish_complete_path $metadata[2];
        else if test $metadata[1] = "plain";
            if test $metadata[3] != "_";
                echo $metadata[2]\t$metadata[3];
            else;
                echo $metadata[2];
            end;
        end;
    end;
end;

complete --no-files --command %(prog_name)s --arguments \
"(%(complete_func)s)";
"""


class ShellComplete:
    """Base class for providing shell completion support. A subclass for
    a given shell will override attributes and methods to implement the
    completion instructions (``source`` and ``complete``).

    :param cli: Command being called.
    :param prog_name: Name of the executable in the shell.
    :param complete_var: Name of the environment variable that holds
        the completion instruction.

    .. versionadded:: 8.0
    """

    name: t.ClassVar[str]
    """Name to register the shell as with :func:`add_completion_class`.
    This is used in completion instructions (``{name}_source`` and
    ``{name}_complete``).
    """

    source_template: t.ClassVar[str]
    """Completion script template formatted by :meth:`source`. This must
    be provided by subclasses.
    """

    def __init__(
        self,
        cli: Command,
        ctx_args: cabc.MutableMapping[str, t.Any],
        prog_name: str,
        complete_var: str,
    ) -> None:
        self.cli = cli
        self.ctx_args = ctx_args
        self.prog_name = prog_name
        self.complete_var = complete_var

    @property
    def func_name(self) -> str:
        """The name of the shell function defined by the completion
        script.
        """
        safe_name = re.sub(r"\W*", "", self.prog_name.replace("-", "_"), flags=re.ASCII)
        return f"_{safe_name}_completion"

    def source_vars(self) -> dict[str, t.Any]:
        """Vars for formatting :attr:`source_template`.

        By default this provides ``complete_func``, ``complete_var``,
        and ``prog_name``.
        """
        return {
            "complete_func": self.func_name,
            "complete_var": self.complete_var,
            "prog_name": self.prog_name,
        }

    def source(self) -> str:
        """Produce the shell script that defines the completion
        function. By default this ``%``-style formats
        :attr:`source_template` with the dict returned by
        :meth:`source_vars`.
        """
        return self.source_template % self.source_vars()

    def get_completion_args(self) -> tuple[list[str], str]:
        """Use the env vars defined by the shell script to return a
        tuple of ``args, incomplete``. This must be implemented by
        subclasses.
        """
        raise NotImplementedError

    def get_completions(self, args: list[str], incomplete: str) -> list[CompletionItem]:
        """Determine the context and last complete command or parameter
        from the complete args. Call that object's ``shell_complete``
        method to get the completions for the incomplete value.

        :param args: List of complete args before the incomplete value.
        :param incomplete: Value being completed. May be empty.
        """
        ctx = _resolve_context(self.cli, self.ctx_args, self.prog_name, args)
        obj, incomplete = _resolve_incomplete(ctx, args, incomplete)
        return obj.shell_complete(ctx, incomplete)

    def format_completion(self, item: CompletionItem) -> str:
        """Format a completion item into the form recognized by the
        shell script. This must be implemented by subclasses.

        :param item: Completion item to format.
        """
        raise NotImplementedError

    def complete(self) -> str:
        """Produce the completion data to send back to the shell.

        By default this calls :meth:`get_completion_args`, gets the
        completions, then calls :meth:`format_completion` for each
        completion.
        """
        args, incomplete = self.get_completion_args()
        completions = self.get_completions(args, incomplete)
        out = [self.format_completion(item) for item in completions]
        return "\n".join(out)


class BashComplete(ShellComplete):
    """Shell completion for Bash."""

    name = "bash"
    source_template = _SOURCE_BASH

    @staticmethod
    def _check_version() -> None:
        import shutil
        import subprocess

        bash_exe = shutil.which("bash")

        if bash_exe is None:
            match = None
        else:
            output = subprocess.run(
                [bash_exe, "--norc", "-c", 'echo "${BASH_VERSION}"'],
                stdout=subprocess.PIPE,
            )
            match = re.search(r"^(\d+)\.(\d+)\.\d+", output.stdout.decode())

        if match is not None:
            major, minor = match.groups()

            if major < "4" or major == "4" and minor < "4":
                echo(
                    _(
                        "Shell completion is not supported for Bash"
                        " versions older than 4.4."
                    ),
                    err=True,
                )
        else:
            echo(
                _("Couldn't detect Bash version, shell completion is not supported."),
                err=True,
            )

    def source(self) -> str:
        self._check_version()
        return super().source()

    def get_completion_args(self) -> tuple[list[str], str]:
        cwords = split_arg_string(os.environ["COMP_WORDS"])
        cword = int(os.environ["COMP_CWORD"])
        args = cwords[1:cword]

        try:
            incomplete = cwords[cword]
        except IndexError:
            incomplete = ""

        return args, incomplete

    def format_completion(self, item: CompletionItem) -> str:
        return f"{item.type},{item.value}"


class ZshComplete(ShellComplete):
    """Shell completion for Zsh."""

    name = "zsh"
    source_template = _SOURCE_ZSH

    def get_completion_args(self) -> tuple[list[str], str]:
        cwords = split_arg_string(os.environ["COMP_WORDS"])
        cword = int(os.environ["COMP_CWORD"])
        args = cwords[1:cword]

        try:
            incomplete = cwords[cword]
        except IndexError:
            incomplete = ""

        return args, incomplete

    def format_completion(self, item: CompletionItem) -> str:
        help_ = item.help or "_"
        # The zsh completion script uses `_describe` on items with help
        # texts (which splits the item help from the item value at the
        # first unescaped colon) and `compadd` on items without help
        # text (which uses the item value as-is and does not support
        # colon escaping).  So escape colons in the item value if and
        # only if the item help is not the sentinel "_" value, as used
        # by the completion script.
        #
        # (The zsh completion script is potentially widely deployed, and
        # thus harder to fix than this method.)
        #
        # See issue #1812 and issue #2703 for further context.
        value = item.value.replace(":", r"\:") if help_ != "_" else item.value
        return f"{item.type}\n{value}\n{help_}"


class FishComplete(ShellComplete):
    """Shell completion for Fish."""

    name = "fish"
    source_template = _SOURCE_FISH

    def get_completion_args(self) -> tuple[list[str], str]:
        cwords = split_arg_string(os.environ["COMP_WORDS"])
        incomplete = os.environ["COMP_CWORD"]
        if incomplete:
            incomplete = split_arg_string(incomplete)[0]
        args = cwords[1:]

        # Fish stores the partial word in both COMP_WORDS and
        # COMP_CWORD, remove it from complete args.
        if incomplete and args and args[-1] == incomplete:
            args.pop()

        return args, incomplete

    def format_completion(self, item: CompletionItem) -> str:
        """
        .. versionchanged:: 8.4
            Escape newlines in value and help to fix completion errors with
            multi-line help strings.
        """
        # The fish completion script splits each response line on literal
        # newlines, so any newline in the value or help would corrupt the
        # frame. Replace them with the two-character escape "\n" so the text
        # round-trips through fish without breaking the format. The "_"
        # sentinel for missing help mirrors :class:`ZshComplete`.
        help_ = item.help or "_"
        value = item.value.replace("\n", r"\n")
        help_escaped = help_.replace("\n", r"\n")
        return f"{item.type}\n{value}\n{help_escaped}"


ShellCompleteType = t.TypeVar("ShellCompleteType", bound="type[ShellComplete]")


_available_shells: dict[str, type[ShellComplete]] = {
    "bash": BashComplete,
    "fish": FishComplete,
    "zsh": ZshComplete,
}


def add_completion_class(
    cls: ShellCompleteType, name: str | None = None
) -> ShellCompleteType:
    """Register a :class:`ShellComplete` subclass under the given name.
    The name will be provided by the completion instruction environment
    variable during completion.

    :param cls: The completion class that will handle completion for the
        shell.
    :param name: Name to register the class under. Defaults to the
        class's ``name`` attribute.
    """
    if name is None:
        name = cls.name

    _available_shells[name] = cls

    return cls


def get_completion_class(shell: str) -> type[ShellComplete] | None:
    """Look up a registered :class:`ShellComplete` subclass by the name
    provided by the completion instruction environment variable. If the
    name isn't registered, returns ``None``.

    :param shell: Name the class is registered under.
    """
    return _available_shells.get(shell)


def split_arg_string(string: str) -> list[str]:
    """Split an argument string as with :func:`shlex.split`, but don't
    fail if the string is incomplete. Ignores a missing closing quote or
    incomplete escape sequence and uses the partial token as-is.

    .. code-block:: python

        split_arg_string("example 'my file")
        ["example", "my file"]

        split_arg_string("example my\\")
        ["example", "my"]

    :param string: String to split.

    .. versionchanged:: 8.2
        Moved to ``shell_completion`` from ``parser``.
    """
    import shlex

    lex = shlex.shlex(string, posix=True)
    lex.whitespace_split = True
    lex.commenters = ""
    out = []

    try:
        for token in lex:
            out.append(token)
    except ValueError:
        # Raised when end-of-string is reached in an invalid state. Use
        # the partial token as-is. The quote or escape character is in
        # lex.state, not lex.token.
        out.append(lex.token)

    return out


def _is_incomplete_argument(ctx: Context, param: Parameter) -> bool:
    """Determine if the given parameter is an argument that can still
    accept values.

    :param ctx: Invocation context for the command represented by the
        parsed complete args.
    :param param: Argument object being checked.
    """
    if not isinstance(param, Argument):
        return False

    value = ctx.params.get(param.name)
    return (
        param.nargs == -1
        or ctx.get_parameter_source(param.name) is not ParameterSource.COMMANDLINE
        or (
            param.nargs > 1
            and isinstance(value, (tuple, list))
            and len(value) < param.nargs
        )
    )


def _start_of_option(ctx: Context, value: str) -> bool:
    """Check if the value looks like the start of an option."""
    if not value:
        return False

    c = value[0]
    return c in ctx._opt_prefixes


def _is_incomplete_option(ctx: Context, args: list[str], param: Parameter) -> bool:
    """Determine if the given parameter is an option that needs a value.

    :param args: List of complete args before the incomplete value.
    :param param: Option object being checked.
    """
    if not isinstance(param, Option):
        return False

    if param.is_flag or param.count:
        return False

    last_option = None

    for index, arg in enumerate(reversed(args)):
        if index + 1 > param.nargs:
            break

        if _start_of_option(ctx, arg):
            last_option = arg
            break

    return last_option is not None and last_option in param.opts


def _resolve_context(
    cli: Command,
    ctx_args: cabc.MutableMapping[str, t.Any],
    prog_name: str,
    args: list[str],
) -> Context:
    """Produce the context hierarchy starting with the command and
    traversing the complete arguments. This only follows the commands,
    it doesn't trigger input prompts or callbacks.

    :param cli: Command being called.
    :param prog_name: Name of the executable in the shell.
    :param args: List of complete args before the incomplete value.
    """
    ctx_args["resilient_parsing"] = True
    with cli.make_context(prog_name, args.copy(), **ctx_args) as ctx:
        args = ctx._protected_args + ctx.args

        while args:
            command = ctx.command

            if isinstance(command, Group):
                if not command.chain:
                    name, cmd, args = command.resolve_command(ctx, args)

                    if cmd is None:
                        return ctx

                    with cmd.make_context(
                        name, args, parent=ctx, resilient_parsing=True
                    ) as sub_ctx:
                        ctx = sub_ctx
                        args = ctx._protected_args + ctx.args
                else:
                    sub_ctx = ctx

                    while args:
                        name, cmd, args = command.resolve_command(ctx, args)

                        if cmd is None:
                            return ctx

                        with cmd.make_context(
                            name,
                            args,
                            parent=ctx,
                            allow_extra_args=True,
                            allow_interspersed_args=False,
                            resilient_parsing=True,
                        ) as sub_sub_ctx:
                            sub_ctx = sub_sub_ctx
                            args = sub_ctx.args

                    ctx = sub_ctx
                    args = [*sub_ctx._protected_args, *sub_ctx.args]
            else:
                break

    return ctx


def _resolve_incomplete(
    ctx: Context, args: list[str], incomplete: str
) -> tuple[Command | Parameter, str]:
    """Find the Click object that will handle the completion of the
    incomplete value. Return the object and the incomplete value.

    :param ctx: Invocation context for the command represented by
        the parsed complete args.
    :param args: List of complete args before the incomplete value.
    :param incomplete: Value being completed. May be empty.
    """
    # Different shells treat an "=" between a long option name and
    # value differently. Might keep the value joined, return the "="
    # as a separate item, or return the split name and value. Always
    # split and discard the "=" to make completion easier.
    if incomplete == "=":
        incomplete = ""
    elif "=" in incomplete and _start_of_option(ctx, incomplete):
        name, _, incomplete = incomplete.partition("=")
        args.append(name)

    # The "--" marker tells Click to stop treating values as options
    # even if they start with the option character. If it hasn't been
    # given and the incomplete arg looks like an option, the current
    # command will provide option name completions.
    if "--" not in args and _start_of_option(ctx, incomplete):
        return ctx.command, incomplete

    params = ctx.command.get_params(ctx)

    # If the last complete arg is an option name with an incomplete
    # value, the option will provide value completions.
    for param in params:
        if _is_incomplete_option(ctx, args, param):
            return param, incomplete

    # It's not an option name or value. The first argument without a
    # parsed value will provide value completions.
    for param in params:
        if _is_incomplete_argument(ctx, param):
            return param, incomplete

    # There were no unparsed arguments, the command may be a group that
    # will provide command name completions.
    return ctx.command, incomplete

```
---

## src/click/termui.py

```python
from __future__ import annotations

import collections.abc as cabc
import inspect
import io
import itertools
import re
import sys
import typing as t
from contextlib import AbstractContextManager
from contextlib import redirect_stdout
from gettext import gettext as _

from ._compat import isatty
from ._compat import strip_ansi
from ._compat import WIN
from .exceptions import Abort
from .exceptions import UsageError
from .globals import resolve_color_default
from .types import Choice
from .types import convert_type
from .types import ParamType
from .utils import echo
from .utils import LazyFile

if t.TYPE_CHECKING:
    from ._termui_impl import ProgressBar

V = t.TypeVar("V")

# The prompt functions to use.  The doc tools currently override these
# functions to customize how they work.
visible_prompt_func: t.Callable[[str], str] = input

_ansi_colors = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "reset": 39,
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}
_ansi_reset_all = "\033[0m"


_HIDDEN_INPUT_MASK = "'***'"


def _mask_hidden_input(message: str, value: str) -> str:
    """Replace occurrences of ``value`` in ``message`` with a fixed mask.

    Both ``repr(value)`` (the form built-in :class:`ParamType` errors use
    via ``{value!r}``) and the raw value are masked. The raw-value pass
    uses word-boundary lookarounds so a substring like ``"1"`` does not
    match inside ``"10"``, and ``"ent"`` does not match inside
    ``"Authentication"``. The empty string is skipped to avoid matching
    at every boundary.
    """
    message = message.replace(repr(value), _HIDDEN_INPUT_MASK)
    if value:
        message = re.sub(
            rf"(?<!\w){re.escape(value)}(?!\w)", _HIDDEN_INPUT_MASK, message
        )
    return message


def hidden_prompt_func(prompt: str) -> str:
    import getpass

    return getpass.getpass(prompt)


def _readline_prompt(func: t.Callable[[str], str], text: str, err: bool) -> str:
    """Call a prompt function, passing the full prompt on non-Windows so
    readline can handle line editing and cursor positioning correctly.

    On Windows the prompt is written separately via :func:`echo` for
    colorama support, with only the last character passed to *func*.
    """
    if WIN:
        # Write the prompt separately so that we get nice coloring
        # through colorama on Windows.
        echo(text[:-1], nl=False, err=err)
        # Echo the last character to stdout to work around an issue
        # where readline causes backspace to clear the whole line.
        return func(text[-1:])
    if err:
        with redirect_stdout(sys.stderr):
            return func(text)
    return func(text)


def _build_prompt(
    text: str,
    suffix: str,
    show_default: bool | str = False,
    default: t.Any | None = None,
    show_choices: bool = True,
    type: ParamType[t.Any] | None = None,
) -> str:
    prompt = text
    if type is not None and show_choices and isinstance(type, Choice):
        prompt += f" ({', '.join(map(str, type.choices))})"
    if isinstance(show_default, str):
        default = f"({show_default})"
    if default is not None and show_default:
        prompt = f"{prompt} [{_format_default(default)}]"
    return f"{prompt}{suffix}"


def _format_default(default: t.Any) -> t.Any:
    if isinstance(default, (io.IOBase, LazyFile)) and hasattr(default, "name"):
        return default.name

    return default


def prompt(
    text: str,
    default: t.Any | None = None,
    hide_input: bool = False,
    confirmation_prompt: bool | str = False,
    type: ParamType[t.Any] | t.Any | None = None,
    value_proc: t.Callable[[str], t.Any] | None = None,
    prompt_suffix: str = ": ",
    show_default: bool | str = True,
    err: bool = False,
    show_choices: bool = True,
) -> t.Any:
    """Prompts a user for input.  This is a convenience function that can
    be used to prompt a user for input later.

    If the user aborts the input by sending an interrupt signal, this
    function will catch it and raise a :exc:`Abort` exception.

    :param text: the text to show for the prompt.
    :param default: the default value to use if no input happens.  If this
                    is not given it will prompt until it's aborted.
    :param hide_input: if this is set to true then the input value will
                       be hidden.
    :param confirmation_prompt: Prompt a second time to confirm the
        value. Can be set to a string instead of ``True`` to customize
        the message.
    :param type: the type to use to check the value against.
    :param value_proc: if this parameter is provided it's a function that
                       is invoked instead of the type conversion to
                       convert a value.
    :param prompt_suffix: a suffix that should be added to the prompt.
    :param show_default: shows or hides the default value in the prompt.
                         If this value is a string, it shows that string
                         in parentheses instead of the actual value.
    :param err: if set to true the file defaults to ``stderr`` instead of
                ``stdout``, the same as with echo.
    :param show_choices: Show or hide choices if the passed type is a Choice.
                         For example if type is a Choice of either day or week,
                         show_choices is true and text is "Group by" then the
                         prompt will be "Group by (day, week): ".

    .. versionchanged:: 8.3.3
        ``show_default`` can be a string to show a custom value instead
        of the actual default, matching the help text behavior.

    .. versionchanged:: 8.3.1
        A space is no longer appended to the prompt.

    .. versionadded:: 8.0
        ``confirmation_prompt`` can be a custom string.

    .. versionadded:: 7.0
        Added the ``show_choices`` parameter.

    .. versionadded:: 6.0
        Added unicode support for cmd.exe on Windows.

    .. versionadded:: 4.0
        Added the `err` parameter.

    """

    def prompt_func(text: str) -> str:
        f = hidden_prompt_func if hide_input else visible_prompt_func
        try:
            return _readline_prompt(f, text, err)
        except (KeyboardInterrupt, EOFError):
            # getpass doesn't print a newline if the user aborts input with ^C.
            # Allegedly this behavior is inherited from getpass(3).
            # A doc bug has been filed at https://bugs.python.org/issue24711
            if hide_input:
                echo(None, err=err)
            raise Abort() from None

    if value_proc is None:
        value_proc = convert_type(type, default)

    prompt = _build_prompt(
        text, prompt_suffix, show_default, default, show_choices, type
    )

    if confirmation_prompt:
        if confirmation_prompt is True:
            confirmation_prompt = _("Repeat for confirmation")

        confirmation_prompt = _build_prompt(confirmation_prompt, prompt_suffix)

    while True:
        while True:
            value = prompt_func(prompt)
            if value:
                break
            elif default is not None:
                value = default
                break
        try:
            result = value_proc(value)
        except UsageError as e:
            message = _mask_hidden_input(e.message, value) if hide_input else e.message
            echo(_("Error: {message}").format(message=message), err=err)
            continue
        if not confirmation_prompt:
            return result
        while True:
            value2 = prompt_func(confirmation_prompt)
            is_empty = not value and not value2
            if value2 or is_empty:
                break
        if value == value2:
            return result
        echo(_("Error: The two entered values do not match."), err=err)


def confirm(
    text: str,
    default: bool | None = False,
    abort: bool = False,
    prompt_suffix: str = ": ",
    show_default: bool = True,
    err: bool = False,
) -> bool:
    """Prompts for confirmation (yes/no question).

    If the user aborts the input by sending a interrupt signal this
    function will catch it and raise a :exc:`Abort` exception.

    :param text: the question to ask.
    :param default: The default value to use when no input is given. If
        ``None``, repeat until input is given.
    :param abort: if this is set to `True` a negative answer aborts the
                  exception by raising :exc:`Abort`.
    :param prompt_suffix: a suffix that should be added to the prompt.
    :param show_default: shows or hides the default value in the prompt.
    :param err: if set to true the file defaults to ``stderr`` instead of
                ``stdout``, the same as with echo.

    .. versionchanged:: 8.3.1
        A space is no longer appended to the prompt.

    .. versionchanged:: 8.0
        Repeat until input is given if ``default`` is ``None``.

    .. versionadded:: 4.0
        Added the ``err`` parameter.
    """
    prompt = _build_prompt(
        text,
        prompt_suffix,
        show_default,
        "y/n" if default is None else ("Y/n" if default else "y/N"),
    )

    while True:
        try:
            value = _readline_prompt(visible_prompt_func, prompt, err).lower().strip()
        except (KeyboardInterrupt, EOFError):
            raise Abort() from None
        if value in ("y", "yes"):
            rv = True
        elif value in ("n", "no"):
            rv = False
        elif default is not None and value == "":
            rv = default
        else:
            echo(_("Error: invalid input"), err=err)
            continue
        break
    if abort and not rv:
        raise Abort()
    return rv


def get_pager_file(
    color: bool | None = None,
) -> t.ContextManager[t.TextIO]:
    """Context manager.

    Yields a writable file-like object which can be used as an output pager.

    .. versionadded:: 8.2

    :param color: controls if the pager supports ANSI colors or not.  The
                  default is autodetection.
    """
    from ._termui_impl import get_pager_file

    color = resolve_color_default(color)

    return get_pager_file(color=color)


def echo_via_pager(
    text_or_generator: cabc.Iterable[str] | t.Callable[[], cabc.Iterable[str]] | str,
    color: bool | None = None,
) -> None:
    """This function takes a text and shows it via an environment specific
    pager on stdout.

    .. versionchanged:: 3.0
       Added the `color` flag.

    :param text_or_generator: the text to page, or alternatively, a
                              generator emitting the text to page.
    :param color: controls if the pager supports ANSI colors or not.  The
                  default is autodetection.
    """

    if inspect.isgeneratorfunction(text_or_generator):
        i = t.cast("t.Callable[[], cabc.Iterable[str]]", text_or_generator)()
    elif isinstance(text_or_generator, str):
        i = [text_or_generator]
    else:
        i = iter(t.cast("cabc.Iterable[str]", text_or_generator))

    # convert every element of i to a text type if necessary
    text_generator = (el if isinstance(el, str) else str(el) for el in i)

    with get_pager_file(color=color) as pager:
        for text in itertools.chain(text_generator, "\n"):
            pager.write(text)


@t.overload
def progressbar(
    *,
    length: int,
    label: str | None = None,
    hidden: bool = False,
    show_eta: bool = True,
    show_percent: bool | None = None,
    show_pos: bool = False,
    fill_char: str = "#",
    empty_char: str = "-",
    bar_template: str = "%(label)s  [%(bar)s]  %(info)s",
    info_sep: str = "  ",
    width: int = 36,
    file: t.TextIO | None = None,
    color: bool | None = None,
    update_min_steps: int = 1,
) -> ProgressBar[int]: ...


@t.overload
def progressbar(
    iterable: cabc.Iterable[V] | None = None,
    length: int | None = None,
    label: str | None = None,
    hidden: bool = False,
    show_eta: bool = True,
    show_percent: bool | None = None,
    show_pos: bool = False,
    item_show_func: t.Callable[[V | None], str | None] | None = None,
    fill_char: str = "#",
    empty_char: str = "-",
    bar_template: str = "%(label)s  [%(bar)s]  %(info)s",
    info_sep: str = "  ",
    width: int = 36,
    file: t.TextIO | None = None,
    color: bool | None = None,
    update_min_steps: int = 1,
) -> ProgressBar[V]: ...


def progressbar(
    iterable: cabc.Iterable[V] | None = None,
    length: int | None = None,
    label: str | None = None,
    hidden: bool = False,
    show_eta: bool = True,
    show_percent: bool | None = None,
    show_pos: bool = False,
    item_show_func: t.Callable[[V | None], str | None] | None = None,
    fill_char: str = "#",
    empty_char: str = "-",
    bar_template: str = "%(label)s  [%(bar)s]  %(info)s",
    info_sep: str = "  ",
    width: int = 36,
    file: t.TextIO | None = None,
    color: bool | None = None,
    update_min_steps: int = 1,
) -> ProgressBar[V]:
    """This function creates an iterable context manager that can be used
    to iterate over something while showing a progress bar.  It will
    either iterate over the `iterable` or `length` items (that are counted
    up).  While iteration happens, this function will print a rendered
    progress bar to the given `file` (defaults to stdout) and will attempt
    to calculate remaining time and more.  By default, this progress bar
    will not be rendered if the file is not a terminal.

    The context manager creates the progress bar.  When the context
    manager is entered the progress bar is already created.  With every
    iteration over the progress bar, the iterable passed to the bar is
    advanced and the bar is updated.  When the context manager exits,
    a newline is printed and the progress bar is finalized on screen.

    Note: The progress bar is currently designed for use cases where the
    total progress can be expected to take at least several seconds.
    Because of this, the ProgressBar class object won't display
    progress that is considered too fast, and progress where the time
    between steps is less than a second.

    No printing must happen or the progress bar will be unintentionally
    destroyed.

    Example usage::

        with progressbar(items) as bar:
            for item in bar:
                do_something_with(item)

    Alternatively, if no iterable is specified, one can manually update the
    progress bar through the `update()` method instead of directly
    iterating over the progress bar.  The update method accepts the number
    of steps to increment the bar with::

        with progressbar(length=chunks.total_bytes) as bar:
            for chunk in chunks:
                process_chunk(chunk)
                bar.update(chunks.bytes)

    The ``update()`` method also takes an optional value specifying the
    ``current_item`` at the new position. This is useful when used
    together with ``item_show_func`` to customize the output for each
    manual step::

        with click.progressbar(
            length=total_size,
            label='Unzipping archive',
            item_show_func=lambda a: a.filename
        ) as bar:
            for archive in zip_file:
                archive.extract()
                bar.update(archive.size, archive)

    :param iterable: an iterable to iterate over.  If not provided the length
                     is required.
    :param length: the number of items to iterate over.  By default the
                   progressbar will attempt to ask the iterator about its
                   length, which might or might not work.  If an iterable is
                   also provided this parameter can be used to override the
                   length.  If an iterable is not provided the progress bar
                   will iterate over a range of that length.
    :param label: the label to show next to the progress bar.
    :param hidden: hide the progressbar. Defaults to ``False``. When no tty is
        detected, it will only print the progressbar label. Setting this to
        ``False`` also disables that.
    :param show_eta: enables or disables the estimated time display.  This is
                     automatically disabled if the length cannot be
                     determined.
    :param show_percent: enables or disables the percentage display.  The
                         default is `True` if the iterable has a length or
                         `False` if not.
    :param show_pos: enables or disables the absolute position display.  The
                     default is `False`.
    :param item_show_func: A function called with the current item which
        can return a string to show next to the progress bar. If the
        function returns ``None`` nothing is shown. The current item can
        be ``None``, such as when entering and exiting the bar.
    :param fill_char: the character to use to show the filled part of the
                      progress bar.
    :param empty_char: the character to use to show the non-filled part of
                       the progress bar.
    :param bar_template: the format string to use as template for the bar.
                         The parameters in it are ``label`` for the label,
                         ``bar`` for the progress bar and ``info`` for the
                         info section.
    :param info_sep: the separator between multiple info items (eta etc.)
    :param width: the width of the progress bar in characters, 0 means full
                  terminal width
    :param file: The file to write to. If this is not a terminal then
        only the label is printed.
    :param color: controls if the terminal supports ANSI colors or not.  The
                  default is autodetection.  This is only needed if ANSI
                  codes are included anywhere in the progress bar output
                  which is not the case by default.
    :param update_min_steps: Render only when this many updates have
        completed. This allows tuning for very fast iterators.

    .. versionadded:: 8.2
        The ``hidden`` argument.

    .. versionchanged:: 8.0
        Output is shown even if execution time is less than 0.5 seconds.

    .. versionchanged:: 8.0
        ``item_show_func`` shows the current item, not the previous one.

    .. versionchanged:: 8.0
        Labels are echoed if the output is not a TTY. Reverts a change
        in 7.0 that removed all output.

    .. versionadded:: 8.0
       The ``update_min_steps`` parameter.

    .. versionadded:: 4.0
        The ``color`` parameter and ``update`` method.

    .. versionadded:: 2.0
    """
    from ._termui_impl import ProgressBar

    color = resolve_color_default(color)
    return ProgressBar(
        iterable=iterable,
        length=length,
        hidden=hidden,
        show_eta=show_eta,
        show_percent=show_percent,
        show_pos=show_pos,
        item_show_func=item_show_func,
        fill_char=fill_char,
        empty_char=empty_char,
        bar_template=bar_template,
        info_sep=info_sep,
        file=file,
        label=label,
        width=width,
        color=color,
        update_min_steps=update_min_steps,
    )


def clear() -> None:
    """Clears the terminal screen.  This will have the effect of clearing
    the whole visible space of the terminal and moving the cursor to the
    top left.  This does not do anything if not connected to a terminal.

    .. versionadded:: 2.0
    """
    if not isatty(sys.stdout):
        return

    # ANSI escape \033[2J clears the screen, \033[1;1H moves the cursor
    echo("\033[2J\033[1;1H", nl=False)


def _interpret_color(color: int | tuple[int, int, int] | str, offset: int = 0) -> str:
    if isinstance(color, int):
        return f"{38 + offset};5;{color:d}"

    if isinstance(color, (tuple, list)):
        r, g, b = color
        return f"{38 + offset};2;{r:d};{g:d};{b:d}"

    return str(_ansi_colors[color] + offset)


def style(
    text: t.Any,
    fg: int | tuple[int, int, int] | str | None = None,
    bg: int | tuple[int, int, int] | str | None = None,
    bold: bool | None = None,
    dim: bool | None = None,
    underline: bool | None = None,
    overline: bool | None = None,
    italic: bool | None = None,
    blink: bool | None = None,
    reverse: bool | None = None,
    strikethrough: bool | None = None,
    reset: bool = True,
) -> str:
    """Styles a text with ANSI styles and returns the new string.  By
    default the styling is self contained which means that at the end
    of the string a reset code is issued.  This can be prevented by
    passing ``reset=False``.

    Examples::

        click.echo(click.style('Hello World!', fg='green'))
        click.echo(click.style('ATTENTION!', blink=True))
        click.echo(click.style('Some things', reverse=True, fg='cyan'))
        click.echo(click.style('More colors', fg=(255, 12, 128), bg=117))

    Supported color names:

    * ``black`` (might be a gray)
    * ``red``
    * ``green``
    * ``yellow`` (might be an orange)
    * ``blue``
    * ``magenta``
    * ``cyan``
    * ``white`` (might be light gray)
    * ``bright_black``
    * ``bright_red``
    * ``bright_green``
    * ``bright_yellow``
    * ``bright_blue``
    * ``bright_magenta``
    * ``bright_cyan``
    * ``bright_white``
    * ``reset`` (reset the color code only)

    If the terminal supports it, color may also be specified as:

    -   An integer in the interval [0, 255]. The terminal must support
        8-bit/256-color mode.
    -   An RGB tuple of three integers in [0, 255]. The terminal must
        support 24-bit/true-color mode.

    See https://en.wikipedia.org/wiki/ANSI_color and
    https://gist.github.com/XVilka/8346728 for more information.

    :param text: the string to style with ansi codes.
    :param fg: if provided this will become the foreground color.
    :param bg: if provided this will become the background color.
    :param bold: if provided this will enable or disable bold mode.
    :param dim: if provided this will enable or disable dim mode.  This is
                badly supported.
    :param underline: if provided this will enable or disable underline.
    :param overline: if provided this will enable or disable overline.
    :param italic: if provided this will enable or disable italic.
    :param blink: if provided this will enable or disable blinking.
    :param reverse: if provided this will enable or disable inverse
                    rendering (foreground becomes background and the
                    other way round).
    :param strikethrough: if provided this will enable or disable
        striking through text.
    :param reset: by default a reset-all code is added at the end of the
                  string which means that styles do not carry over.  This
                  can be disabled to compose styles.

    .. versionchanged:: 8.0
        A non-string ``message`` is converted to a string.

    .. versionchanged:: 8.0
       Added support for 256 and RGB color codes.

    .. versionchanged:: 8.0
        Added the ``strikethrough``, ``italic``, and ``overline``
        parameters.

    .. versionchanged:: 7.0
        Added support for bright colors.

    .. versionadded:: 2.0
    """
    if not isinstance(text, str):
        text = str(text)

    bits = []

    if fg:
        try:
            bits.append(f"\033[{_interpret_color(fg)}m")
        except KeyError:
            raise TypeError(_("Unknown color {colour!r}").format(colour=fg)) from None

    if bg:
        try:
            bits.append(f"\033[{_interpret_color(bg, 10)}m")
        except KeyError:
            raise TypeError(_("Unknown color {colour!r}").format(colour=bg)) from None

    if bold is not None:
        bits.append(f"\033[{1 if bold else 22}m")
    if dim is not None:
        bits.append(f"\033[{2 if dim else 22}m")
    if underline is not None:
        bits.append(f"\033[{4 if underline else 24}m")
    if overline is not None:
        bits.append(f"\033[{53 if overline else 55}m")
    if italic is not None:
        bits.append(f"\033[{3 if italic else 23}m")
    if blink is not None:
        bits.append(f"\033[{5 if blink else 25}m")
    if reverse is not None:
        bits.append(f"\033[{7 if reverse else 27}m")
    if strikethrough is not None:
        bits.append(f"\033[{9 if strikethrough else 29}m")
    bits.append(text)
    if reset:
        bits.append(_ansi_reset_all)
    return "".join(bits)


def unstyle(text: str) -> str:
    """Removes ANSI styling information from a string.  Usually it's not
    necessary to use this function as Click's echo function will
    automatically remove styling if necessary.

    .. versionadded:: 2.0

    :param text: the text to remove style information from.
    """
    return strip_ansi(text)


def secho(
    message: t.Any | None = None,
    file: t.IO[t.AnyStr] | None = None,
    nl: bool = True,
    err: bool = False,
    color: bool | None = None,
    **styles: t.Any,
) -> None:
    """This function combines :func:`echo` and :func:`style` into one
    call.  As such the following two calls are the same::

        click.secho('Hello World!', fg='green')
        click.echo(click.style('Hello World!', fg='green'))

    All keyword arguments are forwarded to the underlying functions
    depending on which one they go with.

    Non-string types will be converted to :class:`str`. However,
    :class:`bytes` are passed directly to :meth:`echo` without applying
    style. If you want to style bytes that represent text, call
    :meth:`bytes.decode` first.

    .. versionchanged:: 8.0
        A non-string ``message`` is converted to a string. Bytes are
        passed through without style applied.

    .. versionadded:: 2.0
    """
    if message is not None and not isinstance(message, (bytes, bytearray)):
        message = style(message, **styles)

    return echo(message, file=file, nl=nl, err=err, color=color)


@t.overload
def edit(
    text: bytes | bytearray,
    editor: str | None = None,
    env: cabc.Mapping[str, str] | None = None,
    require_save: bool = False,
    extension: str = ".txt",
) -> bytes | None: ...


@t.overload
def edit(
    text: str,
    editor: str | None = None,
    env: cabc.Mapping[str, str] | None = None,
    require_save: bool = True,
    extension: str = ".txt",
) -> str | None: ...


@t.overload
def edit(
    text: None = None,
    editor: str | None = None,
    env: cabc.Mapping[str, str] | None = None,
    require_save: bool = True,
    extension: str = ".txt",
    filename: str | cabc.Iterable[str] | None = None,
) -> None: ...


def edit(
    text: str | bytes | bytearray | None = None,
    editor: str | None = None,
    env: cabc.Mapping[str, str] | None = None,
    require_save: bool = True,
    extension: str = ".txt",
    filename: str | cabc.Iterable[str] | None = None,
) -> str | bytes | bytearray | None:
    r"""Edits the given text in the defined editor.  If an editor is given
    (should be the full path to the executable but the regular operating
    system search path is used for finding the executable) it overrides
    the detected editor.  Optionally, some environment variables can be
    used.  If the editor is closed without changes, `None` is returned.  In
    case a file is edited directly the return value is always `None` and
    `require_save` and `extension` are ignored.

    If the editor cannot be opened a :exc:`UsageError` is raised.

    Note for Windows: to simplify cross-platform usage, the newlines are
    automatically converted from POSIX to Windows and vice versa.  As such,
    the message here will have ``\n`` as newline markers.

    :param text: the text to edit.
    :param editor: optionally the editor to use.  Defaults to automatic
                   detection.
    :param env: environment variables to forward to the editor.
    :param require_save: if this is true, then not saving in the editor
                         will make the return value become `None`.
    :param extension: the extension to tell the editor about.  This defaults
                      to `.txt` but changing this might change syntax
                      highlighting.
    :param filename: if provided it will edit this file instead of the
                     provided text contents.  It will not use a temporary
                     file as an indirection in that case. If the editor supports
                     editing multiple files at once, a sequence of files may be
                     passed as well. Invoke `click.file` once per file instead
                     if multiple files cannot be managed at once or editing the
                     files serially is desired.

    .. versionchanged:: 8.2.0
        ``filename`` now accepts any ``Iterable[str]`` in addition to a ``str``
        if the ``editor`` supports editing multiple files at once.

    """
    from ._termui_impl import Editor

    ed = Editor(editor=editor, env=env, require_save=require_save, extension=extension)

    if filename is None:
        return ed.edit(text)

    if isinstance(filename, str):
        filename = (filename,)

    ed.edit_files(filenames=filename)
    return None


def launch(url: str, wait: bool = False, locate: bool = False) -> int:
    """This function launches the given URL (or filename) in the default
    viewer application for this file type.  If this is an executable, it
    might launch the executable in a new session.  The return value is
    the exit code of the launched application.  Usually, ``0`` indicates
    success.

    Examples::

        click.launch('https://click.palletsprojects.com/')
        click.launch('/my/downloaded/file', locate=True)

    .. versionadded:: 2.0

    :param url: URL or filename of the thing to launch.
    :param wait: Wait for the program to exit before returning. This
        only works if the launched program blocks. In particular,
        ``xdg-open`` on Linux does not block.
    :param locate: if this is set to `True` then instead of launching the
                   application associated with the URL it will attempt to
                   launch a file manager with the file located.  This
                   might have weird effects if the URL does not point to
                   the filesystem.
    """
    from ._termui_impl import open_url

    return open_url(url, wait=wait, locate=locate)


# If this is provided, getchar() calls into this instead.  This is used
# for unittesting purposes.
_getchar: t.Callable[[bool], str] | None = None


def getchar(echo: bool = False) -> str:
    """Fetches a single character from the terminal and returns it.  This
    will always return a unicode character and under certain rare
    circumstances this might return more than one character.  The
    situations which more than one character is returned is when for
    whatever reason multiple characters end up in the terminal buffer or
    standard input was not actually a terminal.

    Note that this will always read from the terminal, even if something
    is piped into the standard input.

    Note for Windows: in rare cases when typing non-ASCII characters, this
    function might wait for a second character and then return both at once.
    This is because certain Unicode characters look like special-key markers.

    .. versionadded:: 2.0

    :param echo: if set to `True`, the character read will also show up on
                 the terminal.  The default is to not show it.
    """
    global _getchar

    if _getchar is None:
        from ._termui_impl import getchar as f

        _getchar = f

    return _getchar(echo)


def raw_terminal() -> AbstractContextManager[int]:
    from ._termui_impl import raw_terminal as f

    return f()


def pause(info: str | None = None, err: bool = False) -> None:
    """This command stops execution and waits for the user to press any
    key to continue.  This is similar to the Windows batch "pause"
    command.  If the program is not run through a terminal, this command
    will instead do nothing.

    .. versionadded:: 2.0

    .. versionadded:: 4.0
       Added the `err` parameter.

    :param info: The message to print before pausing. Defaults to
        ``"Press any key to continue..."``.
    :param err: if set to message goes to ``stderr`` instead of
                ``stdout``, the same as with echo.
    """
    if not isatty(sys.stdin) or not isatty(sys.stdout):
        return

    if info is None:
        info = _("Press any key to continue...")

    try:
        if info:
            echo(info, nl=False, err=err)
        try:
            getchar()
        except (KeyboardInterrupt, EOFError):
            pass
    finally:
        if info:
            echo(err=err)

```
---

## src/click/testing.py

```python
from __future__ import annotations

import collections.abc as cabc
import contextlib
import io
import os
import pdb
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

CaptureMode = t.Literal["sys", "fd"]


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


class _FDCapture:
    """Redirect a file descriptor to a temporary file for capture.

    Saves the current target of *targetfd* via :func:`os.dup`, then
    redirects it to a temporary file via :func:`os.dup2`. On
    :meth:`stop`, restores the original ``fd`` and returns the captured
    bytes. Inspired by Pytest's ``FDCapture``.

    .. versionadded:: 8.4.0
    """

    def __init__(self, targetfd: int) -> None:
        self._targetfd = targetfd
        self.saved_fd: int = -1
        self._tmpfile: t.BinaryIO | None = None

    def start(self) -> None:
        self.saved_fd = os.dup(self._targetfd)
        self._tmpfile = tempfile.TemporaryFile(buffering=0)
        os.dup2(self._tmpfile.fileno(), self._targetfd)

    def stop(self) -> bytes:
        assert self._tmpfile is not None, "_FDCapture.start() was not called"
        os.dup2(self.saved_fd, self._targetfd)
        os.close(self.saved_fd)
        self.saved_fd = -1
        self._tmpfile.seek(0)
        data = self._tmpfile.read()
        self._tmpfile.close()
        self._tmpfile = None
        return data


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


class _NamedTextIOWrapper(io.TextIOWrapper):
    """A :class:`~io.TextIOWrapper` with custom ``name`` and ``mode``
    that does not close its underlying buffer.

    When ``CliRunner`` runs in ``fd`` mode, ``_original_fd`` is patched to
    point at the saved (pre-redirection) ``fd``, so C-level consumers that call
    :meth:`fileno` (like ``faulthandler`` or ``subprocess``) keep working. In
    the default ``sys`` mode ``_original_fd`` stays at ``-1`` and
    :meth:`fileno` raises :exc:`io.UnsupportedOperation`, matching the
    pre-``8.3.3`` behavior.
    """

    def __init__(
        self,
        buffer: t.BinaryIO,
        name: str,
        mode: str,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(buffer, **kwargs)
        self._name = name
        self._mode = mode
        self._original_fd: int = -1

    def close(self) -> None:
        """The buffer this object contains belongs to some other object,
        so prevent the default ``__del__`` implementation from closing
        that buffer.

        .. versionadded:: 8.3.2
        """

    def fileno(self) -> int:
        """Return the file descriptor of the saved original stream when
        ``CliRunner`` runs in ``fd`` mode. Otherwise delegate to
        :class:`~io.TextIOWrapper`, which raises
        :exc:`io.UnsupportedOperation` for a ``BytesIO``-backed buffer.
        """
        if self._original_fd >= 0:
            return self._original_fd
        return super().fileno()

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
    :param capture: Selects the output capture strategy. ``sys`` (default)
        captures Python-level writes only and leaves
        :meth:`sys.stdout.fileno` raising :exc:`io.UnsupportedOperation`, so
        user code that calls :func:`os.dup2` on ``sys.stdout.fileno()`` cannot
        clobber the host runner's stdout. ``fd`` redirects file descriptors
        ``1`` and ``2`` via :func:`os.dup2` to a temporary file, also catching
        output from stale stream references, C extensions, and subprocesses.
        ``fd`` is not supported on Windows.

    .. versionchanged:: 8.4.0
        Added the ``capture`` parameter. The default ``sys`` mode no longer
        exposes the original fd through :meth:`fileno`, reverting the change
        introduced in ``8.3.3`` that broke Pytest's ``fd``-level capture
        teardown. Use ``capture="fd"`` to restore that behavior with proper
        isolation. :issue:`3384`

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
        capture: CaptureMode = "sys",
    ) -> None:
        if capture not in {"sys", "fd"}:
            raise ValueError(
                f"capture={capture!r} is not valid. Choose from 'sys' or 'fd'."
            )
        if capture == "fd" and sys.platform == "win32":
            raise ValueError(
                f"capture={capture!r} is not supported on Windows. Use 'sys'."
            )
        self.charset = charset
        self.env: cabc.Mapping[str, str | None] = env or {}
        self.echo_stdin = echo_stdin
        self.catch_exceptions = catch_exceptions
        self.capture: CaptureMode = capture

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
            stream_mixer.stdout,
            encoding=self.charset,
            name="<stdout>",
            mode="w",
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
        old_pdb_init = pdb.Pdb.__init__
        termui.visible_prompt_func = visible_input
        termui.hidden_prompt_func = hidden_input
        termui._getchar = _getchar
        utils.should_strip_ansi = should_strip_ansi  # type: ignore
        _compat.should_strip_ansi = should_strip_ansi

        def _patched_pdb_init(
            self: pdb.Pdb,
            completekey: str = "tab",
            stdin: t.IO[str] | None = None,
            stdout: t.IO[str] | None = None,
            **kwargs: t.Any,
        ) -> None:
            """Default ``pdb.Pdb`` to real terminal streams during
            ``CliRunner`` isolation.

            Without this patch, ``pdb.Pdb.__init__`` inherits from
            ``cmd.Cmd`` which falls back to ``sys.stdin``/``sys.stdout``
            when no explicit streams are provided. During isolation
            those are ``BytesIO``-backed wrappers, so the debugger
            reads from an empty buffer and writes to captured output,
            making interactive debugging impossible.

            By defaulting to ``sys.__stdin__``/``sys.__stdout__`` (the
            original terminal streams Python preserves regardless of
            redirection), debuggers can interact with the user while
            ``click.echo`` output is still captured normally.

            This covers ``pdb.set_trace()``, ``breakpoint()``,
            ``pdb.post_mortem()``, and debuggers that subclass
            ``pdb.Pdb`` (ipdb, pdbpp). Explicit ``stdin``/``stdout``
            arguments are honored and not overridden. Debuggers that
            do not subclass ``pdb.Pdb`` (pudb, debugpy) are not
            covered.
            """
            if stdin is None:
                stdin = sys.__stdin__
            if stdout is None:
                stdout = sys.__stdout__
            old_pdb_init(
                self, completekey=completekey, stdin=stdin, stdout=stdout, **kwargs
            )

        pdb.Pdb.__init__ = _patched_pdb_init  # type: ignore[assignment]

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
            pdb.Pdb.__init__ = old_pdb_init  # type: ignore[method-assign]

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

        # Set up fd capture before isolation replaces sys.stdout and sys.stderr.
        cap_out: _FDCapture | None = None
        cap_err: _FDCapture | None = None

        if self.capture == "fd":
            cap_out = _FDCapture(1)
            cap_err = _FDCapture(2)
            try:
                cap_out.start()
                cap_err.start()
            except OSError:
                cap_out = cap_err = None

        with self.isolation(input=input, env=env, color=color) as outstreams:
            # Point the captured streams' fileno() at the saved (original)
            # fd so that C-level consumers like faulthandler keep working
            # while fd 1/2 are redirected to the capture tmpfile.
            if cap_out is not None and cap_err is not None:
                sys.stdout._original_fd = cap_out.saved_fd  # type: ignore[union-attr]
                sys.stderr._original_fd = cap_err.saved_fd  # type: ignore[union-attr]

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

                # Stop fd capture and merge the captured bytes into
                # the stdout/stderr BytesIO streams. BytesIOCopy mirrors
                # those writes into outstreams[2] automatically.
                if cap_out is not None and cap_err is not None:
                    fd_out = cap_out.stop()
                    fd_err = cap_err.stop()
                    if fd_out:
                        outstreams[0].write(fd_out)
                    if fd_err:
                        outstreams[1].write(fd_err)

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

import abc
import collections.abc as cabc
import enum
import os
import stat
import sys
import typing as t
import uuid
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


class ParamTypeInfoDict(t.TypedDict):
    param_type: str
    name: str


class ParamType(t.Generic[ParamTypeValue], abc.ABC):
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

    def to_info_dict(self) -> ParamTypeInfoDict:
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
    ) -> ParamTypeValue | None:
        if value is not None:
            return self.convert(value, param, ctx)
        return None

    def get_metavar(self, param: Parameter, ctx: Context) -> str | None:
        """Returns the metavar default for this param if it provides one."""

    def get_missing_message(self, param: Parameter, ctx: Context | None) -> str | None:
        """Optionally might return extra information about a missing
        parameter.

        .. versionadded:: 2.0
        """

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> ParamTypeValue:
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
        # The default returns the value as-is so subclasses that only customize
        # metadata are not forced to redeclare ``convert``.
        return t.cast("ParamTypeValue", value)

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


class CompositeParamType(ParamType[ParamTypeValue]):
    is_composite = True

    @property
    @abc.abstractmethod
    def arity(self) -> int: ...  # type: ignore[override]


class FuncParamTypeInfoDict(ParamTypeInfoDict):
    func: t.Callable[[t.Any], t.Any]


class FuncParamType(ParamType[ParamTypeValue]):
    def __init__(self, func: t.Callable[[t.Any], ParamTypeValue]) -> None:
        self.name: str = func.__name__
        self.func = func

    def to_info_dict(self) -> FuncParamTypeInfoDict:
        return {"func": self.func, **super().to_info_dict()}

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> ParamTypeValue:
        try:
            return self.func(value)
        except ValueError as exc:
            message = str(exc)

            if not message:
                try:
                    message = str(value)
                except UnicodeError:
                    message = value.decode("utf-8", "replace")

            self.fail(message, param, ctx)


class UnprocessedParamType(ParamType[t.Any]):
    name = "text"

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> t.Any:
        return value

    def __repr__(self) -> str:
        return "UNPROCESSED"


class StringParamType(ParamType[str]):
    name = "text"

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> str:
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
            return value  # type: ignore[no-any-return]
        return str(value)

    def __repr__(self) -> str:
        return "STRING"


class ChoiceInfoDict(ParamTypeInfoDict):
    choices: cabc.Sequence[t.Any]
    case_sensitive: bool


class Choice(ParamType[ParamTypeValue], t.Generic[ParamTypeValue]):
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

    def to_info_dict(self) -> ChoiceInfoDict:
        return {
            "choices": self.choices,
            "case_sensitive": self.case_sensitive,
            **super().to_info_dict(),
        }

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
        return _("Choice({choices})").format(choices=list(self.choices))

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

        str_choices = [self.normalize_choice(choice, ctx) for choice in self.choices]
        if self.case_sensitive:
            matched = (c for c in str_choices if c.startswith(incomplete))
        else:
            incomplete = incomplete.lower()
            matched = (c for c in str_choices if c.lower().startswith(incomplete))

        return [CompletionItem(c) for c in matched]


class DateTimeInfoDict(ParamTypeInfoDict):
    formats: cabc.Sequence[str]


class DateTime(ParamType[datetime]):
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

    def to_info_dict(self) -> DateTimeInfoDict:
        return {"formats": self.formats, **super().to_info_dict()}

    def get_metavar(self, param: Parameter, ctx: Context) -> str | None:
        return f"[{'|'.join(self.formats)}]"

    def _try_to_convert_date(self, value: t.Any, format: str) -> datetime | None:
        try:
            return datetime.strptime(value, format)
        except ValueError:
            return None

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> datetime:
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


class _NumberParamTypeBase(ParamType[ParamTypeValue]):
    _number_class: t.Callable[[t.Any], ParamTypeValue]

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> ParamTypeValue:
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


class NumberRangeInfoDict(ParamTypeInfoDict):
    min: float | None
    max: float | None
    min_open: bool
    max_open: bool
    clamp: bool


class _NumberRangeBase(_NumberParamTypeBase[ParamTypeValue]):
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

    def to_info_dict(self) -> NumberRangeInfoDict:
        return {
            "min": self.min,
            "max": self.max,
            "min_open": self.min_open,
            "max_open": self.max_open,
            "clamp": self.clamp,
            **super().to_info_dict(),
        }

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> ParamTypeValue:
        import operator

        rv = super().convert(value, param, ctx)
        min = self.min
        max = self.max
        lt_min: bool = min is not None and (
            operator.le if self.min_open else operator.lt
        )(rv, min)  # type: ignore[arg-type]
        gt_max: bool = max is not None and (
            operator.ge if self.max_open else operator.gt
        )(rv, max)  # type: ignore[arg-type]

        if self.clamp:
            if min is not None and lt_min:
                return self._clamp(min, 1, self.min_open)  # type: ignore[arg-type]

            if max is not None and gt_max:
                return self._clamp(max, -1, self.max_open)  # type: ignore[arg-type]

        if lt_min or gt_max:
            self.fail(
                _("{value} is not in the range {range}.").format(
                    value=rv, range=self._describe_range()
                ),
                param,
                ctx,
            )

        return rv

    @abc.abstractmethod
    def _clamp(
        self, bound: ParamTypeValue, dir: t.Literal[1, -1], open: bool
    ) -> ParamTypeValue:
        """Find the valid value to clamp to bound in the given
        direction.

        :param bound: The boundary value.
        :param dir: 1 or -1 indicating the direction to move.
        :param open: If true, the range does not include the bound.
        """
        ...

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


class IntParamType(_NumberParamTypeBase[int]):
    name = "integer"
    _number_class = int

    def __repr__(self) -> str:
        return "INT"


class IntRange(_NumberRangeBase[int], IntParamType):
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

    def _clamp(self, bound: int, dir: t.Literal[1, -1], open: bool) -> int:
        if not open:
            return bound

        return bound + dir


class FloatParamType(_NumberParamTypeBase[float]):
    name = "float"
    _number_class = float

    def __repr__(self) -> str:
        return "FLOAT"


class FloatRange(_NumberRangeBase[float], FloatParamType):
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


class BoolParamType(ParamType[bool]):
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


class UUIDParameterType(ParamType[uuid.UUID]):
    name = "uuid"

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> uuid.UUID:
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


class FileInfoDict(ParamTypeInfoDict):
    mode: str
    encoding: str | None


class File(ParamType[t.IO[t.Any]]):
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

    def to_info_dict(self) -> FileInfoDict:
        return {
            "mode": self.mode,
            "encoding": self.encoding,
            **super().to_info_dict(),
        }

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
            self.fail(
                f"'{format_filename(value)}': {e.strerror}",
                param,
                ctx,
            )

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


class PathInfoDict(ParamTypeInfoDict):
    exists: bool
    file_okay: bool
    dir_okay: bool
    writable: bool
    readable: bool
    allow_dash: bool


class Path(ParamType[str | bytes | os.PathLike[str]]):
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

    def to_info_dict(self) -> PathInfoDict:
        return {
            "exists": self.exists,
            "file_okay": self.file_okay,
            "dir_okay": self.dir_okay,
            "writable": self.writable,
            "readable": self.readable,
            "allow_dash": self.allow_dash,
            **super().to_info_dict(),
        }

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


class TupleInfoDict(ParamTypeInfoDict):
    types: cabc.Sequence[ParamTypeInfoDict]


class Tuple(CompositeParamType[tuple[t.Any, ...]]):
    """The default behavior of Click is to apply a type on a value directly.
    This works well in most cases, except for when `nargs` is set to a fixed
    count and different types should be used for different items.  In this
    case the :class:`Tuple` type can be used.  This type can only be used
    if `nargs` is set to a fixed number.

    For more information see :ref:`tuple-type`.

    This can be selected by using a Python tuple literal as a type.

    :param types: a list of types that should be used for the tuple items.
    """

    def __init__(self, types: cabc.Sequence[type[t.Any] | ParamType[t.Any]]) -> None:
        self.types: cabc.Sequence[ParamType[t.Any]] = [convert_type(ty) for ty in types]

    def to_info_dict(self) -> TupleInfoDict:
        return {
            "types": [ty.to_info_dict() for ty in self.types],
            **super().to_info_dict(),
        }

    @property
    def name(self) -> str:  # type: ignore[override]
        return f"<{' '.join(ty.name for ty in self.types)}>"

    @property
    def arity(self) -> int:  # type: ignore[override]
        return len(self.types)

    def convert(
        self, value: t.Any, param: Parameter | None, ctx: Context | None
    ) -> tuple[t.Any, ...]:
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


def _guess_type(
    ty: type[t.Any] | ParamType[t.Any] | None,
    default: t.Any | None,
) -> type[t.Any] | tuple[type[t.Any], ...] | ParamType[t.Any] | None:
    """Infer a type from *ty* or *default*.

    Returns *ty* unchanged when it is not ``None``.  Otherwise inspects
    *default* to produce a ``type``, a ``tuple`` of types (for tuple
    defaults), or ``None``.
    """
    if ty is not None:
        return ty

    if default is None:
        return None

    if not isinstance(default, (tuple, list)):
        return type(default)

    # If the default is empty, return None so convert_type falls
    # through to STRING.
    if not default:
        return None

    item = default[0]

    # A sequence of iterables needs to detect the inner types.
    # Can't call convert_type recursively because that would
    # incorrectly unwind the tuple to a single type.
    if isinstance(item, (tuple, list)):
        return tuple(map(type, item))

    return type(item)


@t.overload
def convert_type(ty: None, default: None = None) -> StringParamType: ...


@t.overload
def convert_type(
    ty: type[t.Any] | ParamType[t.Any], default: t.Any | None = None
) -> ParamType[t.Any]: ...


@t.overload
def convert_type(
    ty: t.Any | None, default: t.Any | None = None
) -> ParamType[t.Any]: ...


def convert_type(
    ty: t.Any | None = None, default: t.Any | None = None
) -> ParamType[t.Any]:
    """Find the most appropriate :class:`ParamType` for the given Python
    type. If the type isn't provided, it can be inferred from a default
    value.
    """
    guessed = _guess_type(ty, default)
    is_guessed = guessed is not ty

    if isinstance(guessed, tuple):
        return Tuple(guessed)

    if isinstance(guessed, ParamType):
        return guessed

    if guessed is str or guessed is None:
        return STRING

    if guessed is int:
        return INT

    if guessed is float:
        return FLOAT

    if guessed is bool:
        return BOOL

    if is_guessed:
        return STRING

    if __debug__:
        try:
            if issubclass(guessed, ParamType):
                raise AssertionError(
                    f"Attempted to use an uninstantiated parameter type ({guessed})."
                )
        except TypeError:
            # guessed is an instance (correct), so issubclass fails.
            pass

    return FuncParamType(guessed)


#: A dummy parameter type that just does nothing.  From a user's
#: perspective this appears to just be the same as `STRING` but
#: internally no string conversion takes place if the input was bytes.
#: This is usually useful when working with file paths as they can
#: appear in bytes and unicode.
#:
#: For path related uses the :class:`Path` type is a better choice but
#: there are situations where an unprocessed type is useful which is why
#: it is provided.
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
from gettext import gettext as _
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
    """Returns a condensed version of help string.

    :meta private:
    """
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

    name: str
    mode: str
    encoding: str | None
    errors: str | None
    atomic: bool
    _f: t.IO[t.Any] | None
    should_close: bool

    def __init__(
        self,
        filename: str | os.PathLike[str],
        mode: str = "r",
        encoding: str | None = None,
        errors: str | None = "strict",
        atomic: bool = False,
    ) -> None:
        self.name = os.fspath(filename)
        self.mode = mode
        self.encoding = encoding
        self.errors = errors
        self.atomic = atomic

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
    _file: t.IO[t.Any]

    def __init__(self, file: t.IO[t.Any]) -> None:
        self._file = file

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
        raise TypeError(_("Unknown standard stream '{name}'").format(name=name))
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
        raise TypeError(_("Unknown standard stream '{name}'").format(name=name))
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

    wrapped: t.IO[t.Any]

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
    """Comprehensive check of default-value processing for arguments with
    ``nargs``.

    .. hint::
        An option-specific equivalent is available in
        ``test_options.py::test_good_defaults_for_multiple``.

        A smoke test covering a single basic case is in
        ``test_defaults.py::test_nargs_plus_multiple``.
    """

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
---

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

    .. hint::
        Similar to ``test_options.py::test_default_dual_option_callback``.

        ``test_defaults.py::test_shared_param_prefers_first_default``
        is a smoke-test complement that exercises both default placements.
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
