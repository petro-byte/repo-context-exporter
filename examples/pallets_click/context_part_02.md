# Repository Context Part 2/9

Generated for LLM prompt context.

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
---

## docs/quickstart.md

```markdown
# Quickstart

```{currentmodule} click
```

## Install

Install from PyPI:

```console
pip install click
```

Installing into a virtual environment is highly recommended. We suggest {ref}`virtualenv-heading`.

## Examples

Some standalone examples of Click applications are packaged with Click. They are available in the
[examples folder](https://github.com/pallets/click/tree/main/examples) of the repo.

- [inout](https://github.com/pallets/click/tree/main/examples/inout) : A very simple example of an application that can
  read from files and write to files and also accept input from stdin or write to stdout.
- [validation](https://github.com/pallets/click/tree/main/examples/validation) : A simple example of an application that
  performs custom validation of parameters in different ways.
- [naval](https://github.com/pallets/click/tree/main/examples/naval) : Port of the [docopt](http://docopt.org/) naval
  example.
- [colors](https://github.com/pallets/click/tree/main/examples/colors) : A simple example that colorizes text. Uses
  colorama on Windows.
- [aliases](https://github.com/pallets/click/tree/main/examples/aliases) : An advanced example that implements
  {ref}`aliases`.
- [imagepipe](https://github.com/pallets/click/tree/main/examples/imagepipe) : A complex example that implements some
  {ref}`command-pipelines` . It chains together image processing instructions. Requires pillow.
- [repo](https://github.com/pallets/click/tree/main/examples/repo) : An advanced example that implements a
  Git-/Mercurial-like command line interface.
- [complex](https://github.com/pallets/click/tree/main/examples/complex) : A very advanced example that implements
  loading subcommands dynamically from a plugin folder.
- [termui](https://github.com/pallets/click/tree/main/examples/termui) : A simple example that showcases terminal UI
  helpers provided by click.

## Basic Concepts - Creating a Command

Click is based on declaring commands through decorators. Internally, there is a non-decorator interface for advanced use
cases, but it's discouraged for high-level usage.

A function becomes a Click command line tool by decorating it through {func}`command`. At its simplest, just
decorating a function with this decorator will make it into a callable script:


```{eval-rst}
.. click:example::
    import click

    @click.command()
    def hello():
        click.echo('Hello World!')

What's happening is that the decorator converts the function into a :class:`Command` which then can be invoked:

.. click:example::
    if __name__ == '__main__':
        hello()

And what it looks like:

.. click:run::
    invoke(hello, args=[], prog_name='python hello.py')

And the corresponding help page:

.. click:run::
    invoke(hello, args=['--help'], prog_name='python hello.py')
```

## Echoing

Why does this example use {func}`echo` instead of the regular {func}`print` function? The answer to this question is
that Click attempts to support different environments consistently and to be very robust even when the environment is
misconfigured. Click wants to be functional at least on a basic level even if everything is completely broken.

What this means is that the {func}`echo` function applies some error correction in case the terminal is misconfigured
instead of dying with a {exc}`UnicodeError`.

The echo function also supports color and other styles in output. It will automatically remove styles if the output
stream is a file. On Windows, colorama is automatically installed and used. See {ref}`ansi-colors`.

If you don't need this, you can also use the `print()` construct / function.

## Nesting Commands

Commands can be attached to other commands of type {class}`Group`. This allows arbitrary nesting of scripts. As an
example here is a script that implements two commands for managing databases:

```{eval-rst}
.. click:example::
    @click.group()
    def cli():
        pass

    @click.command()
    def initdb():
        click.echo('Initialized the database')

    @click.command()
    def dropdb():
        click.echo('Dropped the database')

    cli.add_command(initdb)
    cli.add_command(dropdb)
```

As you can see, the {func}`group` decorator works like the {func}`command` decorator, but creates a {class}`Group`
object instead which can be given multiple subcommands that can be attached with {meth}`Group.add_command`.

For simple scripts, it's also possible to automatically attach and create a command by using the {meth}`Group.command`
decorator instead. The above script can instead be written like this:

```{eval-rst}
.. click:example::
    @click.group()
    def cli():
        pass

    @cli.command()
    def initdb():
        click.echo('Initialized the database')

    @cli.command()
    def dropdb():
        click.echo('Dropped the database')

You would then invoke the :class:`Group` in your entry points or other invocations:

.. click:example::
    if __name__ == '__main__':
        cli()
```

## Registering Commands Later

Instead of using the `@group.command()` decorator, commands can be decorated with the plain `@command()` decorator
and registered with a group later with `group.add_command()`. This could be used to split commands into multiple Python
modules.

```{code-block} python
    @click.command()
    def greet():
        click.echo("Hello, World!")
```

```{code-block} python
    @click.group()
    def group():
        pass

    group.add_command(greet)
