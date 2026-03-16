# Repository Context Part 3/9

Generated for LLM prompt context.

## docs/support-multiple-versions.md

```markdown
# Supporting Multiple Versions

If you are a library maintainer, you may want to support multiple versions of
Click. See the Pallets [version policy] for information about our version
numbers and support policy.

[version policy]: https://palletsprojects.com/versions

Most features of Click are stable across releases, and don't require special
handling. However, feature releases may deprecate and change APIs. Occasionally,
a change will require special handling.

## Use Feature Detection

Prefer using feature detection. Looking at the version can be tempting, but is
often more brittle or results in more complicated code. Try to use `if` or `try`
blocks to decide whether to use a new or old pattern.

If you do need to look at the version, use {func}`importlib.metadata.version`,
the standardized way to get versions for any installed Python package.

## Changes in 8.2

### `ParamType` methods require `ctx`

In 8.2, several methods of `ParamType` now have a `ctx: click.Context`
argument. Because this changes the signature of the methods from 8.1, it's not
obvious how to support both when subclassing or calling.

This example uses `ParamType.get_metavar`, and the same technique should be
applicable to other methods such as `get_missing_message`.

Update your methods overrides to take the new `ctx` argument. Use the
following decorator to wrap each method. In 8.1, it will get the context where
possible and pass it using the 8.2 signature.

```python
import functools
import typing as t
import click

F = t.TypeVar("F", bound=t.Callable[..., t.Any])