```

## Adding Parameters

To add parameters, use the {func}`option` and {func}`argument` decorators:

```{eval-rst}
.. click:example::
    @click.command()
    @click.option('--count', default=1, help='number of greetings')
    @click.argument('name')
    def hello(count, name):
        for x in range(count):
            click.echo(f"Hello {name}!")

What it looks like:

.. click:run::
    invoke(hello, args=['--help'], prog_name='python hello.py')
```

## Switching to Entry Points

In the code you wrote so far there is a block at the end of the file which looks like this:
`if __name__ == '__main__':`. This is traditionally how a standalone Python file looks like. With Click you can continue
doing that, but a better way is to package your app with an entry point.

There are two main (and many more) reasons for this:

The first one is that installers automatically generate executable wrappers for Windows so your command line utilities
work on Windows too.

The second reason is that entry point scripts work with virtualenv on Unix without the virtualenv having to be
activated. This is a very useful concept which allows you to bundle your scripts with all requirements into a
virtualenv.

Click is perfectly equipped to work with that and in fact the rest of the documentation will assume that you are writing
applications as distributed packages.

Look at the {doc}`entry-points` chapter before reading the rest as the examples assume that you will be using entry
points.

```
---

## docs/setuptools.md

```markdown
---
orphan: true
---

# Setuptools Integration

Moved to {doc}`entry-points`.

```
---

## docs/shell-completion.md

```markdown
(shell-completion)=

# Shell Completion

```{currentmodule} click.shell_completion
```

Click provides tab completion support for Bash (version 4.4 and up), Zsh, and Fish. It is possible to add support for
other shells too, and suggestions can be customized at multiple levels.

Shell completion suggests command names, option names, and values for choice, file, and path parameter types. Options
are only listed if at least a dash has been entered. Hidden commands and options are not shown.

```console
$ repo <TAB><TAB>
clone  commit  copy  delete  setuser
$ repo clone -<TAB><TAB>
--deep  --help  --rev  --shallow  -r
```

## Enabling Completion

Completion is only available if a script is installed and invoked through an entry point, not through the `python`
command. See {doc}`entry-points`. Once the executable is installed, calling it with a special environment variable will
put Click in completion mode.

To enable shell completion, the user needs to register a special function with their shell. The exact script varies
depending on the shell you are using. Click will output it when called with `_{FOO_BAR}_COMPLETE` set to
`{shell}_source`. `{FOO_BAR}` is the executable name in uppercase with dashes replaced by underscores. It is
conventional but not strictly required for environment variable names to be in upper case. This convention helps
distinguish environment variables from regular shell variables and commands, making scripts and configuration files more
readable and easier to maintain. The built-in shells are `bash`, `zsh`, and `fish`.

Provide your users with the following instructions customized to your program name. This uses `foo-bar` as an example.

```{eval-rst}
.. tabs::

    .. group-tab:: Bash

        Add this to ``~/.bashrc``:

        .. code-block:: bash

            eval "$(_FOO_BAR_COMPLETE=bash_source foo-bar)"

    .. group-tab:: Zsh

        Add this to ``~/.zshrc``:

        .. code-block:: zsh

            eval "$(_FOO_BAR_COMPLETE=zsh_source foo-bar)"

    .. group-tab:: Fish

        Add this to ``~/.config/fish/completions/foo-bar.fish``:

        .. code-block:: fish

            _FOO_BAR_COMPLETE=fish_source foo-bar | source

        This is the same file used for the activation script method
        below. For Fish it's probably always easier to use that method.
```

Using `eval` means that the command is invoked and evaluated every time a shell is started, which can delay shell
responsiveness. To speed it up, write the generated script to a file, then source that. You can generate the files ahead
of time and distribute them with your program to save your users a step.

```{eval-rst}
.. tabs::

    .. group-tab:: Bash

        Save the script somewhere.

        .. code-block:: bash

            _FOO_BAR_COMPLETE=bash_source foo-bar > ~/.foo-bar-complete.bash

        Source the file in ``~/.bashrc``.

        .. code-block:: bash

            . ~/.foo-bar-complete.bash

    .. group-tab:: Zsh

        Save the script somewhere.

        .. code-block:: bash

            _FOO_BAR_COMPLETE=zsh_source foo-bar > ~/.foo-bar-complete.zsh

        Source the file in ``~/.zshrc``.

        .. code-block:: bash

            . ~/.foo-bar-complete.zsh

    .. group-tab:: Fish

        Save the script to ``~/.config/fish/completions/foo-bar.fish``:

        .. code-block:: fish

            _FOO_BAR_COMPLETE=fish_source foo-bar > ~/.config/fish/completions/foo-bar.fish