def add_ctx_arg(f: F) -> F:
    @functools.wraps(f)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        if "ctx" not in kwargs:
            kwargs["ctx"] = click.get_current_context(silent=True)

        return f(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
```

Here's an example ``ParamType`` subclass which uses this:

```python
class CommaDelimitedString(click.ParamType):
    @add_ctx_arg
    def get_metavar(self, param: click.Parameter, ctx: click.Context | None) -> str:
        return "TEXT,TEXT,..."
```

```
---

## docs/testing.md

```markdown
# Testing Click Applications

```{eval-rst}
.. currentmodule:: click.testing
```

Click provides the {ref}`click.testing <testing>` module to help you invoke command line applications and check their behavior.

These tools should only be used for testing since they change
the entire interpreter state for simplicity. They are not thread-safe!

The examples use [pytest](https://docs.pytest.org/en/stable/) style tests.

```{contents}
:depth: 1
:local: true
```

## Basic Example

The key pieces are:
  - {class}`CliRunner` - used to invoke commands as command line scripts.
  - {class}`Result` - returned from {meth}`CliRunner.invoke`. Captures output data, exit code, optional exception, and captures the output as bytes and binary data.

```{code-block} python
:caption: hello.py

import click

@click.command()
@click.argument('name')
def hello(name):
   click.echo(f'Hello {name}!')
```

```{code-block} python
:caption: test_hello.py

from click.testing import CliRunner
from hello import hello

def test_hello_world():
  runner = CliRunner()
  result = runner.invoke(hello, ['Peter'])
  assert result.exit_code == 0
  assert result.output == 'Hello Peter!\n'
```

## Subcommands

A subcommand name must be specified in the `args` parameter {meth}`CliRunner.invoke`:

```{code-block} python
:caption: sync.py

import click

@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
   click.echo(f"Debug mode is {'on' if debug else 'off'}")

@cli.command()
def sync():
   click.echo('Syncing')
```

```{code-block} python
:caption: test_sync.py

from click.testing import CliRunner
from sync import cli

def test_sync():
  runner = CliRunner()
  result = runner.invoke(cli, ['--debug', 'sync'])
  assert result.exit_code == 0
  assert 'Debug mode is on' in result.output
  assert 'Syncing' in result.output
```

## Context Settings

Additional keyword arguments passed to {meth}`CliRunner.invoke` will be used to construct the initial {class}`Context object <click.Context>`.
For example, setting a fixed terminal width equal to 60:

```{code-block} python
:caption: sync.py

import click

@click.group()
def cli():
   pass

@cli.command()
def sync():
   click.echo('Syncing')
```

```{code-block} python
:caption: test_sync.py

from click.testing import CliRunner
from sync import cli

def test_sync():
  runner = CliRunner()
  result = runner.invoke(cli, ['sync'], terminal_width=60)
  assert result.exit_code == 0
  assert 'Debug mode is on' in result.output
  assert 'Syncing' in result.output
```

## File System Isolation

The {meth}`CliRunner.isolated_filesystem` context manager sets the current working directory to a new, empty folder.

```{code-block} python
:caption: cat.py

import click

@click.command()
@click.argument('f', type=click.File())
def cat(f):
   click.echo(f.read())
```

```{code-block} python
:caption: test_cat.py

from click.testing import CliRunner
from cat import cat

def test_cat():
   runner = CliRunner()
   with runner.isolated_filesystem():
      with open('hello.txt', 'w') as f:
          f.write('Hello World!')

      result = runner.invoke(cat, ['hello.txt'])
      assert result.exit_code == 0
      assert result.output == 'Hello World!\n'
```

Pass in a path to control where the temporary directory is created.
In this case, the directory will not be removed by Click. Its useful
to integrate with a framework like Pytest that manages temporary files.

```{code-block} python
:caption: test_cat.py

from click.testing import CliRunner
from cat import cat

def test_cat_with_path_specified():
   runner = CliRunner()
   with runner.isolated_filesystem('~/test_folder'):
      with open('hello.txt', 'w') as f:
          f.write('Hello World!')

      result = runner.invoke(cat, ['hello.txt'])
      assert result.exit_code == 0
      assert result.output == 'Hello World!\n'
```

## Input Streams

The test wrapper can provide input data for the input stream (stdin). This is very useful for testing prompts.

```{code-block} python
:caption: prompt.py

import click

@click.command()
@click.option('--foo', prompt=True)
def prompt(foo):
   click.echo(f"foo={foo}")
```

```{code-block} python
:caption: test_prompt.py

from click.testing import CliRunner
from prompt import prompt

def test_prompts():
   runner = CliRunner()
   result = runner.invoke(prompt, input='wau wau\n')
   assert not result.exception
   assert result.output == 'Foo: wau wau\nfoo=wau wau\n'
```

Prompts will be emulated so they write the input data to
the output stream as well. If hidden input is expected then this
does not happen.

```
---

## docs/unicode-support.md

```markdown
# Unicode Support

```{currentmodule} click
```

Click has to take extra care to support Unicode text in different environments.

- The command line in Unix is traditionally bytes, not Unicode. While there are encoding hints, there are some
  situations where this can break. The most common one is SSH connections to machines with different locales.

  Misconfigured environments can cause a wide range of Unicode problems due to the lack of support for roundtripping
  surrogate escapes. This will not be fixed in Click itself!

- Standard input and output is opened in text mode by default. Click has to reopen the stream in binary mode in certain
  situations. Because there is no standard way to do this, it might not always work. Primarily this can become a problem
  when testing command-line applications.

  This is not supported:

  ```python
  sys.stdin = io.StringIO('Input here')
  sys.stdout = io.StringIO()
  ```

  Instead you need to do this:

  ```python
  input = 'Input here'
  in_stream = io.BytesIO(input.encode('utf-8'))
  sys.stdin = io.TextIOWrapper(in_stream, encoding='utf-8')
  out_stream = io.BytesIO()
  sys.stdout = io.TextIOWrapper(out_stream, encoding='utf-8')
  ```

  Remember in that case, you need to use `out_stream.getvalue()` and not `sys.stdout.getvalue()` if you want to access
  the buffer contents as the wrapper will not forward that method.

- `sys.stdin`, `sys.stdout` and `sys.stderr` are by default text-based. When Click needs a binary stream, it attempts to
  discover the underlying binary stream.

- `sys.argv` is always text. This means that the native type for input values to the types in Click is Unicode, not
  bytes.

  This causes problems if the terminal is incorrectly set and Python does not figure out the encoding. In that case, the
  Unicode string will contain error bytes encoded as surrogate escapes.

- When dealing with files, Click will always use the Unicode file system API by using the operating system's reported or
  guessed filesystem encoding. Surrogates are supported for filenames, so it should be possible to open files through
  the {func}`File` type even if the environment is misconfigured.

## Surrogate Handling

Click does all the Unicode handling in the standard library and is subject to its behavior. Unicode requires extra care.
The reason for this is that the encoding detection is done in the interpreter, and on Linux and certain other operating
systems, its encoding handling is problematic.

The biggest source of frustration is that Click scripts invoked by init systems, deployment tools, or cron jobs will
refuse to work unless a Unicode locale is exported.

If Click encounters such an environment it will prevent further execution to force you to set a locale. This is done
because Click cannot know about the state of the system once it's invoked and restore the values before Python's Unicode
handling kicked in.

If you see something like this error:

```console
Traceback (most recent call last):
  ...
RuntimeError: Click will abort further execution because Python was
  configured to use ASCII as encoding for the environment. Consult
  https://click.palletsprojects.com/unicode-support/ for mitigation
  steps.
```

You are dealing with an environment where Python thinks you are restricted to ASCII data. The solution to these problems
is different depending on which locale your computer is running in.

For instance, if you have a German Linux machine, you can fix the problem by exporting the locale to `de_DE.utf-8`:

```console
export LC_ALL=de_DE.utf-8
export LANG=de_DE.utf-8
```

If you are on a US machine, `en_US.utf-8` is the encoding of choice. On some newer Linux systems, you could also try
`C.UTF-8` as the locale:

```console
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
```

On some systems it was reported that `UTF-8` has to be written as `UTF8` and vice versa. To see which locales are
supported you can invoke `locale -a`.

You need to export the values before you invoke your Python script.

In Python 3.7 and later you will no longer get a `RuntimeError` in many cases thanks to {pep}`538` and {pep}`540`, which
changed the default assumption in unconfigured environments. This doesn't change the general issue that your locale may
be misconfigured.

```
---

## docs/upgrade-guides.md

```markdown
# Upgrade Guides

```{contents}
:depth: 1
:local: true
```

## Upgrading 8.3.X to 9.0
**This is under active construction and will not be finalized until 9.0.0 is released.**

This guide assumes the user is on version 8.3.X.

### Deprecations

For each deprecation, provide a brief explanation, and direct users to new function / class if available.
- TBD

### Removals with prior deprecation

For each removal, provide a brief explanation, and direct users to new function / class if available. If possible, deprecate and remove in 10.0.0, rather than removing outright.
- TBD

### Removals with no prior deprecation

The changes were not able to be deprecated prior to removal. Explain clearly why then were not able to be deprecated first.
- TBD

### Changes

- TBD

### Fixes

- TBD

```
---

## docs/utils.md

```markdown
# Utilities

```{currentmodule} click
```

Besides the functionality that Click provides to interface with argument parsing and handling, it also provides a bunch
of addon functionality that is useful for writing command line utilities.

## Printing to Stdout

The most obvious helper is the {func}`echo` function, which in many ways works like the Python `print` statement or
function. The main difference is that it works the same in many different terminal environments.

Example:

```python
import click

click.echo('Hello World!')
```

It can output both text and binary data. It will emit a trailing newline by default, which needs to be suppressed by
passing `nl=False`:

```python
click.echo(b'\xe2\x98\x83', nl=False)
```

Last but not least {func}`echo` uses click's intelligent internal output streams to stdout and stderr which support
unicode output on the Windows console. This means for as long as you are using `click.echo` you can output unicode
characters (there are some limitations on the default font with regards to which characters can be displayed).

```{versionadded} 6.0
```

Click emulates output streams on Windows to support unicode to the Windows console through separate APIs. For more
information see {doc}`wincmd`.

```{versionadded} 3.0
```

You can also easily print to standard error by passing `err=True`:

```python
click.echo('Hello World!', err=True)
```

(ansi-colors)=

## ANSI Colors

```{versionadded} 2.0
```

The {func}`echo` function supports ANSI colors and styles. On Windows this uses [colorama](https://pypi.org/project/colorama/).

Primarily this means that:

- Click's {func}`echo` function will automatically strip ANSI color codes if the stream is not connected to a terminal.
- the {func}`echo` function will transparently connect to the terminal on Windows and translate ANSI codes to terminal
  API calls. This means that colors will work on Windows the same way they do on other operating systems.

On Windows, Click uses colorama without calling `colorama.init()`. You can still call that in your code, but it's not
required for Click.

For styling a string, the {func}`style` function can be used:

```python
import click

click.echo(click.style('Hello World!', fg='green'))
click.echo(click.style('Some more text', bg='blue', fg='white'))
click.echo(click.style('ATTENTION', blink=True, bold=True))
```

The combination of {func}`echo` and {func}`style` is also available in a single function called {func}`secho`:

```python
click.secho('Hello World!', fg='green')
click.secho('Some more text', bg='blue', fg='white')
click.secho('ATTENTION', blink=True, bold=True)
```

## Pager Support

In some situations, you might want to show long texts on the terminal and let a user scroll through it. This can be
achieved by using the {func}`echo_via_pager` function which works similarly to the {func}`echo` function, but always
writes to stdout and, if possible, through a pager.

Example:

```{eval-rst}
.. click:example::
    @click.command()
    def less():
        click.echo_via_pager("\n".join(f"Line {idx}" for idx in range(200)))
```

If you want to use the pager for a lot of text, especially if generating everything in advance would take a lot of time,
you can pass a generator (or generator function) instead of a string:

```{eval-rst}
.. click:example::
    def _generate_output():
        for idx in range(50000):
            yield f"Line {idx}\n"

    @click.command()
    def less():
        click.echo_via_pager(_generate_output())
```

## Screen Clearing

```{versionadded} 2.0
```

To clear the terminal screen, you can use the {func}`clear` function that is provided starting with Click 2.0. It does
what the name suggests: it clears the entire visible screen in a platform-agnostic way:

```python
import click
click.clear()
```

## Getting Characters from Terminal

```{versionadded} 2.0
```

Normally, when reading input from the terminal, you would read from standard input. However, this is buffered input and
will not show up until the line has been terminated. In certain circumstances, you might not want to do that and instead
read individual characters as they are being written.

For this, Click provides the {func}`getchar` function which reads a single character from the terminal buffer and
returns it as a Unicode character.

Note that this function will always read from the terminal, even if stdin is instead a pipe.

Example:

```python
import click

click.echo('Continue? [yn] ', nl=False)
c = click.getchar()
click.echo()
if c == 'y':
    click.echo('We will go on')
elif c == 'n':
    click.echo('Abort!')
else:
    click.echo('Invalid input :(')
```

Note that this reads raw input, which means that things like arrow keys will show up in the platform's native escape
format. The only characters translated are `^C` and `^D` which are converted into keyboard interrupts and end of file
exceptions respectively. This is done because otherwise, it's too easy to forget about that and to create scripts that
cannot be properly exited.

## Waiting for Key Press

```{versionadded} 2.0
```

Sometimes, it's useful to pause until the user presses any key on the keyboard. This is especially useful on Windows
where `cmd.exe` will close the window at the end of the command execution by default, instead of waiting.

In click, this can be accomplished with the {func}`pause` function. This function will print a quick message to the
terminal (which can be customized) and wait for the user to press a key. In addition to that, it will also become a NOP
(no operation instruction) if the script is not run interactively.

Example:

```python
import click
click.pause()
```

## Launching Editors

```{versionadded} 2.0
```

Click supports launching editors automatically through {func}`edit`. This is very useful for asking users for multi-line
input. It will automatically open the user's defined editor or fall back to a sensible default. If the user closes the
editor without saving, the return value will be `None`, otherwise the entered text.

Example usage:

```python
import click

def get_commit_message():
    MARKER = '# Everything below is ignored\n'
    message = click.edit('\n\n' + MARKER)
    if message is not None:
        return message.split(MARKER, 1)[0].rstrip('\n')
```

Alternatively, the function can also be used to launch editors for files by a specific filename. In this case, the
return value is always `None`.

Example usage:

```python
import click
click.edit(filename='/etc/passwd')
```

## Launching Applications

```{versionadded} 2.0
```

Click supports launching applications through {func}`launch`. This can be used to open the default application
associated with a URL or filetype. This can be used to launch web browsers or picture viewers, for instance. In addition
to this, it can also launch the file manager and automatically select the provided file.

Example usage:

```python
click.launch("https://click.palletsprojects.com/")
click.launch("/my/downloaded/file.txt", locate=True)
```

## Printing Filenames

Because filenames might not be Unicode, formatting them can be a bit tricky.

The way this works with click is through the {func}`format_filename` function. It does a best-effort conversion of the
filename to Unicode and will never fail. This makes it possible to use these filenames in the context of a full Unicode
string.

Example:

```python
click.echo(f"Path: {click.format_filename(b'foo.txt')}")
```

## Standard Streams

For command line utilities, it's very important to get access to input and output streams reliably. Python generally
provides access to these streams through `sys.stdout` and friends, but unfortunately, there are API differences between
2.x and 3.x, especially with regards to how these streams respond to Unicode and binary data.

Because of this, click provides the {func}`get_binary_stream` and {func}`get_text_stream` functions, which produce
consistent results with different Python versions and for a wide variety of terminal configurations.

The end result is that these functions will always return a functional stream object (except in very odd cases; see
{doc}`/unicode-support`).

Example:

```python
import click

stdin_text = click.get_text_stream('stdin')
stdout_binary = click.get_binary_stream('stdout')
```

```{versionadded} 6.0
```

Click now emulates output streams on Windows to support unicode to the Windows console through separate APIs. For more
information see {doc}`wincmd`.

## Intelligent File Opening

```{versionadded} 3.0
```

Starting with Click 3.0 the logic for opening files from the {func}`File` type is exposed through the {func}`open_file`
function. It can intelligently open stdin/stdout as well as any other file.

Example:

```python
import click

stdout = click.open_file('-', 'w')
test_file = click.open_file('test.txt', 'w')
```

If stdin or stdout are returned, the return value is wrapped in a special file where the context manager will prevent
the closing of the file. This makes the handling of standard streams transparent and you can always use it like this:

```python
with click.open_file(filename, 'w') as f:
    f.write('Hello World!\n')
```

## Finding Application Folders

```{versionadded} 2.0
```

Very often, you want to open a configuration file that belongs to your application. However, different operating systems
store these configuration files in different locations depending on their standards. Click provides a
{func}`get_app_dir` function which returns the most appropriate location for per-user config files for your application
depending on the OS.

Example usage:

```python
import os
import click
import ConfigParser

APP_NAME = 'My Application'
def read_config():
cfg = os.path.join(click.get_app_dir(APP_NAME), 'config.ini')
parser = ConfigParser.RawConfigParser()
parser.read([cfg])
rv = {}
for section in parser.sections():
    for key, value in parser.items(section):
        rv[f"{section}.{key}"] = value
return rv
```

## Showing Progress Bars

Sometimes, you have command line scripts that need to process a lot of data, but you want to quickly show the user some
progress about how long that will take. Click supports simple progress bar rendering for that through the
{func}`progressbar` function.

```{note} If you find that you have requirements beyond what Click's progress bar supports, try using [tqdm](https://tqdm.github.io/).
```

The basic usage is very simple: the idea is that you have an iterable that you want to operate on. For each item in the
iterable it might take some time to do processing. So say you have a loop like this:

```python
for user in all_the_users_to_process:
    modify_the_user(user)
```

To hook this up with an automatically updating progress bar, all you need to do is to change the code to this:

```python
import click

with click.progressbar(all_the_users_to_process) as bar:
    for user in bar:
        modify_the_user(user)
```

Click will then automatically print a progress bar to the terminal and calculate the remaining time for you. The
calculation of remaining time requires that the iterable has a length. If it does not have a length but you know the
length, you can explicitly provide it:

```python
with click.progressbar(all_the_users_to_process,
                       length=number_of_users) as bar:
    for user in bar:
        modify_the_user(user)
```

Note that {func}`progressbar` updates the bar *after* each iteration of the loop. So code like this will render
correctly:

```python
import time

with click.progressbar([1, 2, 3]) as bar:
    for x in bar:
        print(f"sleep({x})...")
        time.sleep(x)
```

Another useful feature is to associate a label with the progress bar which will be shown preceding the progress bar:

```python
with click.progressbar(all_the_users_to_process,
                       label='Modifying user accounts',
                       length=number_of_users) as bar:
    for user in bar:
        modify_the_user(user)
```

Sometimes, one may need to iterate over an external iterator, and advance the progress bar irregularly. To do so, you
need to specify the length (and no iterable), and use the update method on the context return value instead of iterating
directly over it:

```python
with click.progressbar(length=total_size,
                       label='Unzipping archive') as bar:
    for archive in zip_file:
        archive.extract()
        bar.update(archive.size)
```

```
---

## docs/virtualenv.md

```markdown
(virtualenv-heading)=

# Virtualenv

## Why Use Virtualenv?

You should use [Virtualenv](https://virtualenv.pypa.io/en/latest/) because:

- It allows you to install multiple versions of the same dependency.
- If you have an operating system version of Python, it prevents you from changing its dependencies and potentially
  messing up your os.

## How to Use Virtualenv

Create your project folder, then a virtualenv within it:

```console
$ mkdir myproject
$ cd myproject
$ python3 -m venv .venv
```

Now, whenever you want to work on a project, you only have to activate the corresponding environment.


```{eval-rst}
.. tabs::

    .. group-tab:: OSX/Linux

        .. code-block:: text

            $ . .venv/bin/activate
            (venv) $

    .. group-tab:: Windows

        .. code-block:: text

            > .venv\scripts\activate
            (venv) >
```

You are now using your virtualenv (notice how the prompt of your shell has changed to show the active environment).

To install packages in the virtual environment:

```console
$ pip install click
```

And if you want to stop using the virtualenv, use the following command:

```console
$ deactivate
```

After doing this, the prompt of your shell should be as familiar as before.

```
---

## docs/why.md

```markdown
# Why Click?

There are so many libraries out there for writing command line utilities; why does Click exist?

This question is easy to answer: because there is not a single command line utility for Python out there which ticks the
following boxes:

- Is lazily composable without restrictions.
- Supports implementation of Unix/POSIX command line conventions.
- Supports loading values from environment variables out of the box.
- Support for prompting of custom values.
- Is fully nestable and composable.
- Supports file handling out of the box.
- Comes with useful common helpers (getting terminal dimensions, ANSI colors, fetching direct keyboard input, screen
  clearing, finding config paths, launching apps and editors, etc.).

There are many alternatives to Click; the obvious ones are `optparse` and `argparse` from the standard library. Have a
look to see if something else resonates with you.

Click actually implements its own parsing of arguments and does not use `optparse` or `argparse` following the
`optparse` parsing behavior. The reason it's not based on `argparse` is that `argparse` does not allow proper nesting of
commands by design and has some deficiencies when it comes to POSIX compliant argument handling.

Click is designed to be fun and customizable but not overly flexible. For instance, the customizability of help pages is
constrained. This constraint is intentional because Click promises multiple Click instances will continue to function as
intended when strung together.

Too much customizability would break this promise.

Click was written to support the [Flask](https://palletsprojects.com/p/flask/) microframework ecosystem because no tool
could provide it with the functionality it needed.

To get an understanding of what Click is all about, I strongly recommend looking at the {ref}`complex-guide` chapter.

## Why not Argparse?

Click is internally based on `optparse` instead of `argparse`. This is an implementation detail that a user does not
have to be concerned with. Click is not based on `argparse` because it has some behaviors that make handling arbitrary
command line interfaces hard:

- `argparse` has built-in behavior to guess if something is an argument or an option. This becomes a problem when
  dealing with incomplete command lines; the behaviour becomes unpredictable without full knowledge of a command line.
  This goes against Click's ambitions of dispatching to subparsers.
- `argparse` does not support disabling interspersed arguments. Without this feature, it's not possible to safely
  implement Click's nested parsing.

## Why not Docopt etc.?

Docopt, and many tools like it, are cool in how they work, but very few of these tools deal with nesting of commands and
composability in a way like Click. To the best of the developer's knowledge, Click is the first Python library that aims
to create a level of composability of applications that goes beyond what the system itself supports.

Docopt, for instance, acts by parsing your help pages and then parsing according to those rules. The side effect of this
is that docopt is quite rigid in how it handles the command line interface. The upside of docopt is that it gives you
strong control over your help page; the downside is that due to this it cannot rewrap your output for the current
terminal width, and it makes translations hard. On top of that, docopt is restricted to basic parsing. It does not
handle argument dispatching and callback invocation or types. This means there is a lot of code that needs to be written
in addition to the basic help page to handle the parsing results.

Most of all, however, it makes composability hard. While docopt does support dispatching to subcommands, it, for
instance, does not directly support any kind of automatic subcommand enumeration based on what's available or it does
not enforce subcommands to work in a consistent way.

This is fine, but it's different from how Click wants to work. Click aims to support fully composable command line user
interfaces by doing the following:

- Click does not just parse, it also dispatches to the appropriate code.
- Click has a strong concept of an invocation context that allows subcommands to respond to data from the parent
  command.
- Click has strong information available for all parameters and commands, so it can generate unified help pages for the
  full CLI and assist the user in converting the input data as necessary.
- Click has a strong understanding of what types are, and it can give the user consistent error messages if something
  goes wrong. A subcommand written by a different developer will not suddenly die with a different error message because
  it's manually handled.
- Click has enough meta information available for its whole program to evolve over time and improve the user experience
  without forcing developers to adjust their programs. For instance, if Click decides to change how help pages are
  formatted, all Click programs will automatically benefit from this.

The aim of Click is to make composable systems. Whereas, the aim of docopt is to build the most beautiful and
hand-crafted command line interfaces. These two goals conflict with one another in subtle ways. Click actively prevents
people from implementing certain patterns in order to achieve unified command line interfaces. For instance, as a
developer, you are given very little choice in formatting your help pages.

## Why Hardcoded Behaviors?

The other question is why Click goes away from optparse and hardcodes certain behaviors instead of staying configurable.
There are multiple reasons for this. The biggest one is that too much configurability makes it hard to achieve a
consistent command line experience.

The best example for this is optparse's `callback` functionality for accepting an arbitrary number of arguments. Due to
syntactical ambiguities on the command line, there is no way to implement fully variadic arguments. There are always
tradeoffs that need to be made and in case of `argparse` these tradeoffs have been critical enough, that a system like
Click cannot even be implemented on top of it.

In this particular case, Click attempts to stay with a handful of accepted paradigms for building command line
interfaces that can be well documented and tested.

## Why No Auto Correction?

The question came up why Click does not auto correct parameters given that even optparse and `argparse` support
automatic expansion of long arguments. The reason for this is that it's a liability for backwards compatibility. If
people start relying on automatically modified parameters and someone adds a new parameter in the future, the script
might stop working. These kinds of problems are hard to find, so Click does not attempt to be magical about this.

This sort of behavior however can be implemented on a higher level to support things such as explicit aliases. For more
information see {ref}`aliases`.

```
---

## docs/wincmd.md

```markdown
# Windows Console Notes

```{versionadded} 6.0
```

Click emulates output streams on Windows to support unicode to the Windows console through separate APIs and we perform
different decoding of parameters.

Here is a brief overview of how this works and what it means to you.

## Unicode Arguments

Click internally is generally based on the concept that any argument can come in as either byte string or unicode string
and conversion is performed to the type expected value as late as possible. This has some advantages as it allows us to
accept the data in the most appropriate form for the operating system and Python version.

This caused some problems on Windows where initially the wrong encoding was used and garbage ended up in your input
data. We not only fixed the encoding part, but we also now extract unicode parameters from `sys.argv`.

There is also another limitation with this: if `sys.argv` was modified prior to invoking a click handler, we have to
fall back to the regular byte input in which case not all unicode values are available but only a subset of the codepage
used for parameters.

## Unicode Output and Input

Unicode output and input on Windows is implemented through the concept of a dispatching text stream. What this means is
that when click first needs a text output (or input) stream on windows it goes through a few checks to figure out of a
windows console is connected or not. If no Windows console is present then the text output stream is returned as such
and the encoding for that stream is set to `utf-8` like on all platforms.

However if a console is connected the stream will instead be emulated and use the cmd.exe unicode APIs to output text
information. In this case the stream will also use `utf-16-le` as internal encoding. However there is some hackery going
on that the underlying raw IO buffer is still bypassing the unicode APIs and byte output through an indirection is still
possible.

- This unicode support is limited to `click.echo`, `click.prompt` as well as `click.get_text_stream`.
- Depending on if unicode values or byte strings are passed the control flow goes completely different places internally
  which can have some odd artifacts if data partially ends up being buffered. Click attempts to protect against that by
  manually always flushing but if you are mixing and matching different string types to `stdout` or `stderr` you will
  need to manually flush.
- The raw output stream is set to binary mode, which is a global operation on Windows, so `print` calls will be
  affected. Prefer `click.echo` over `print`.
- On Windows 7 and below, there is a limitation where at most 64k characters can be written in one call in binary mode.
  In this situation, `sys.stdout` and `sys.stderr` are replaced with wrappers that work around the limitation.

Another important thing to note is that the Windows console's default fonts do not support a lot of characters which
means that you are mostly limited to international letters but no emojis or special characters.

```
---

## examples/README

```text
Click Examples

  This folder contains various Click examples.  Note that
  all of these are not runnable by themselves but should be
  installed into a virtualenv.

```
---

## examples/aliases/README

```text
$ aliases_

  aliases is a fairly advanced example that shows how
  to implement command aliases with Click.  It uses a
  subclass of the default group to customize how commands
  are located.

  It supports both aliases read from a config file as well
  as automatic abbreviations.

  The aliases from the config are read from the aliases.ini
  file.  Try `aliases st` and `aliases ci`!

Usage:

  $ pip install --editable .
  $ aliases --help

```
---

## examples/aliases/aliases.ini

```ini
[aliases]
ci=commit

```
---

## examples/aliases/aliases.py

```python
import configparser
import os

import click


class Config:
    """The config in this example only holds aliases."""

    def __init__(self):
        self.path = os.getcwd()
        self.aliases = {}

    def add_alias(self, alias, cmd):
        self.aliases.update({alias: cmd})

    def read_config(self, filename):
        parser = configparser.RawConfigParser()
        parser.read([filename])
        try:
            self.aliases.update(parser.items("aliases"))
        except configparser.NoSectionError:
            pass

    def write_config(self, filename):
        parser = configparser.RawConfigParser()
        parser.add_section("aliases")
        for key, value in self.aliases.items():
            parser.set("aliases", key, value)
        with open(filename, "wb") as file:
            parser.write(file)


pass_config = click.make_pass_decorator(Config, ensure=True)


class AliasedGroup(click.Group):
    """This subclass of a group supports looking up aliases in a config
    file and with a bit of magic.
    """

    def get_command(self, ctx, cmd_name):
        # Step one: bulitin commands as normal
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        # Step two: find the config object and ensure it's there.  This
        # will create the config object is missing.
        cfg = ctx.ensure_object(Config)

        # Step three: look up an explicit command alias in the config
        if cmd_name in cfg.aliases:
            actual_cmd = cfg.aliases[cmd_name]
            return click.Group.get_command(self, ctx, actual_cmd)

        # Alternative option: if we did not find an explicit alias we
        # allow automatic abbreviation of the command.  "status" for
        # instance will match "st".  We only allow that however if
        # there is only one command.
        matches = [
            x for x in self.list_commands(ctx) if x.lower().startswith(cmd_name.lower())
        ]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

    def resolve_command(self, ctx, args):
        # always return the command's name, not the alias
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name, cmd, args


def read_config(ctx, param, value):
    """Callback that is used whenever --config is passed.  We use this to
    always load the correct config.  This means that the config is loaded
    even if the group itself never executes so our aliases stay always
    available.
    """
    cfg = ctx.ensure_object(Config)
    if value is None:
        value = os.path.join(os.path.dirname(__file__), "aliases.ini")
    cfg.read_config(value)
    return value


@click.command(cls=AliasedGroup)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    callback=read_config,
    expose_value=False,
    help="The config file to use instead of the default.",
)
def cli():
    """An example application that supports aliases."""


@cli.command()
def push():
    """Pushes changes."""
    click.echo("Push")


@cli.command()
def pull():
    """Pulls changes."""
    click.echo("Pull")


@cli.command()
def clone():
    """Clones a repository."""
    click.echo("Clone")


@cli.command()
def commit():
    """Commits pending changes."""
    click.echo("Commit")


@cli.command()
@pass_config
def status(config):
    """Shows the status."""
    click.echo(f"Status for {config.path}")


@cli.command()
@pass_config
@click.argument("alias_", metavar="ALIAS", type=click.STRING)
@click.argument("cmd", type=click.STRING)
@click.option(
    "--config_file", type=click.Path(exists=True, dir_okay=False), default="aliases.ini"
)
def alias(config, alias_, cmd, config_file):
    """Adds an alias to the specified configuration file."""
    config.add_alias(alias_, cmd)
    config.write_config(config_file)
    click.echo(f"Added '{alias_}' as alias for '{cmd}'")

```
---

## examples/aliases/pyproject.toml

```toml
[project]
name = "click-example-aliases"
version = "1.0.0"
description = "Click aliases example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
]

[project.scripts]
aliases = "aliases:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "aliases"

```
---

## examples/colors/README

```text
$ colors_

  colors is a simple example that shows how you can
  colorize text.

  Uses colorama on Windows.

Usage:

  $ pip install --editable .
  $ colors

```
---

## examples/colors/colors.py

```python
import click


all_colors = (
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
    "bright_black",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_blue",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
)


@click.command()
def cli():
    """This script prints some colors. It will also automatically remove
    all ANSI styles if data is piped into a file.

    Give it a try!
    """
    for color in all_colors:
        click.echo(click.style(f"I am colored {color}", fg=color))
    for color in all_colors:
        click.echo(click.style(f"I am colored {color} and bold", fg=color, bold=True))
    for color in all_colors:
        click.echo(click.style(f"I am reverse colored {color}", fg=color, reverse=True))

    click.echo(click.style("I am blinking", blink=True))
    click.echo(click.style("I am underlined", underline=True))

```
---

## examples/colors/pyproject.toml

```toml
[project]
name = "click-example-colors"
version = "1.0.0"
description = "Click colors example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
]

[project.scripts]
colors = "colors:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "colors"

```
---

## examples/completion/README

```text
$ completion
============

Demonstrates Click's shell completion support.

.. code-block:: bash

    pip install --editable .

For Bash:

.. code-block:: bash

    eval "$(_COMPLETION_COMPLETE=bash_source completion)"

For Zsh:

.. code-block:: zsh

    eval "$(_COMPLETION_COMPLETE=zsh_source completion)"

For Fish:

.. code-block:: fish

    eval (env _COMPLETION_COMPLETE=fish_source completion)

Now press tab (maybe twice) after typing something to see completions.

.. code-block:: python

    $ completion <TAB> <TAB>
    $ completion gr <TAB> <TAB>

```
---

## examples/completion/completion.py

```python
import os

import click
from click.shell_completion import CompletionItem


@click.group()
def cli():
    pass


@cli.command()
@click.option("--dir", type=click.Path(file_okay=False))
def ls(dir):
    click.echo("\n".join(os.listdir(dir)))


def get_env_vars(ctx, param, incomplete):
    # Returning a list of values is a shortcut to returning a list of
    # CompletionItem(value).
    return [k for k in os.environ if incomplete in k]


@cli.command(help="A command to print environment variables")
@click.argument("envvar", shell_complete=get_env_vars)
def show_env(envvar):
    click.echo(f"Environment variable: {envvar}")
    click.echo(f"Value: {os.environ[envvar]}")


@cli.group(help="A group that holds a subcommand")
def group():
    pass


def list_users(ctx, param, incomplete):
    # You can generate completions with help strings by returning a list
    # of CompletionItem. You can match on whatever you want, including
    # the help.
    items = [("bob", "butcher"), ("alice", "baker"), ("jerry", "candlestick maker")]
    out = []

    for value, help in items:
        if incomplete in value or incomplete in help:
            out.append(CompletionItem(value, help=help))

    return out


@group.command(help="Choose a user")
@click.argument("user", shell_complete=list_users)
def select_user(user):
    click.echo(f"Chosen user is {user}")


cli.add_command(group)

```
---

## examples/completion/pyproject.toml

```toml
[project]
name = "click-example-completion"
version = "1.0.0"
description = "Click completion example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
]

[project.scripts]
completion = "completion:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "completion"

```
---

## examples/complex/README

```text
$ complex_

  complex is an example of building very complex cli
  applications that load subcommands dynamically from
  a plugin folder and other things.

  All the commands are implemented as plugins in the
  `complex.commands` package.  If a python module is
  placed named "cmd_foo" it will show up as "foo"
  command and the `cli` object within it will be
  loaded as nested Click command.

Usage:

  $ pip install --editable .
  $ complex --help

```
---

## examples/complex/complex/__init__.py

```python

```
---

## examples/complex/complex/cli.py

```python
import os
import sys

import click


CONTEXT_SETTINGS = dict(auto_envvar_prefix="COMPLEX")


class Environment:
    def __init__(self):
        self.verbose = False
        self.home = os.getcwd()

    def log(self, msg, *args):
        """Logs a message to stderr."""
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def vlog(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled."""
        if self.verbose:
            self.log(msg, *args)


pass_environment = click.make_pass_decorator(Environment, ensure=True)
cmd_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "commands"))


class ComplexCLI(click.Group):
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith(".py") and filename.startswith("cmd_"):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f"complex.commands.cmd_{name}", None, None, ["cli"])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click.option(
    "--home",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Changes the folder to operate on.",
)
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode.")
@pass_environment
def cli(ctx, verbose, home):
    """A complex command line interface."""
    ctx.verbose = verbose
    if home is not None:
        ctx.home = home

```
---

## examples/complex/complex/commands/__init__.py

```python

```
---

## examples/complex/complex/commands/cmd_init.py

```python
from complex.cli import pass_environment

import click


@click.command("init", short_help="Initializes a repo.")
@click.argument("path", required=False, type=click.Path(resolve_path=True))
@pass_environment
def cli(ctx, path):
    """Initializes a repository."""
    if path is None:
        path = ctx.home
    ctx.log(f"Initialized the repository in {click.format_filename(path)}")

```
---

## examples/complex/complex/commands/cmd_status.py

```python
from complex.cli import pass_environment

import click


@click.command("status", short_help="Shows file changes.")
@pass_environment
def cli(ctx):
    """Shows file changes in the current working directory."""
    ctx.log("Changed files: none")
    ctx.vlog("bla bla bla, debug info")

```
---

## examples/complex/pyproject.toml

```toml
[project]
name = "click-example-complex"
version = "1.0.0"
description = "Click complex example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
]

[project.scripts]
complex = "complex.cli:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "complex"

```
---

## examples/imagepipe/.gitignore

```gitignore
processed-*

```
---

## examples/imagepipe/README

```text
$ imagepipe_

  imagepipe is an example application that implements some
  commands that chain image processing instructions
  together.

  This requires pillow.

Usage:

  $ pip install --editable .
  $ imagepipe open -i example01.jpg resize -w 128 display
  $ imagepipe open -i example02.jpg blur save

```
---

## examples/imagepipe/imagepipe.py

```python
from functools import update_wrapper

from PIL import Image
from PIL import ImageEnhance
from PIL import ImageFilter

import click


@click.group(chain=True)
def cli():
    """This script processes a bunch of images through pillow in a unix
    pipe.  One commands feeds into the next.

    Example:

    \b
        imagepipe open -i example01.jpg resize -w 128 display
        imagepipe open -i example02.jpg blur save
    """


@cli.result_callback()
def process_commands(processors):
    """This result callback is invoked with an iterable of all the chained
    subcommands.  As in this example each subcommand returns a function
    we can chain them together to feed one into the other, similar to how
    a pipe on unix works.
    """
    # Start with an empty iterable.
    stream = ()

    # Pipe it through all stream processors.
    for processor in processors:
        stream = processor(stream)

    # Evaluate the stream and throw away the items.
    for _ in stream:
        pass


def processor(f):
    """Helper decorator to rewrite a function so that it returns another
    function from it.
    """

    def new_func(*args, **kwargs):
        def processor(stream):
            return f(stream, *args, **kwargs)

        return processor

    return update_wrapper(new_func, f)


def generator(f):
    """Similar to the :func:`processor` but passes through old values
    unchanged and does not pass through the values as parameter.
    """

    @processor
    def new_func(stream, *args, **kwargs):
        yield from stream
        yield from f(*args, **kwargs)

    return update_wrapper(new_func, f)


def copy_filename(new, old):
    new.filename = old.filename
    return new


@cli.command("open")
@click.option(
    "-i",
    "--image",
    "images",
    type=click.Path(),
    multiple=True,
    help="The image file to open.",
)
@generator
def open_cmd(images):
    """Loads one or multiple images for processing.  The input parameter
    can be specified multiple times to load more than one image.
    """
    for image in images:
        try:
            click.echo(f"Opening '{image}'")
            if image == "-":
                img = Image.open(click.get_binary_stdin())
                img.filename = "-"
            else:
                img = Image.open(image)
            yield img
        except Exception as e:
            click.echo(f"Could not open image '{image}': {e}", err=True)


@cli.command("save")
@click.option(
    "--filename",
    default="processed-{:04}.png",
    type=click.Path(),
    help="The format for the filename.",
    show_default=True,
)
@processor
def save_cmd(images, filename):
    """Saves all processed images to a series of files."""
    for idx, image in enumerate(images):
        try:
            fn = filename.format(idx + 1)
            click.echo(f"Saving '{image.filename}' as '{fn}'")
            yield image.save(fn)
        except Exception as e:
            click.echo(f"Could not save image '{image.filename}': {e}", err=True)


@cli.command("display")
@processor
def display_cmd(images):
    """Opens all images in an image viewer."""
    for image in images:
        click.echo(f"Displaying '{image.filename}'")
        image.show()
        yield image


@cli.command("resize")
@click.option("-w", "--width", type=int, help="The new width of the image.")
@click.option("-h", "--height", type=int, help="The new height of the image.")
@processor
def resize_cmd(images, width, height):
    """Resizes an image by fitting it into the box without changing
    the aspect ratio.
    """
    for image in images:
        w, h = (width or image.size[0], height or image.size[1])
        click.echo(f"Resizing '{image.filename}' to {w}x{h}")
        image.thumbnail((w, h))
        yield image


@cli.command("crop")
@click.option(
    "-b", "--border", type=int, help="Crop the image from all sides by this amount."
)
@processor
def crop_cmd(images, border):
    """Crops an image from all edges."""
    for image in images:
        box = [0, 0, image.size[0], image.size[1]]

        if border is not None:
            for idx, val in enumerate(box):
                box[idx] = max(0, val - border)
            click.echo(f"Cropping '{image.filename}' by {border}px")
            yield copy_filename(image.crop(box), image)
        else:
            yield image


def convert_rotation(ctx, param, value):
    if value is None:
        return
    value = value.lower()
    if value in ("90", "r", "right"):
        return (Image.ROTATE_90, 90)
    if value in ("180", "-180"):
        return (Image.ROTATE_180, 180)
    if value in ("-90", "270", "l", "left"):
        return (Image.ROTATE_270, 270)
    raise click.BadParameter(f"invalid rotation '{value}'")


def convert_flip(ctx, param, value):
    if value is None:
        return
    value = value.lower()
    if value in ("lr", "leftright"):
        return (Image.FLIP_LEFT_RIGHT, "left to right")
    if value in ("tb", "topbottom", "upsidedown", "ud"):
        return (Image.FLIP_LEFT_RIGHT, "top to bottom")
    raise click.BadParameter(f"invalid flip '{value}'")


@cli.command("transpose")
@click.option(
    "-r", "--rotate", callback=convert_rotation, help="Rotates the image (in degrees)"
)
@click.option("-f", "--flip", callback=convert_flip, help="Flips the image  [LR / TB]")
@processor
def transpose_cmd(images, rotate, flip):
    """Transposes an image by either rotating or flipping it."""
    for image in images:
        if rotate is not None:
            mode, degrees = rotate
            click.echo(f"Rotate '{image.filename}' by {degrees}deg")
            image = copy_filename(image.transpose(mode), image)
        if flip is not None:
            mode, direction = flip
            click.echo(f"Flip '{image.filename}' {direction}")
            image = copy_filename(image.transpose(mode), image)
        yield image


@cli.command("blur")
@click.option("-r", "--radius", default=2, show_default=True, help="The blur radius.")
@processor
def blur_cmd(images, radius):
    """Applies gaussian blur."""
    blur = ImageFilter.GaussianBlur(radius)
    for image in images:
        click.echo(f"Blurring '{image.filename}' by {radius}px")
        yield copy_filename(image.filter(blur), image)


@cli.command("smoothen")
@click.option(
    "-i",
    "--iterations",
    default=1,
    show_default=True,
    help="How many iterations of the smoothen filter to run.",
)
@processor
def smoothen_cmd(images, iterations):
    """Applies a smoothening filter."""
    for image in images:
        click.echo(
            f"Smoothening {image.filename!r} {iterations}"
            f" time{'s' if iterations != 1 else ''}"
        )
        for _ in range(iterations):
            image = copy_filename(image.filter(ImageFilter.BLUR), image)
        yield image


@cli.command("emboss")
@processor
def emboss_cmd(images):
    """Embosses an image."""
    for image in images:
        click.echo(f"Embossing '{image.filename}'")
        yield copy_filename(image.filter(ImageFilter.EMBOSS), image)


@cli.command("sharpen")
@click.option(
    "-f", "--factor", default=2.0, help="Sharpens the image.", show_default=True
)
@processor
def sharpen_cmd(images, factor):
    """Sharpens an image."""
    for image in images:
        click.echo(f"Sharpen '{image.filename}' by {factor}")
        enhancer = ImageEnhance.Sharpness(image)
        yield copy_filename(enhancer.enhance(max(1.0, factor)), image)


@cli.command("paste")
@click.option("-l", "--left", default=0, help="Offset from left.")
@click.option("-r", "--right", default=0, help="Offset from right.")
@processor
def paste_cmd(images, left, right):
    """Pastes the second image on the first image and leaves the rest
    unchanged.
    """
    imageiter = iter(images)
    image = next(imageiter, None)
    to_paste = next(imageiter, None)

    if to_paste is None:
        if image is not None:
            yield image
        return

    click.echo(f"Paste '{to_paste.filename}' on '{image.filename}'")
    mask = None
    if to_paste.mode == "RGBA" or "transparency" in to_paste.info:
        mask = to_paste
    image.paste(to_paste, (left, right), mask)
    image.filename += f"+{to_paste.filename}"
    yield image

    yield from imageiter

```
---

## examples/imagepipe/pyproject.toml

```toml
[project]
name = "click-example-imagepipe"
version = "1.0.0"
description = "Click imagepipe example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
    "pillow",
]

[project.scripts]
imagepipe = "imagepipe:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "imagepipe"

```
---

## examples/inout/README

```text
$ inout_

  inout is a simple example of an application that
  can read from files and write to files but also
  accept input from stdin or write to stdout.

Usage:

  $ pip install --editable .
  $ inout input_file.txt output_file.txt

```
---

## examples/inout/inout.py

```python
import click


@click.command()
@click.argument("input", type=click.File("rb"), nargs=-1)
@click.argument("output", type=click.File("wb"))
def cli(input, output):
    """This script works similar to the Unix `cat` command but it writes
    into a specific file (which could be the standard output as denoted by
    the ``-`` sign).

    \b
    Copy stdin to stdout:
        inout - -

    \b
    Copy foo.txt and bar.txt to stdout:
        inout foo.txt bar.txt -

    \b
    Write stdin into the file foo.txt
        inout - foo.txt
    """
    for f in input:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            output.write(chunk)
            output.flush()

```
---

## examples/inout/pyproject.toml

```toml
[project]
name = "click-example-inout"
version = "1.0.0"
description = "Click inout example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
]

[project.scripts]
inout = "inout:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "inout"

```
---

## examples/naval/README

```text
$ naval_

  naval is a simple example of an application that
  is ported from the docopt example of the same name.

  Unlike the original this one also runs some code and
  prints messages and it's command line interface was
  changed slightly to make more sense with established
  POSIX semantics.

Usage:

  $ pip install --editable .
  $ naval --help

```
---

## examples/naval/naval.py

```python
import click


@click.group()
@click.version_option()
def cli():
    """Naval Fate.

    This is the docopt example adopted to Click but with some actual
    commands implemented and not just the empty parsing which really
    is not all that interesting.
    """


@cli.group()
def ship():
    """Manages ships."""


@ship.command("new")
@click.argument("name")
def ship_new(name):
    """Creates a new ship."""
    click.echo(f"Created ship {name}")


@ship.command("move")
@click.argument("ship")
@click.argument("x", type=float)
@click.argument("y", type=float)
@click.option("--speed", metavar="KN", default=10, help="Speed in knots.")
def ship_move(ship, x, y, speed):
    """Moves SHIP to the new location X,Y."""
    click.echo(f"Moving ship {ship} to {x},{y} with speed {speed}")


@ship.command("shoot")
@click.argument("ship")
@click.argument("x", type=float)
@click.argument("y", type=float)
def ship_shoot(ship, x, y):
    """Makes SHIP fire to X,Y."""
    click.echo(f"Ship {ship} fires to {x},{y}")


@cli.group("mine")
def mine():
    """Manages mines."""


@mine.command("set")
@click.argument("x", type=float)
@click.argument("y", type=float)
@click.option(
    "ty",
    "--moored",
    flag_value="moored",
    default=True,
    help="Moored (anchored) mine. Default.",
)
@click.option("ty", "--drifting", flag_value="drifting", help="Drifting mine.")
def mine_set(x, y, ty):
    """Sets a mine at a specific coordinate."""
    click.echo(f"Set {ty} mine at {x},{y}")


@mine.command("remove")
@click.argument("x", type=float)
@click.argument("y", type=float)
def mine_remove(x, y):
    """Removes a mine at a specific coordinate."""
    click.echo(f"Removed mine at {x},{y}")

```
---

## examples/naval/pyproject.toml

```toml
[project]
name = "click-example-naval"
version = "1.0.0"
description = "Click naval example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
]

[project.scripts]
naval = "naval:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "naval"

```
---

## examples/repo/README

```text
$ repo_

  repo is a simple example of an application that looks
  and works similar to hg or git.

Usage:

  $ pip install --editable .
  $ repo --help

```
---

## examples/repo/pyproject.toml

```toml
[project]
name = "click-example-repo"
version = "1.0.0"
description = "Click repo example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
]

[project.scripts]
repo = "repo:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "repo"

```
---

## examples/repo/repo.py

```python
import os
import posixpath
import sys

import click


class Repo:
    def __init__(self, home):
        self.home = home
        self.config = {}
        self.verbose = False

    def set_config(self, key, value):
        self.config[key] = value
        if self.verbose:
            click.echo(f"  config[{key}] = {value}", file=sys.stderr)

    def __repr__(self):
        return f"<Repo {self.home}>"


pass_repo = click.make_pass_decorator(Repo)


@click.group()
@click.option(
    "--repo-home",
    envvar="REPO_HOME",
    default=".repo",
    metavar="PATH",
    help="Changes the repository folder location.",
)
@click.option(
    "--config",
    nargs=2,
    multiple=True,
    metavar="KEY VALUE",
    help="Overrides a config key/value pair.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
@click.version_option("1.0")
@click.pass_context
def cli(ctx, repo_home, config, verbose):
    """Repo is a command line tool that showcases how to build complex
    command line interfaces with Click.

    This tool is supposed to look like a distributed version control
    system to show how something like this can be structured.
    """
    # Create a repo object and remember it as as the context object.  From
    # this point onwards other commands can refer to it by using the
    # @pass_repo decorator.
    ctx.obj = Repo(os.path.abspath(repo_home))
    ctx.obj.verbose = verbose
    for key, value in config:
        ctx.obj.set_config(key, value)


@cli.command()
@click.argument("src")
@click.argument("dest", required=False)
@click.option(
    "--shallow/--deep",
    default=False,
    help="Makes a checkout shallow or deep.  Deep by default.",
)
@click.option(
    "--rev", "-r", default="HEAD", help="Clone a specific revision instead of HEAD."
)
@pass_repo
def clone(repo, src, dest, shallow, rev):
    """Clones a repository.

    This will clone the repository at SRC into the folder DEST.  If DEST
    is not provided this will automatically use the last path component
    of SRC and create that folder.
    """
    if dest is None:
        dest = posixpath.split(src)[-1] or "."
    click.echo(f"Cloning repo {src} to {os.path.basename(dest)}")
    repo.home = dest
    if shallow:
        click.echo("Making shallow checkout")
    click.echo(f"Checking out revision {rev}")


@cli.command()
@click.confirmation_option()
@pass_repo
def delete(repo):
    """Deletes a repository.

    This will throw away the current repository.
    """
    click.echo(f"Destroying repo {repo.home}")
    click.echo("Deleted!")


@cli.command()
@click.option("--username", prompt=True, help="The developer's shown username.")
@click.option("--email", prompt="E-Mail", help="The developer's email address")
@click.password_option(help="The login password.")
@pass_repo
def setuser(repo, username, email, password):
    """Sets the user credentials.

    This will override the current user config.
    """
    repo.set_config("username", username)
    repo.set_config("email", email)
    repo.set_config("password", "*" * len(password))
    click.echo("Changed credentials.")


@cli.command()
@click.option(
    "--message",
    "-m",
    multiple=True,
    help="The commit message.  If provided multiple times each"
    " argument gets converted into a new line.",
)
@click.argument("files", nargs=-1, type=click.Path())
@pass_repo
def commit(repo, files, message):
    """Commits outstanding changes.

    Commit changes to the given files into the repository.  You will need to
    "repo push" to push up your changes to other repositories.

    If a list of files is omitted, all changes reported by "repo status"
    will be committed.
    """
    if not message:
        marker = "# Files to be committed:"
        hint = ["", "", marker, "#"]
        for file in files:
            hint.append(f"#   U {file}")
        message = click.edit("\n".join(hint))
        if message is None:
            click.echo("Aborted!")
            return
        msg = message.split(marker)[0].rstrip()
        if not msg:
            click.echo("Aborted! Empty commit message")
            return
    else:
        msg = "\n".join(message)
    click.echo(f"Files to be committed: {files}")
    click.echo(f"Commit message:\n{msg}")


@cli.command(short_help="Copies files.")
@click.option(
    "--force", is_flag=True, help="forcibly copy over an existing managed file"
)
@click.argument("src", nargs=-1, type=click.Path())
@click.argument("dst", type=click.Path())
@pass_repo
def copy(repo, src, dst, force):
    """Copies one or multiple files to a new location.  This copies all
    files from SRC to DST.
    """
    for fn in src:
        click.echo(f"Copy from {fn} -> {dst}")

```
---

## examples/termui/README

```text
$ termui_

  termui showcases the different terminal UI helpers that
  Click provides.

Usage:

  $ pip install --editable .
  $ termui --help

```
---

## examples/termui/pyproject.toml

```toml
[project]
name = "click-example-termui"
version = "1.0.0"
description = "Click termui example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
]

[project.scripts]
termui = "termui:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "termui"

```
---

## examples/termui/termui.py

```python
import math
import random
import time

import click


@click.group()
def cli():
    """This script showcases different terminal UI helpers in Click."""
    pass


@cli.command()
def colordemo():
    """Demonstrates ANSI color support."""
    for color in "red", "green", "blue":
        click.echo(click.style(f"I am colored {color}", fg=color))
        click.echo(click.style(f"I am background colored {color}", bg=color))


@cli.command()
def pager():
    """Demonstrates using the pager."""
    lines = []
    for x in range(200):
        lines.append(f"{click.style(str(x), fg='green')}. Hello World!")
    click.echo_via_pager("\n".join(lines))


@cli.command()
@click.option(
    "--count",
    default=8000,
    type=click.IntRange(1, 100000),
    help="The number of items to process.",
)
def progress(count):
    """Demonstrates the progress bar."""
    items = range(count)

    def process_slowly(item):
        time.sleep(0.002 * random.random())

    def filter(items):
        for item in items:
            if random.random() > 0.3:
                yield item

    with click.progressbar(
        items, label="Processing accounts", fill_char=click.style("#", fg="green")
    ) as bar:
        for item in bar:
            process_slowly(item)

    def show_item(item):
        if item is not None:
            return f"Item #{item}"

    with click.progressbar(
        filter(items),
        label="Committing transaction",
        fill_char=click.style("#", fg="yellow"),
        item_show_func=show_item,
    ) as bar:
        for item in bar:
            process_slowly(item)

    with click.progressbar(
        length=count,
        label="Counting",
        bar_template="%(label)s  %(bar)s | %(info)s",
        fill_char=click.style("█", fg="cyan"),
        empty_char=" ",
    ) as bar:
        for item in bar:
            process_slowly(item)

    with click.progressbar(
        length=count,
        width=0,
        show_percent=False,
        show_eta=False,
        fill_char=click.style("#", fg="magenta"),
    ) as bar:
        for item in bar:
            process_slowly(item)

    # 'Non-linear progress bar'
    steps = [math.exp(x * 1.0 / 20) - 1 for x in range(20)]
    count = int(sum(steps))
    with click.progressbar(
        length=count,
        show_percent=False,
        label="Slowing progress bar",
        fill_char=click.style("█", fg="green"),
    ) as bar:
        for item in steps:
            time.sleep(item)
            bar.update(item)


@cli.command()
@click.argument("url")
def open(url):
    """Opens a file or URL In the default application."""
    click.launch(url)


@cli.command()
@click.argument("url")
def locate(url):
    """Opens a file or URL In the default application."""
    click.launch(url, locate=True)


@cli.command()
def edit():
    """Opens an editor with some text in it."""
    MARKER = "# Everything below is ignored\n"
    message = click.edit(f"\n\n{MARKER}")
    if message is not None:
        msg = message.split(MARKER, 1)[0].rstrip("\n")
        if not msg:
            click.echo("Empty message!")
        else:
            click.echo(f"Message:\n{msg}")
    else:
        click.echo("You did not enter anything!")


@cli.command()
def clear():
    """Clears the entire screen."""
    click.clear()


@cli.command()
def pause():
    """Waits for the user to press a button."""
    click.pause()


@cli.command()
def menu():
    """Shows a simple menu."""
    menu = "main"
    while True:
        if menu == "main":
            click.echo("Main menu:")
            click.echo("  d: debug menu")
            click.echo("  q: quit")
            char = click.getchar()
            if char == "d":
                menu = "debug"
            elif char == "q":
                menu = "quit"
            else:
                click.echo("Invalid input")
        elif menu == "debug":
            click.echo("Debug menu")
            click.echo("  b: back")
            char = click.getchar()
            if char == "b":
                menu = "main"
            else:
                click.echo("Invalid input")
        elif menu == "quit":
            return

```
---

## examples/validation/README

```text
$ validation_

  validation is a simple example of an application that
  performs custom validation of parameters in different
  ways.

  This example requires Click 2.0 or higher.

Usage:

  $ pip install --editable .
  $ validation --help

```
---

## examples/validation/pyproject.toml

```toml
[project]
name = "click-example-validation"
version = "1.0.0"
description = "Click validation example"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1",
]

[project.scripts]
validation = "validation:cli"

[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "validation"

```
---

## examples/validation/validation.py

```python
from urllib import parse as urlparse

import click


def validate_count(ctx, param, value):
    if value < 0 or value % 2 != 0:
        raise click.BadParameter("Should be a positive, even integer.")
    return value


class URL(click.ParamType):
    name = "url"

    def convert(self, value, param, ctx):
        if not isinstance(value, tuple):
            value = urlparse.urlparse(value)
            if value.scheme not in ("http", "https"):
                self.fail(
                    f"invalid URL scheme ({value.scheme}). Only HTTP URLs are allowed",
                    param,
                    ctx,
                )
        return value


@click.command()
@click.option(
    "--count", default=2, callback=validate_count, help="A positive even number."
)
@click.option("--foo", help="A mysterious parameter.")
@click.option("--url", help="A URL", type=URL())
@click.version_option()
def cli(count, foo, url):
    """Validation.

    This example validates parameters in different ways.  It does it
    through callbacks, through a custom type as well as by validating
    manually in the function.
    """
    if foo is not None and foo != "wat":
        raise click.BadParameter(
            'If a value is provided it needs to be the value "wat".',
            param_hint=["--foo"],
        )
    click.echo(f"count: {count}")
    click.echo(f"foo: {foo}")
    click.echo(f"url: {url!r}")

```
---

## pyproject.toml

```toml
[project]
name = "click"
version = "8.3.dev"
description = "Composable command line interface toolkit"
readme = "README.md"
license = "BSD-3-Clause"
license-files = ["LICENSE.txt"]
maintainers = [{name = "Pallets", email = "contact@palletsprojects.com"}]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Typing :: Typed",
]
requires-python = ">=3.10"
dependencies = [
    "colorama; platform_system == 'Windows'",
]

[project.urls]
Donate = "https://palletsprojects.com/donate"
Documentation = "https://click.palletsprojects.com/"
Changes = "https://click.palletsprojects.com/page/changes/"
Source = "https://github.com/pallets/click/"
Chat = "https://discord.gg/pallets"

[dependency-groups]
dev = [
    "ruff",
    "tox",
    "tox-uv",
]
docs = [
    "myst-parser",
    "pallets-sphinx-themes",
    "sphinx",
    "sphinx-tabs",
    "sphinxcontrib-log-cabinet",
]
docs-auto = [
    "sphinx-autobuild",
]
gha-update = [
    "gha-update ; python_full_version >= '3.12'",
]
pre-commit = [
    "pre-commit",
    "pre-commit-uv",
]
tests = [
    "pytest",
]
typing = [
    "mypy",
    "pyright",
    "pytest",
]

[build-system]
requires = ["flit_core>=3.11,<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "click"

[tool.flit.sdist]
include = [
    "docs/",
    "tests/",
    "CHANGES.rst",
    "uv.lock"
]
exclude = [
    "docs/_build/",
]

[tool.uv]
default-groups = ["dev", "pre-commit", "tests", "typing"]

[tool.pytest.ini_options]
testpaths = ["tests"]
filterwarnings = [
    "error",
]

[tool.coverage.run]
branch = true
source = ["click", "tests"]

[tool.coverage.paths]
source = ["src", "*/site-packages"]

[tool.coverage.report]
exclude_also = [
    "if t.TYPE_CHECKING",
    "raise NotImplementedError",
    ": \\.{3}",
]

[tool.mypy]
python_version = "3.10"
files = ["src", "tests/typing"]
show_error_codes = true
pretty = true
strict = true

[[tool.mypy.overrides]]
module = [
    "colorama.*",
]
ignore_missing_imports = true

[tool.pyright]
pythonVersion = "3.10"
include = ["src", "tests/typing"]
typeCheckingMode = "basic"

[tool.ruff]
extend-exclude = ["examples/"]
src = ["src"]
fix = true
show-fixes = true
output-format = "full"

[tool.ruff.lint]
select = [
    "B",  # flake8-bugbear
    "E",  # pycodestyle error
    "F",  # pyflakes
    "I",  # isort
    "UP",  # pyupgrade
    "W",  # pycodestyle warning
]

[tool.ruff.lint.isort]
force-single-line = true
order-by-type = false

[tool.tox]
env_list = [
    "py3.14", "py3.13", "py3.12", "py3.11", "py3.10",
    "py3.14t",
    "pypy3.11",
    "style",
    "typing",
    "docs",
]

[tool.tox.env_run_base]
description = "pytest on latest dependency versions"
runner = "uv-venv-lock-runner"
package = "wheel"
wheel_build_env = ".pkg"
constrain_package_deps = true
use_frozen_constraints = true
dependency_groups = ["tests"]
commands = [[
    "pytest", "-v", "--tb=short", "--basetemp={env_tmp_dir}",
    {replace = "posargs", default = [], extend = true},
]]

[tool.tox.env.style]
description = "run all pre-commit hooks on all files"
dependency_groups = ["pre-commit"]
skip_install = true
commands = [["pre-commit", "run", "--all-files"]]

[tool.tox.env.typing]
description = "run static type checkers"
dependency_groups = ["typing"]
commands = [
    ["mypy"],
    ["pyright", "--ignoreexternal", "--verifytypes", "click"],
]

[tool.tox.env.docs]
description = "build docs"
dependency_groups = ["docs"]
commands = [["sphinx-build", "-E", "-W", "-b", "dirhtml", "docs", "docs/_build/dirhtml"]]

[tool.tox.env.docs-auto]
description = "continuously rebuild docs and start a local server"
dependency_groups = ["docs", "docs-auto"]
commands = [["sphinx-autobuild", "-W", "-b", "dirhtml", "--watch", "src", "docs", "docs/_build/dirhtml"]]

[tool.tox.env.update-actions]
description = "update GitHub Actions pins"
labels = ["update"]
dependency_groups = ["gha-update"]
skip_install = true
commands = [["gha-update"]]

[tool.tox.env.update-pre_commit]
description = "update pre-commit pins"
labels = ["update"]
dependency_groups = ["pre-commit"]
skip_install = true
commands = [["pre-commit", "autoupdate", "--freeze", "-j4"]]

[tool.tox.env.update-requirements]
description = "update uv lock"
labels = ["update"]
dependency_groups = []
no_default_groups = true
skip_install = true
commands = [["uv", "lock", {replace = "posargs", default = ["-U"], extend = true}]]

```
---

## src/click/__init__.py

```python
"""
Click is a simple Python module inspired by the stdlib optparse to make
writing command line scripts fun. Unlike other modules, it's based
around a simple API that does not come with too much magic and is
composable.
"""

from __future__ import annotations

from .core import Argument as Argument
from .core import Command as Command
from .core import CommandCollection as CommandCollection
from .core import Context as Context
from .core import Group as Group
from .core import Option as Option
from .core import Parameter as Parameter
from .decorators import argument as argument
from .decorators import command as command
from .decorators import confirmation_option as confirmation_option
from .decorators import group as group
from .decorators import help_option as help_option
from .decorators import make_pass_decorator as make_pass_decorator
from .decorators import option as option
from .decorators import pass_context as pass_context
from .decorators import pass_obj as pass_obj
from .decorators import password_option as password_option
from .decorators import version_option as version_option
from .exceptions import Abort as Abort
from .exceptions import BadArgumentUsage as BadArgumentUsage
from .exceptions import BadOptionUsage as BadOptionUsage
from .exceptions import BadParameter as BadParameter
from .exceptions import ClickException as ClickException
from .exceptions import FileError as FileError
from .exceptions import MissingParameter as MissingParameter
from .exceptions import NoSuchOption as NoSuchOption
from .exceptions import UsageError as UsageError
from .formatting import HelpFormatter as HelpFormatter
from .formatting import wrap_text as wrap_text
from .globals import get_current_context as get_current_context
from .termui import clear as clear
from .termui import confirm as confirm
from .termui import echo_via_pager as echo_via_pager
from .termui import edit as edit
from .termui import getchar as getchar
from .termui import launch as launch
from .termui import pause as pause
from .termui import progressbar as progressbar
from .termui import prompt as prompt
from .termui import secho as secho
from .termui import style as style
from .termui import unstyle as unstyle
from .types import BOOL as BOOL
from .types import Choice as Choice
from .types import DateTime as DateTime
from .types import File as File
from .types import FLOAT as FLOAT
from .types import FloatRange as FloatRange
from .types import INT as INT
from .types import IntRange as IntRange
from .types import ParamType as ParamType
from .types import Path as Path
from .types import STRING as STRING
from .types import Tuple as Tuple
from .types import UNPROCESSED as UNPROCESSED
from .types import UUID as UUID
from .utils import echo as echo
from .utils import format_filename as format_filename
from .utils import get_app_dir as get_app_dir
from .utils import get_binary_stream as get_binary_stream
from .utils import get_text_stream as get_text_stream
from .utils import open_file as open_file


def __getattr__(name: str) -> object:
    import warnings

    if name == "BaseCommand":
        from .core import _BaseCommand

        warnings.warn(
            "'BaseCommand' is deprecated and will be removed in Click 9.0. Use"
            " 'Command' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _BaseCommand

    if name == "MultiCommand":
        from .core import _MultiCommand

        warnings.warn(
            "'MultiCommand' is deprecated and will be removed in Click 9.0. Use"
            " 'Group' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _MultiCommand

    if name == "OptionParser":
        from .parser import _OptionParser

        warnings.warn(
            "'OptionParser' is deprecated and will be removed in Click 9.0. The"
            " old parser is available in 'optparse'.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _OptionParser

    if name == "__version__":
        import importlib.metadata
        import warnings

        warnings.warn(
            "The '__version__' attribute is deprecated and will be removed in"
            " Click 9.1. Use feature detection or"
            " 'importlib.metadata.version(\"click\")' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return importlib.metadata.version("click")

    raise AttributeError(name)

```
---

## src/click/_compat.py

```python
from __future__ import annotations

import codecs
import collections.abc as cabc
import io
import os
import re
import sys
import typing as t
from types import TracebackType
from weakref import WeakKeyDictionary

CYGWIN = sys.platform.startswith("cygwin")
WIN = sys.platform.startswith("win")
auto_wrap_for_ansi: t.Callable[[t.TextIO], t.TextIO] | None = None
_ansi_re = re.compile(r"\033\[[;?0-9]*[a-zA-Z]")


def _make_text_stream(
    stream: t.BinaryIO,
    encoding: str | None,
    errors: str | None,
    force_readable: bool = False,
    force_writable: bool = False,
) -> t.TextIO:
    if encoding is None:
        encoding = get_best_encoding(stream)
    if errors is None:
        errors = "replace"
    return _NonClosingTextIOWrapper(
        stream,
        encoding,
        errors,
        line_buffering=True,
        force_readable=force_readable,
        force_writable=force_writable,
    )


def is_ascii_encoding(encoding: str) -> bool:
    """Checks if a given encoding is ascii."""
    try:
        return codecs.lookup(encoding).name == "ascii"
    except LookupError:
        return False


def get_best_encoding(stream: t.IO[t.Any]) -> str:
    """Returns the default stream encoding if not found."""
    rv = getattr(stream, "encoding", None) or sys.getdefaultencoding()
    if is_ascii_encoding(rv):
        return "utf-8"
    return rv


class _NonClosingTextIOWrapper(io.TextIOWrapper):
    def __init__(
        self,
        stream: t.BinaryIO,
        encoding: str | None,
        errors: str | None,
        force_readable: bool = False,
        force_writable: bool = False,
        **extra: t.Any,
    ) -> None:
        self._stream = stream = t.cast(
            t.BinaryIO, _FixupStream(stream, force_readable, force_writable)
        )
        super().__init__(stream, encoding, errors, **extra)

    def __del__(self) -> None:
        try:
            self.detach()
        except Exception:
            pass

    def isatty(self) -> bool:
        # https://bitbucket.org/pypy/pypy/issue/1803
        return self._stream.isatty()


class _FixupStream:
    """The new io interface needs more from streams than streams
    traditionally implement.  As such, this fix-up code is necessary in
    some circumstances.

    The forcing of readable and writable flags are there because some tools
    put badly patched objects on sys (one such offender are certain version
    of jupyter notebook).
    """

    def __init__(
        self,
        stream: t.BinaryIO,
        force_readable: bool = False,
        force_writable: bool = False,
    ):
        self._stream = stream
        self._force_readable = force_readable
        self._force_writable = force_writable

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self._stream, name)

    def read1(self, size: int) -> bytes:
        f = getattr(self._stream, "read1", None)

        if f is not None:
            return t.cast(bytes, f(size))

        return self._stream.read(size)

    def readable(self) -> bool:
        if self._force_readable:
            return True
        x = getattr(self._stream, "readable", None)
        if x is not None:
            return t.cast(bool, x())
        try:
            self._stream.read(0)
        except Exception:
            return False
        return True

    def writable(self) -> bool:
        if self._force_writable:
            return True
        x = getattr(self._stream, "writable", None)
        if x is not None:
            return t.cast(bool, x())
        try:
            self._stream.write(b"")
        except Exception:
            try:
                self._stream.write(b"")
            except Exception:
                return False
        return True

    def seekable(self) -> bool:
        x = getattr(self._stream, "seekable", None)
        if x is not None:
            return t.cast(bool, x())
        try:
            self._stream.seek(self._stream.tell())
        except Exception:
            return False
        return True


def _is_binary_reader(stream: t.IO[t.Any], default: bool = False) -> bool:
    try:
        return isinstance(stream.read(0), bytes)
    except Exception:
        return default
        # This happens in some cases where the stream was already
        # closed.  In this case, we assume the default.


def _is_binary_writer(stream: t.IO[t.Any], default: bool = False) -> bool:
    try:
        stream.write(b"")
    except Exception:
        try:
            stream.write("")
            return False
        except Exception:
            pass
        return default
    return True


def _find_binary_reader(stream: t.IO[t.Any]) -> t.BinaryIO | None:
    # We need to figure out if the given stream is already binary.
    # This can happen because the official docs recommend detaching
    # the streams to get binary streams.  Some code might do this, so
    # we need to deal with this case explicitly.
    if _is_binary_reader(stream, False):
        return t.cast(t.BinaryIO, stream)

    buf = getattr(stream, "buffer", None)

    # Same situation here; this time we assume that the buffer is
    # actually binary in case it's closed.
    if buf is not None and _is_binary_reader(buf, True):
        return t.cast(t.BinaryIO, buf)

    return None


def _find_binary_writer(stream: t.IO[t.Any]) -> t.BinaryIO | None:
    # We need to figure out if the given stream is already binary.
    # This can happen because the official docs recommend detaching
    # the streams to get binary streams.  Some code might do this, so
    # we need to deal with this case explicitly.
    if _is_binary_writer(stream, False):
        return t.cast(t.BinaryIO, stream)

    buf = getattr(stream, "buffer", None)

    # Same situation here; this time we assume that the buffer is
    # actually binary in case it's closed.
    if buf is not None and _is_binary_writer(buf, True):
        return t.cast(t.BinaryIO, buf)

    return None


def _stream_is_misconfigured(stream: t.TextIO) -> bool:
    """A stream is misconfigured if its encoding is ASCII."""
    # If the stream does not have an encoding set, we assume it's set
    # to ASCII.  This appears to happen in certain unittest
    # environments.  It's not quite clear what the correct behavior is
    # but this at least will force Click to recover somehow.
    return is_ascii_encoding(getattr(stream, "encoding", None) or "ascii")


def _is_compat_stream_attr(stream: t.TextIO, attr: str, value: str | None) -> bool:
    """A stream attribute is compatible if it is equal to the
    desired value or the desired value is unset and the attribute
    has a value.
    """
    stream_value = getattr(stream, attr, None)
    return stream_value == value or (value is None and stream_value is not None)


def _is_compatible_text_stream(
    stream: t.TextIO, encoding: str | None, errors: str | None
) -> bool:
    """Check if a stream's encoding and errors attributes are
    compatible with the desired values.
    """
    return _is_compat_stream_attr(
        stream, "encoding", encoding
    ) and _is_compat_stream_attr(stream, "errors", errors)


def _force_correct_text_stream(
    text_stream: t.IO[t.Any],
    encoding: str | None,
    errors: str | None,
    is_binary: t.Callable[[t.IO[t.Any], bool], bool],
    find_binary: t.Callable[[t.IO[t.Any]], t.BinaryIO | None],
    force_readable: bool = False,
    force_writable: bool = False,
) -> t.TextIO:
    if is_binary(text_stream, False):
        binary_reader = t.cast(t.BinaryIO, text_stream)
    else:
        text_stream = t.cast(t.TextIO, text_stream)
        # If the stream looks compatible, and won't default to a
        # misconfigured ascii encoding, return it as-is.
        if _is_compatible_text_stream(text_stream, encoding, errors) and not (
            encoding is None and _stream_is_misconfigured(text_stream)
        ):
            return text_stream

        # Otherwise, get the underlying binary reader.
        possible_binary_reader = find_binary(text_stream)

        # If that's not possible, silently use the original reader
        # and get mojibake instead of exceptions.
        if possible_binary_reader is None:
            return text_stream

        binary_reader = possible_binary_reader

    # Default errors to replace instead of strict in order to get
    # something that works.
    if errors is None:
        errors = "replace"

    # Wrap the binary stream in a text stream with the correct
    # encoding parameters.
    return _make_text_stream(
        binary_reader,
        encoding,
        errors,
        force_readable=force_readable,
        force_writable=force_writable,
    )


def _force_correct_text_reader(
    text_reader: t.IO[t.Any],
    encoding: str | None,
    errors: str | None,
    force_readable: bool = False,
) -> t.TextIO:
    return _force_correct_text_stream(
        text_reader,
        encoding,
        errors,
        _is_binary_reader,
        _find_binary_reader,
        force_readable=force_readable,
    )


def _force_correct_text_writer(
    text_writer: t.IO[t.Any],
    encoding: str | None,
    errors: str | None,
    force_writable: bool = False,
) -> t.TextIO:
    return _force_correct_text_stream(
        text_writer,
        encoding,
        errors,
        _is_binary_writer,
        _find_binary_writer,
        force_writable=force_writable,
    )


def get_binary_stdin() -> t.BinaryIO:
    reader = _find_binary_reader(sys.stdin)
    if reader is None:
        raise RuntimeError("Was not able to determine binary stream for sys.stdin.")
    return reader


def get_binary_stdout() -> t.BinaryIO:
    writer = _find_binary_writer(sys.stdout)
    if writer is None:
        raise RuntimeError("Was not able to determine binary stream for sys.stdout.")
    return writer


def get_binary_stderr() -> t.BinaryIO:
    writer = _find_binary_writer(sys.stderr)
    if writer is None:
        raise RuntimeError("Was not able to determine binary stream for sys.stderr.")
    return writer


def get_text_stdin(encoding: str | None = None, errors: str | None = None) -> t.TextIO:
    rv = _get_windows_console_stream(sys.stdin, encoding, errors)
    if rv is not None:
        return rv
    return _force_correct_text_reader(sys.stdin, encoding, errors, force_readable=True)


def get_text_stdout(encoding: str | None = None, errors: str | None = None) -> t.TextIO:
    rv = _get_windows_console_stream(sys.stdout, encoding, errors)
    if rv is not None:
        return rv
    return _force_correct_text_writer(sys.stdout, encoding, errors, force_writable=True)


def get_text_stderr(encoding: str | None = None, errors: str | None = None) -> t.TextIO:
    rv = _get_windows_console_stream(sys.stderr, encoding, errors)
    if rv is not None:
        return rv
    return _force_correct_text_writer(sys.stderr, encoding, errors, force_writable=True)


def _wrap_io_open(
    file: str | os.PathLike[str] | int,
    mode: str,
    encoding: str | None,
    errors: str | None,
) -> t.IO[t.Any]:
    """Handles not passing ``encoding`` and ``errors`` in binary mode."""
    if "b" in mode:
        return open(file, mode)

    return open(file, mode, encoding=encoding, errors=errors)


def open_stream(
    filename: str | os.PathLike[str],
    mode: str = "r",
    encoding: str | None = None,
    errors: str | None = "strict",
    atomic: bool = False,
) -> tuple[t.IO[t.Any], bool]:
    binary = "b" in mode
    filename = os.fspath(filename)

    # Standard streams first. These are simple because they ignore the
    # atomic flag. Use fsdecode to handle Path("-").
    if os.fsdecode(filename) == "-":
        if any(m in mode for m in ["w", "a", "x"]):
            if binary:
                return get_binary_stdout(), False
            return get_text_stdout(encoding=encoding, errors=errors), False
        if binary:
            return get_binary_stdin(), False
        return get_text_stdin(encoding=encoding, errors=errors), False

    # Non-atomic writes directly go out through the regular open functions.
    if not atomic:
        return _wrap_io_open(filename, mode, encoding, errors), True

    # Some usability stuff for atomic writes
    if "a" in mode:
        raise ValueError(
            "Appending to an existing file is not supported, because that"
            " would involve an expensive `copy`-operation to a temporary"
            " file. Open the file in normal `w`-mode and copy explicitly"
            " if that's what you're after."
        )
    if "x" in mode:
        raise ValueError("Use the `overwrite`-parameter instead.")
    if "w" not in mode:
        raise ValueError("Atomic writes only make sense with `w`-mode.")

    # Atomic writes are more complicated.  They work by opening a file
    # as a proxy in the same folder and then using the fdopen
    # functionality to wrap it in a Python file.  Then we wrap it in an
    # atomic file that moves the file over on close.
    import errno
    import random

    try:
        perm: int | None = os.stat(filename).st_mode
    except OSError:
        perm = None

    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL

    if binary:
        flags |= getattr(os, "O_BINARY", 0)

    while True:
        tmp_filename = os.path.join(
            os.path.dirname(filename),
            f".__atomic-write{random.randrange(1 << 32):08x}",
        )
        try:
            fd = os.open(tmp_filename, flags, 0o666 if perm is None else perm)
            break
        except OSError as e:
            if e.errno == errno.EEXIST or (
                os.name == "nt"
                and e.errno == errno.EACCES
                and os.path.isdir(e.filename)
                and os.access(e.filename, os.W_OK)
            ):
                continue
            raise

    if perm is not None:
        os.chmod(tmp_filename, perm)  # in case perm includes bits in umask

    f = _wrap_io_open(fd, mode, encoding, errors)
    af = _AtomicFile(f, tmp_filename, os.path.realpath(filename))
    return t.cast(t.IO[t.Any], af), True


class _AtomicFile:
    def __init__(self, f: t.IO[t.Any], tmp_filename: str, real_filename: str) -> None:
        self._f = f
        self._tmp_filename = tmp_filename
        self._real_filename = real_filename
        self.closed = False

    @property
    def name(self) -> str:
        return self._real_filename

    def close(self, delete: bool = False) -> None:
        if self.closed:
            return
        self._f.close()
        os.replace(self._tmp_filename, self._real_filename)
        self.closed = True

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self._f, name)

    def __enter__(self) -> _AtomicFile:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close(delete=exc_type is not None)

    def __repr__(self) -> str:
        return repr(self._f)


def strip_ansi(value: str) -> str:
    return _ansi_re.sub("", value)


def _is_jupyter_kernel_output(stream: t.IO[t.Any]) -> bool:
    while isinstance(stream, (_FixupStream, _NonClosingTextIOWrapper)):
        stream = stream._stream

    return stream.__class__.__module__.startswith("ipykernel.")


def should_strip_ansi(
    stream: t.IO[t.Any] | None = None, color: bool | None = None
) -> bool:
    if color is None:
        if stream is None:
            stream = sys.stdin
        return not isatty(stream) and not _is_jupyter_kernel_output(stream)
    return not color


# On Windows, wrap the output streams with colorama to support ANSI
# color codes.
# NOTE: double check is needed so mypy does not analyze this on Linux
if sys.platform.startswith("win") and WIN:
    from ._winconsole import _get_windows_console_stream

    def _get_argv_encoding() -> str:
        import locale

        return locale.getpreferredencoding()

    _ansi_stream_wrappers: cabc.MutableMapping[t.TextIO, t.TextIO] = WeakKeyDictionary()

    def auto_wrap_for_ansi(stream: t.TextIO, color: bool | None = None) -> t.TextIO:
        """Support ANSI color and style codes on Windows by wrapping a
        stream with colorama.
        """
        try:
            cached = _ansi_stream_wrappers.get(stream)
        except Exception:
            cached = None

        if cached is not None:
            return cached

        import colorama

        strip = should_strip_ansi(stream, color)
        ansi_wrapper = colorama.AnsiToWin32(stream, strip=strip)
        rv = t.cast(t.TextIO, ansi_wrapper.stream)
        _write = rv.write

        def _safe_write(s: str) -> int:
            try:
                return _write(s)
            except BaseException:
                ansi_wrapper.reset_all()
                raise

        rv.write = _safe_write  # type: ignore[method-assign]

        try:
            _ansi_stream_wrappers[stream] = rv
        except Exception:
            pass

        return rv

else:

    def _get_argv_encoding() -> str:
        return getattr(sys.stdin, "encoding", None) or sys.getfilesystemencoding()

    def _get_windows_console_stream(
        f: t.TextIO, encoding: str | None, errors: str | None
    ) -> t.TextIO | None:
        return None


def term_len(x: str) -> int:
    return len(strip_ansi(x))


def isatty(stream: t.IO[t.Any]) -> bool:
    try:
        return stream.isatty()
    except Exception:
        return False


def _make_cached_stream_func(
    src_func: t.Callable[[], t.TextIO | None],
    wrapper_func: t.Callable[[], t.TextIO],
) -> t.Callable[[], t.TextIO | None]:
    cache: cabc.MutableMapping[t.TextIO, t.TextIO] = WeakKeyDictionary()

    def func() -> t.TextIO | None:
        stream = src_func()

        if stream is None:
            return None

        try:
            rv = cache.get(stream)
        except Exception:
            rv = None
        if rv is not None:
            return rv
        rv = wrapper_func()
        try:
            cache[stream] = rv
        except Exception:
            pass
        return rv

    return func


_default_text_stdin = _make_cached_stream_func(lambda: sys.stdin, get_text_stdin)
_default_text_stdout = _make_cached_stream_func(lambda: sys.stdout, get_text_stdout)
_default_text_stderr = _make_cached_stream_func(lambda: sys.stderr, get_text_stderr)


binary_streams: cabc.Mapping[str, t.Callable[[], t.BinaryIO]] = {
    "stdin": get_binary_stdin,
    "stdout": get_binary_stdout,
    "stderr": get_binary_stderr,
}

text_streams: cabc.Mapping[str, t.Callable[[str | None, str | None], t.TextIO]] = {
    "stdin": get_text_stdin,
    "stdout": get_text_stdout,
    "stderr": get_text_stderr,
}

```