```

After modifying the shell config, you need to start a new shell in order for the changes to be loaded.

## Custom Type Completion

When creating a custom {class}`~click.ParamType`, override its {meth}`~click.ParamType.shell_complete` method to provide
shell completion for parameters with the type. The method must return a list of {class}`~CompletionItem` objects.
Besides the value, these objects hold metadata that shell support might use. The built-in implementations use `type` to
indicate special handling for paths, and `help` for shells that support showing a help string next to a suggestion.

In this example, the type will suggest environment variables that start with the incomplete value.

```python
class EnvVarType(ParamType):
    name = "envvar"

    def shell_complete(self, ctx, param, incomplete):
        return [
            CompletionItem(name)
            for name in os.environ if name.startswith(incomplete)
        ]

@click.command()
@click.option("--ev", type=EnvVarType())
def cli(ev):
    click.echo(os.environ[ev])
```

## Overriding Value Completion

Value completions for a parameter can be customized without a custom type by providing a `shell_complete` function. The
function is used instead of any completion provided by the type. It is passed 3 positional arguments:

- `ctx` - The current command context.
- `param` - The current parameter requesting completion.
- `incomplete` - The partial word that is being completed. May be an empty string if no characters have been entered
  yet.

It must return a list of {class}`CompletionItem` objects, or as a shortcut it can return a list of strings.

In this example, the command will suggest environment variables that start with the incomplete value.

```python
def complete_env_vars(ctx, param, incomplete):
    return [k for k in os.environ if k.startswith(incomplete)]

@click.command()
@click.argument("name", shell_complete=complete_env_vars)
def cli(name):
    click.echo(f"Name: {name}")
    click.echo(f"Value: {os.environ[name]}")
```

## Adding Support for a Shell

Support can be added for shells that do not come built in. Be sure to check PyPI to see if there's already a package
that adds support for your shell. This topic is very technical, you'll want to look at Click's source to study the
built-in implementations.

Shell support is provided by subclasses of {class}`ShellComplete` registered with {func}`add_completion_class`. When
Click is invoked in completion mode, it calls {meth}`~ShellComplete.source` to output the completion script, or
{meth}`~ShellComplete.complete` to output completions. The base class provides default implementations that require
implementing some smaller parts.

First, you'll need to figure out how your shell's completion system works and write a script to integrate it with Click.
It must invoke your program with the environment variable `_{FOO_BAR}_COMPLETE` set to `{shell}_complete` and pass the
complete args and incomplete value. How it passes those values, and the format of the completion response from Click is
up to you.

In your subclass, set {attr}`ShellComplete.source_template` to the completion script. The default implementation will
perform `%` formatting with the following variables:

- `complete_func` - A safe name for the completion function defined in the script.
- `complete_var` - The environment variable name for passing the `{shell}_complete` instruction.
- `foo_bar` - The name of the executable being completed.

The example code is for a made up shell "My Shell" or "mysh" for short.

```python
from click.shell_completion import add_completion_class
from click.shell_completion import ShellComplete

_mysh_source = """\
%(complete_func)s {
    response=$(%(complete_var)s=mysh_complete %(foo_bar)s)
    # parse response and set completions somehow
}
call-on-complete %(foo_bar)s %(complete_func)s
"""

@add_completion_class
class MyshComplete(ShellComplete):
    name = "mysh"
    source_template = _mysh_source
```

Next, implement {meth}`~ShellComplete.get_completion_args`. This must get, parse, and return the complete args and
incomplete value from the completion script. For example, for the Bash implementation the `COMP_WORDS` env var contains
the command line args as a string, and the `COMP_CWORD` env var contains the index of the incomplete arg. The method
must return a `(args, incomplete)` tuple.

```python
import os
from click.parser import split_arg_string

class MyshComplete(ShellComplete):
    ...

    def get_completion_args(self):
        args = split_arg_string(os.environ["COMP_WORDS"])

        if os.environ["COMP_PARTIAL"] == "1":
            incomplete = args.pop()
            return args, incomplete

        return args, ""
```

Finally, implement {meth}`~ShellComplete.format_completion`. This is called to format each {class}`CompletionItem` into a string. For example, the Bash implementation returns `f"{item.type},{item.value}` (it doesn't support help strings), and the Zsh implementation returns each part separated by a newline, replacing empty help with a `_` placeholder. This format is entirely up to what you parse with your completion script.

The `type` value is usually `plain`, but it can be another value that the completion script can switch on. For example,
`file` or `dir` can tell the shell to handle path completion, since the shell is better at that than Click.

```python
class MyshComplete(ShellComplete):
    ...

    def format_completion(self, item):
        return f"{item.type}\t{item.value}"
```

With those three things implemented, the new shell support is ready. In case those weren't sufficient, there are more
parts that can be overridden, but that probably isn't necessary.

The activation instructions will again depend on how your shell works. Use the following to generate the completion
script, then load it into the shell somehow.

```console
_FOO_BAR_COMPLETE=mysh_source foo-bar
```

```
