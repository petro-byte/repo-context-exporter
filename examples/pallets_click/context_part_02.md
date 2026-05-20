# Repository Context Part 2/7

Generated for LLM prompt context.

## docs/options.md

`````markdown
(options)=

# Options

```{eval-rst}
.. currentmodule:: click
```

Adding options to commands can be accomplished with the {func}`option`
decorator. At runtime the decorator invokes the {class}`Option` class. Options
in Click are distinct from {ref}`positional arguments <arguments>`.

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

The {func}`option()` decorator is usually passed two positional arguments: the
option name and the decorated function argument name.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--string-to-echo', 'string_to_echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)


.. click:run::

    invoke(echo, args=['--help'])
```

However, if the decorated function argument name is not passed in, then Click
will try to infer it. A simple way to name the option so that Click will infer
it correctly is by taking the function argument, adding two dashes to the front
and converting underscores to dashes.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--string-to-echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)

.. click:run::

    invoke(echo, args=['--string-to-echo', 'Hi!'])
```

More formally, Click will try to infer the decorated function argument name as
follows:

1. If a positional argument is a valid [Python identifier](https://docs.python.org/3/reference/lexical_analysis.html#identifiers) (and thus does not have dashes), it is chosen.
2. If multiple positional arguments are prefixed with `--`, the first one
  declared is chosen.
3. Otherwise, the first positional argument prefixed with `-` is chosen.

To get the argument name, the chosen positional argument is converted to lower
case, a leading `-` or `--` is removed if found, and any remaining `-`
characters are replaced with `_`.

```{eval-rst}
.. list-table:: Examples
    :widths: 15 15
    :header-rows: 1

    * - Decorator Arguments
      - Inferred Argument Name
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

A simple {class}`click.Option` takes one option name. By default, it's assumed
that the decorated function argument is not required and the expected type is
`str`. If the decorated function takes a positional argument but the option is
not passed with the command, then `None` is passed.

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

Instead of setting the `type`, you may set a default and Click will try to infer
the type.

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

To make an option take multiple values, pass in `nargs`. Note you may pass in
any positive integer, but not -1. The values are passed to the decorated
function as a tuple.

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

By setting `nargs` to a specific number, each item in
the resulting tuple is of the same type. Alternatively, you might want to use
different types for different indexes in
the tuple. For this you can directly specify a tuple as `type`:

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

By using a tuple literal as the `type`, `nargs` gets automatically set to the
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

The multiple options format allows options to take an arbitrary number of
arguments (which is called variadic). The arguments are passed to the decorated
function as a tuple. If set, `default` must be a list or tuple. Setting a string
as `default` will be interpreted as a list of characters.

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

## Combining short options

Short options made of a single character can be combined into one argument: `-abc` is equivalent to `-a -b -c`. This is the standard POSIX behavior for short option stacking, and it is the reason a repeated flag like `-vvv` works with the [Counting](#counting) feature.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('-a', is_flag=True)
    @click.option('-b', is_flag=True)
    @click.option('-c', is_flag=True)
    def cli(a, b, c):
        click.echo(f"a={a} b={b} c={c}")

.. click:run::

    invoke(cli, args=['-a', '-b', '-c'])
    invoke(cli, args=['-abc'])
```

If the last option in the combination takes a value, the value can either follow as the next argument or be attached directly:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('-v', is_flag=True)
    @click.option('-n', type=int)
    def cli(v, n):
        click.echo(f"v={v} n={n}")

.. click:run::

    invoke(cli, args=['-v', '-n', '5'])
    invoke(cli, args=['-vn', '5'])
    invoke(cli, args=['-vn5'])
```

```{note}
Multi-character short option names are not supported. An argument like `-dbg` is interpreted as the combination of `-d`, `-b`, and `-g`, so Click reports `No such option: -d` if `-d` is not declared. For longer option names, use a long option with the `--` prefix (like `--debug`).
```

## Counting

To count the occurrence of an option, set `count=True`. If the option is not
passed on the command line, then the count is 0. Counting is commonly used for
verbosity.

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

Boolean options (boolean flags) take the values `True` or `False`. The simplest
case sets the default value to `False` if the flag is not passed, and `True` if
it is.

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

To implement this more explicitly, declare `--{on-option}/--{off-option}`. Click
will automatically set `is_flag=True`.

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

* The default can be dynamic so the user can explicitly specify the option with
  either on or off option, or pass in no option to use the dynamic default.
* Shell scripts sometimes want to be explicit even when it's the default
* Shell aliases can set a flag, then an invocation can add a negation of the
  flag

If a forward slash(`/`) is contained in your option name already, you can split
the parameters using `;`. In Windows `/` is commonly used as the prefix
character.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('/debug;/no-debug')
    def log(debug):
        click.echo(f"debug={debug}")
```

```{versionchanged} 6.0
```

If you want to define an alias for the second option only, then you will need to
use leading whitespace to disambiguate the format string.

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

To have a flag pass a value to the decorated function set `flag_value`. This
automatically sets `is_flag=True`. To mark the flag as default, set
`default=True`. Setting flag values can be used to create patterns like this:

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

### How `default` and `flag_value` interact

The `default` value is given to the underlying function
as-is. So if you set `default=None`, the function receives
`None`. Same for any other type.

But there is a special case for **non-boolean** flags: if a
flag has a non-boolean `flag_value` (like a string or a
class), then `default=True` is interpreted as *the flag
should be activated by default*. The function receives the
`flag_value`, not the Python `True`.

Which means, in the example above, this option:

```python
@click.option('--upper', 'transformation', flag_value='upper', default=True)
```

is equivalent to:

```python
@click.option('--upper', 'transformation', flag_value='upper', default='upper')
```

Because the two are equivalent, it is recommended to always
use the second form and set `default` to the actual value
you want. This makes code more explicit and predictable.

This special case does **not** apply to boolean flags (where
`flag_value` is `True` or `False`). For boolean flags,
`default=True` is the literal Python value `True`.

The tables below show the value received by the function for
each combination of `default`, `flag_value`, and whether
the flag was passed on the command line.

#### Boolean flags (`is_flag=True`, boolean `flag_value`)

These are flags where `flag_value` is `True` or `False`.
The `default` value is always passed through literally
without any special substitution.

| `default` | `flag_value` | Not passed | `--flag` passed |
|-----------|--------------|------------|-----------------|
| *(unset)* | *(unset)*    | `False`    | `True`          |
| `True`    | *(unset)*    | `True`     | `True`          |
| `False`   | *(unset)*    | `False`    | `True`          |
| `None`    | *(unset)*    | `None`     | `True`          |
| `True`    | `True`       | `True`     | `True`          |
| `True`    | `False`      | `True`     | `False`         |
| `False`   | `True`       | `False`    | `True`          |
| `False`   | `False`      | `False`    | `False`         |
| `None`    | `True`       | `None`     | `True`          |
| `None`    | `False`      | `None`     | `False`         |

````{tip}
For a negative flag that defaults to off, prefer the
explicit pair form `--with-xyz/--without-xyz` over the
single-flag `flag_value=False, default=True`:

```python
@click.option('--with-xyz/--without-xyz', 'enable_xyz', default=True)
```
````

#### Boolean flag pairs (`--flag/--no-flag`)

These use secondary option names to provide both an on and
off switch. The `default` value is always literal.

| `default` | Not passed | `--flag` | `--no-flag` |
|-----------|------------|----------|-------------|
| *(unset)* | `False`    | `True`   | `False`     |
| `True`    | `True`     | `True`   | `False`     |
| `False`   | `False`    | `True`   | `False`     |
| `None`    | `None`     | `True`   | `False`     |

#### Non-boolean feature switches (`flag_value` is a string, class, etc.)

For these flags, `default=True` is a **special case**: it
means "activate this flag by default" and resolves to the
`flag_value`. All other `default` values are passed through
literally.

| `default`  | `flag_value` | Not passed  | `--flag` passed |
|------------|--------------|-------------|-----------------|
| *(unset)*  | `"upper"`    | `None`      | `"upper"`       |
| `True`     | `"upper"`    | `"upper"`¹  | `"upper"`       |
| `"lower"`  | `"upper"`    | `"lower"`   | `"upper"`       |
| `None`     | `"upper"`    | `None`      | `"upper"`       |

```{hint}
¹: `default=True` is substituted with `flag_value`.
```

#### Feature switch groups (multiple flags sharing one variable)

Several `flag_value` options can target the same parameter name to form a
feature switch group. The user picks one flag on the command line, and the
function receives the corresponding `flag_value`. When the user picks none,
Click falls back to whichever option claims the slot under the arbitration
rules described below.

##### Non-boolean groups

For non-boolean `flag_value` (strings, enum members, classes, ...), place
`default=True` on the option that should win when no flag is passed. The
substitution rule above resolves it to that option's `flag_value`. Any other
explicit `default` is passed through literally.

| Definition                                             | Not passed | `--upper` | `--lower` |
|--------------------------------------------------------|------------|-----------|-----------|
| `--upper` with `flag_value='upper'`, `default=True`    | `"upper"`  | `"upper"` | `"lower"` |
| `--upper` with `flag_value='upper'`, `default='upper'` | `"upper"`  | `"upper"` | `"lower"` |
| `--upper` with `flag_value='upper'`, `default=None`    | `None`     | `"upper"` | `"lower"` |
| Neither option carries a `default`                     | `None`     | `"upper"` | `"lower"` |

The third row is the three-state pattern: the function receives `None` when no
flag is passed, distinguishable from either explicit choice.

##### Boolean groups

When `flag_value` is `True` or `False`, the substitution rule does not apply:
`default=True` is the literal Python `True`. To make one flag in an
enable/disable pair the default, set its `default=True` explicitly:

```python
@click.option("--without-xyz", "enable_xyz", flag_value=False)
@click.option("--with-xyz", "enable_xyz", flag_value=True, default=True)
```

| Definition                                              | Not passed | `--with-xyz` | `--without-xyz` |
|---------------------------------------------------------|------------|--------------|-----------------|
| `--with-xyz` with `flag_value=True`, `default=True`     | `True`     | `True`       | `False`         |
| `--without-xyz` with `flag_value=False`, `default=False`| `False`    | `True`       | `False`         |
| `--with-xyz` with `flag_value=True`, `default=None`     | `None`     | `True`       | `False`         |
| Neither option carries a `default`                      | `False`    | `True`       | `False`         |

```{tip}
For most enable/disable cases, the pair form `--with-xyz/--without-xyz` is
shorter and equivalent. The multi-flag group form is useful when the on and off
flags need distinct names without a shared stem, or when each flag needs its
own help text.
```

##### Arbitration rules

When several options in a group resolve their values simultaneously, only one
wins the parameter slot. The full arbitration policy (source precedence,
explicit-beats-auto tie-break, first-declared fallback) is enumerated under
[Option value resolution](#option-value-resolution).

## Option value resolution

This section enumerates the rules Click applies when computing the value
delivered to the decorated function for every option. Rules are listed in the
order they fire during the parsing pipeline.

### Type inference

Without an explicit `type=`, Click infers the parameter type at construction:

1. If `flag_value` is `True` or `False`, the type is {class}`BoolParamType`.
2. If `flag_value` is an `int`, `float`, or `str`, the type is the matching
   basic type.
3. If `flag_value` is any other Python object (a class, an enum member, a
   `frozenset`, ...), the type is {data}`UNPROCESSED` so the value passes
   through unchanged.
4. Otherwise, the type is inferred from `default` if set, falling back to
   {class}`StringParamType` when neither hint is available.

### `default` interpretation

The literal value passed as `default=` is interpreted differently depending on
whether the option is a flag and what `flag_value` it carries:

1. `default=UNSET` (the absence sentinel) is treated as if `default` was not
   passed at all. It does not count as "the user picked nothing", and it does
   not count as an explicit default for arbitration purposes.
2. For a bare boolean flag (no `flag_value`, or `flag_value` of `True` or
   `False`), an unset `default` auto-derives to `False`.
3. For a non-boolean flag with a `flag_value`, `default=True` is substituted
   with `flag_value`. This is the "activate this flag by default" shorthand.
   Any non-`True` `default` is passed through literally.
4. For a boolean flag with `flag_value` set, `default=True` is the literal
   Python `True`. The substitution from rule 3 does not apply.
5. `default=None` is always a real explicit value, distinct from `UNSET`
   absence.
6. Any other `default` is delivered to the function unchanged after conversion
   through the parameter's type.

### Value sources

Click resolves the value of every option from the following
sources, in order of decreasing precedence:

1. **command line input** ({attr}`ParameterSource.COMMANDLINE`),
2. **environment variable** named in `envvar=` or derived from `auto_envvar_prefix`
   ({attr}`ParameterSource.ENVIRONMENT`),
3. **`default_map` entry** matching the parameter name on the active {class}`Context`
   ({attr}`ParameterSource.DEFAULT_MAP`),
4. **parameter default** ({attr}`ParameterSource.DEFAULT`).

The first source that produces a value wins. Environment variables and
`default_map` entries set to `Sentinel.UNSET` are skipped, so they fall through
to the next source rather than supplying `UNSET` to the function.

### Slot arbitration

Several options can target the same `name` to form a feature switch group. When
they do, only one option's value reaches the function. Arbitration applies
these rules, in order:

1. **By source.** Whichever option resolved its value from the most explicit
   source wins, regardless of decorator order. Any command-line input beats any
   default, an environment variable beats a `default_map` entry, and so on.
2. **Within the default tier, explicit beats auto-derived.** An option that
   received an explicit `default=` keyword wins over one whose default came
   from `default` interpretation.
3. **Otherwise, last declared wins.** When all options in the group resolved
   from the same source and tier (all auto-derived defaults, or all explicit
   defaults), the option declared last in the source code keeps the slot.

## Values from Environment Variables

To pass in a value from a specific environment variable use `envvar`.

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
 - Not stripped of whitespace and should match the exact name provided to the
   `envvar` argument.

For flag options, there are two concepts to consider: the activation of the flag
driven by the environment variable, and the value of the flag if it is
activated.

The values read from environment variables are always strings and will require
extra processing. We need to transform these strings into boolean values that
will determine if the flag is activated or not.

Here are the rules used to parse environment variable values for flag options:
   - `true`, `1`, `yes`, `on`, `t`, `y` are interpreted as activating the flag
   - `false`, `0`, `no`, `off`, `f`, `n` are interpreted as deactivating the
     flag
   - The presence of the environment variable without value is interpreted as
     deactivating the flag
   - Empty strings are interpreted as deactivating the flag
   - Values are case-insensitive, so the `True`, `TRUE`, `tRuE` strings are all
     interpreted as activating the flag
   - Values are stripped of leading and trailing whitespace before being
     interpreted, so the `" True "` string is transformed to `"true"` and thus
     activates the flag
   - If the flag option has a `flag_value` argument, passing that value in the
     environment variable will activate the flag, in addition to all the cases
     described above
   - Any other value is interpreted as deactivating the flag

```{caution}
For boolean flags with a pair of values, the only recognized environment variable is the one provided to the `envvar` argument.

So an option defined as `--flag\--no-flag`, with a `envvar="FLAG"` parameter, there is no magical `NO_FLAG=<anything>` variable that is recognized. Only the `FLAG=<anything>` environment variable is recognized.
```

If the flag is activated, its value is set to `flag_value`. Otherwise, the value
defaults to `None`.

## Multiple Options from Environment Values

As options can accept multiple values, pulling in such values from
environment variables (which are strings) is a bit more complex. Click handles
this by deferring customization of the behavior to the `type`. For both
`multiple` and `nargs` with values other than
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

Click can deal with prefix characters besides `-` for options, including `/` and
`+`, as well as others. Note that alternative prefix characters are generally
used very sparingly if at all within POSIX.

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

There are special considerations for using `/` as prefix character. See
{ref}`option-boolean-flag` for more.

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

`````
---

## docs/parameter-types.md

````markdown
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

```{versionchanged} 8.4.0
{class}`Choice` is now generic. Parameterize it with the choice value type
({class}`!Choice[HashType]` for an enum, {class}`!Choice[str]` for plain
strings) to enable type-checked consumers.
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

{class}`ParamType` is generic in the converted value type: parameterize it with
the type returned by `convert` so that consumers (and type checkers) can rely
on the narrowed return type.

The following code implements an integer type that accepts hex and octal numbers in addition to normal integers, and
converts them into regular integers.

```python
import click


class BasedIntParamType(click.ParamType[int]):
    name = "integer"

    def convert(self, value, param, ctx) -> int:
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

```{versionchanged} 8.4.0
{class}`ParamType` is now a generic abstract base class. Parameterize it with
the converted value type ({class}`!ParamType[int]` for an integer-returning
type) so that {meth}`~ParamType.convert` and downstream consumers carry the
narrowed type.
```

````
---

## docs/parameters.md

````markdown
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

````
---

## docs/prompts.md

````markdown
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

````
---

## docs/quickstart.md

````markdown
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

````
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

````markdown
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
class EnvVarType(ParamType[str]):
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

````
---

## docs/standalone-apps.md

````markdown
# Standalone Application with Briefcase

[Briefcase](https://briefcase.beeware.org/) is a tool for packaging Python
projects as standalone native applications. It can produce installers and
executables for macOS, Windows, and Linux that do not require the user to
install Python or any dependencies.

- Produces platform-native installers (``.pkg`` on macOS, ``.msi`` on
    Windows, ``.deb``/``.rpm`` on Linux).
- Bundles a Python interpreter and all dependencies.
- Supports passing command line arguments to the app.

This page outlines the basics of packaging a Click application with
Briefcase. Be sure to read its
[documentation](https://briefcase.beeware.org/en/stable/how-to/building/cli-apps/)
and use ``briefcase --help`` to understand what features are available.

## Installation

Install Briefcase in the virtual environment:

```console
pip install briefcase
```

## Configuration

Add a ``[tool.briefcase]`` section and a
``[tool.briefcase.app.<app-name>]`` section to ``pyproject.toml``.
Set ``console_app = true`` so Briefcase treats the project as a command
line application rather than a GUI application.

Given a Click application with the following project structure:

```text
hello-cli/
    src/
        hello_cli/
            __init__.py
            app.py
    LICENSE
    pyproject.toml
```

Where ``app.py`` contains a Click command:

```python
import click

@click.command()
@click.argument("name", default="World")
@click.option("--count", default=1, help="Number of times to greet.")
def main(name, count):
    """Greet someone by NAME (default: World)."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")
```

Add the following Briefcase configuration to ``pyproject.toml``:

```toml
[tool.briefcase]
project_name = "Hello CLI"
bundle = "com.example"
version = "0.0.1"
url = "https://example.com/hello-cli"
license.file = "LICENSE"
author = "Your Name"
author_email = "you@example.com"

[tool.briefcase.app.hello-cli]
formal_name = "Hello CLI"
description = "My first application"
long_description = """More details about the app should go here.
"""
sources = [
    "src/hello_cli",
]
console_app = true
requires = [
    "click",
]
```

The key settings are:

- ``console_app = true`` -- tells Briefcase this is a terminal
    application, not a GUI.
- ``sources`` -- the list of source packages to include.
- ``requires`` -- the Python dependencies to bundle (Click and any other
    libraries the project needs).

## Entry Point

Briefcase launches the application by running the package with
``python -m <package>``, so a ``__main__.py`` file **must** exist in the
package. Without it, Briefcase will not be able to start the application.

Create ``__main__.py`` in the package directory and call the Click
command:

```python
from hello_cli.app import main

if __name__ == "__main__":
    main()
```

## Running

Use ``briefcase dev`` to run the application directly from the source
tree. Pass command line arguments after ``--``:

```console
$ briefcase dev -- World
Hello, World!
$ briefcase dev -- World --count 2
Hello, World!
Hello, World!
```

## Building and Packaging

To create a distributable executable, run the following commands:

```console
briefcase create
briefcase build
briefcase package
```

``briefcase create`` downloads a Python interpreter and installs
dependencies into an isolated app bundle. ``briefcase build`` compiles
the app, and ``briefcase package`` produces the final platform installer.

On macOS, this produces a ``.pkg`` installer. On Windows, it produces a
``.msi`` installer. On Linux, it produces a system package (``.deb``,
``.rpm``, etc.) for the current distribution.

Once installed, users can run the application directly from the terminal:

```console
$ hello-cli World
Hello, World!
$ hello-cli World --count 2
Hello, World!
Hello, World!
```

````
---

## docs/support-multiple-versions.md

````markdown
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
class CommaDelimitedString(click.ParamType[str]):
    @add_ctx_arg
    def get_metavar(self, param: click.Parameter, ctx: click.Context | None) -> str:
        return "TEXT,TEXT,..."
```

````
---

## docs/testing.md

````markdown
# Testing Click Applications

```{eval-rst}
.. currentmodule:: click.testing
```

Click provides the {ref}`click.testing <testing>` module to help you invoke
command line applications and check their behavior.

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
  - {class}`Result` - returned from {meth}`CliRunner.invoke`. Captures output
    data, exit code, optional exception, and captures the output as bytes and
    binary data.

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

A subcommand name must be specified in the `args` parameter
{meth}`CliRunner.invoke`:

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

Additional keyword arguments passed to {meth}`CliRunner.invoke` will be used to
construct the initial {class}`Context object <click.Context>`.
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

The {meth}`CliRunner.isolated_filesystem` context manager sets the current
working directory to a new, empty folder.

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

The test wrapper can provide input data for the input stream (stdin). This is
very useful for testing prompts.

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

## Capture modes

{class}`CliRunner` captures output by replacing `sys.stdout` and `sys.stderr`
with in-memory wrappers. The `capture` parameter controls which strategy is
used.

### `capture="sys"` (default)

Captures Python-level writes (`print()`, `click.echo()`, `sys.stdout.write()`).
It is fast and sufficient for most Click applications.

Code that holds a reference to the original `sys.stdout` (like a library that
does `from sys import stdout` at import time) bypasses the capture and its
output is lost.

In this mode `sys.stdout.fileno()` and `sys.stderr.fileno()` raise
{exc}`io.UnsupportedOperation`, matching the pre-`8.3.3` behavior. C-level
consumers ({mod}`faulthandler`, {mod}`subprocess`, C extensions) that expect a
real file descriptor must opt into the `capture="fd"` mode.

### `capture="fd"`

Redirects OS file descriptors `1` and `2` to a temporary file via
{func}`os.dup2`, inspired by [Pytest's
`capfd`](https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html).
This catches output that bypasses `sys.stdout`, including:

- Stale references to the original `sys.stdout` and `sys.stderr`.
- Logging frameworks that cache the original stream (like `structlog` or the
  stdlib's `logging` module).
- C extensions and subprocesses that write directly to `fd 1` or `fd 2`.

```python
from click.testing import CliRunner
from myapp import cli


def test_captures_everything():
    runner = CliRunner(capture="fd")
    result = runner.invoke(cli)
    # result.stdout contains both Python-level and fd-level output
    assert "expected output" in result.stdout
```

In this mode `sys.stdout.fileno()` returns the saved (pre-redirection) `fd`, so
{mod}`faulthandler` and similar consumers keep working. Writes to `fd 1` and
`fd 2` land in the capture tmpfile, so `os.dup2()` calls inside the CLI no
longer leak into the host runner's stdout.

```{note}
`capture="fd"` is not available on Windows.
```

```{versionchanged} 8.4.0
Added the `capture` parameter. The default `sys` mode no longer exposes the
original `fd` through `fileno()`, reverting the change introduced in `8.3.3`
that broke Pytest's `fd`-level capture teardown. Use `capture="fd"` to restore
that behavior with proper isolation.
```

````
---

## docs/unicode-support.md

````markdown
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

````
---

## docs/upgrade-guides.md

````markdown
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

````
---

## docs/utils.md

````markdown
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

For more complex programs, which can't easily use a simple generator, you
can get access to a writable file-like object for the pager, and write to
that instead:

```{eval-rst}
.. click:example::
    @click.command()
    def less():
        with click.get_pager_file() as pager:
            for idx in range(50000):
                print(idx, file=pager)
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

````
---

## docs/virtualenv.md

````markdown
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

````
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

````markdown
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

Unicode output and input on Windows is implemented through the concept of a
dispatching text stream. This means that when click first needs a text output
(or input) stream on windows it goes through a few checks to figure out if a
windows console is connected or not. If no Windows console is present then the
text output stream is returned as such and the encoding for that stream is set
to `utf-8` like on all platforms.

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

````
---

## pyproject.toml

```toml
[project]
name = "click"
version = "8.5.0.dev"
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
tests-random = [
    "pytest",
    "pytest-randomly",
    "pytest-xdist",
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
markers = [
    "stress: high-iteration stress tests for race conditions (deselect with '-m \"not stress\"')",
]
addopts = "-m 'not stress'"

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
    "stress-py3.14", "stress-py3.14t",
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

[tool.tox.env.random]
description = "randomized parallel tests to detect test pollution and race conditions"
dependency_groups = ["tests-random"]
commands = [[
    "pytest", "-v", "--tb=short", "--numprocesses=auto",
    "--basetemp={env_tmp_dir}",
    {replace = "posargs", default = [], extend = true},
]]

[tool.tox.env.stress]
description = "stress tests for stream lifecycle race conditions"
commands = [[
    "pytest", "-v", "--tb=short", "-x", "-m", "stress",
    "--basetemp={env_tmp_dir}",
    "--override-ini=addopts=",
    "tests/test_stream_lifecycle.py",
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

## repo_context_exporter_1.py

````python
#!/usr/bin/env python3
"""
Export a repository into markdown context files for LLM prompting.

Features
- Recursively collects files from a repository.
- Uses gitignore-like inline pattern lists (no external ignore file required).
- Writes source code into markdown files with path headers and fenced code blocks.
- Emits a separate markdown file with the directory tree.
- Keeps source files whole; never splits one file across multiple output files.
- Uses a soft file size threshold per markdown file (in KB).
- If the repository is too large for MAX_OUTPUT_FILES * MAX_OUTPUT_FILE_SIZE_KB,
  it rebalances content across exactly MAX_OUTPUT_FILES files as evenly as possible.

Typical usage
    python repo_context_exporter.py .
    python repo_context_exporter.py /path/to/repo --output-dir llm-context
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


# ============================================================
# Configuration
# ============================================================

# Maximum number of output markdown files.
MAX_OUTPUT_FILES = 8

# Optional maximum size per output markdown file in KB.
# Set to -1 to disable the threshold and always distribute evenly.
MAX_OUTPUT_FILE_SIZE_KB = 200

OUTPUT_DIR_NAME = "llm-context"
TREE_FILE_NAME = "00_DIRECTORY_TREE.md"
OUTPUT_FILE_PREFIX = "context_part_"
READ_FILE_ENCODING = "utf-8"
READ_FILE_ERRORS = "replace"

# Gitignore-like patterns for files that should NOT be included in code exports.
EXPORT_IGNORE_PATTERNS = [
    "repo_context_exporter.py",
    ".git/",
    ".idea/",
    ".vscode/",
    ".gitignore",
    ".gitkeep",
    "node_modules/",
    "dist/",
    "build/",
    "coverage/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.log",
    "*.sqlite",
    "*.sqlite3",
    "*.lock",
    "examples/",
    OUTPUT_DIR_NAME + "/",
]

# Separate ignore patterns for the directory tree export.
TREE_IGNORE_PATTERNS = [
    "repo_context_exporter.py",
    ".git/",
    "node_modules/",
    "dist/",
    "build/",
    "coverage/",
    "__pycache__/",
    ".DS_Store",
    "examples/",
    OUTPUT_DIR_NAME + "/",
]

# Files that are usually not helpful as prompt context.
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".mp3", ".wav", ".ogg", ".flac", ".mp4", ".mov", ".avi", ".mkv",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".class",
    ".jar", ".pyc", ".pyo",
}

# Optional extra file names to skip completely.
BINARY_FILENAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}


# ============================================================
# Language mapping for fenced code blocks
# ============================================================

EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".php": "php",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".scala": "scala",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".ps1": "powershell",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".xml": "xml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".md": "markdown",
    ".dockerfile": "dockerfile",
    ".tf": "hcl",
    ".vue": "vue",
    ".svelte": "svelte",
    ".graphql": "graphql",
    ".gql": "graphql",
}

SPECIAL_FILENAMES_TO_LANGUAGE = {
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
    "CMakeLists.txt": "cmake",
    ".gitignore": "gitignore",
    ".env": "dotenv",
}


# ============================================================
# Data structures
# ============================================================

@dataclass(slots=True)
class FileBlock:
    rel_path: str
    markdown: str
    bytes: int


# ============================================================
# Ignore matching
# ============================================================

class IgnoreMatcher:
    """
    Small gitignore-like matcher implemented with stdlib only.
    """

    def __init__(self, patterns: Iterable[str]):
        self.patterns = [p.strip() for p in patterns if p.strip() and not p.strip().startswith("#")]

    def matches(self, rel_path: str, is_dir: bool) -> bool:
        rel_posix = rel_path.replace(os.sep, "/").strip("/")
        path_obj = PurePosixPath(rel_posix)
        included = True
        ignored = False

        for raw_pattern in self.patterns:
            negate = raw_pattern.startswith("!")
            pattern = raw_pattern[1:] if negate else raw_pattern
            if not pattern:
                continue

            if self._match_pattern(path_obj, pattern, is_dir):
                if negate:
                    ignored = False
                    included = True
                else:
                    ignored = True
                    included = False

        return ignored and not included

    def _match_pattern(self, path_obj: PurePosixPath, pattern: str, is_dir: bool) -> bool:
        path_str = str(path_obj)
        anchored = pattern.startswith("/")
        dir_only = pattern.endswith("/")

        normalized = pattern.strip("/")
        if not normalized:
            return False

        if dir_only and not is_dir:
            if path_str == normalized or path_str.startswith(normalized + "/"):
                return True

        if dir_only and is_dir:
            if path_str == normalized or path_str.startswith(normalized + "/"):
                return True

        candidate_patterns: list[str] = []

        if anchored:
            candidate_patterns.append(normalized)
        else:
            candidate_patterns.append(normalized)
            candidate_patterns.append(f"**/{normalized}")

        for candidate in candidate_patterns:
            if self._pure_match(path_obj, candidate):
                return True
            if fnmatch.fnmatch(path_str, candidate):
                return True

        return False

    @staticmethod
    def _pure_match(path_obj: PurePosixPath, pattern: str) -> bool:
        try:
            return path_obj.match(pattern)
        except Exception:
            return False


# ============================================================
# File selection and formatting
# ============================================================

def detect_language(path: Path) -> str:
    if path.name in SPECIAL_FILENAMES_TO_LANGUAGE:
        return SPECIAL_FILENAMES_TO_LANGUAGE[path.name]

    suffix = path.suffix.lower()
    if suffix in EXTENSION_TO_LANGUAGE:
        return EXTENSION_TO_LANGUAGE[suffix]

    if path.name.lower().endswith("dockerfile"):
        return "dockerfile"

    return "text"


def looks_binary(path: Path) -> bool:
    if path.name in BINARY_FILENAMES:
        return True

    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    try:
        with path.open("rb") as fh:
            chunk = fh.read(4096)
        if b"\x00" in chunk:
            return True
    except OSError:
        return True

    return False


def read_text_file(path: Path) -> str:
    return path.read_text(encoding=READ_FILE_ENCODING, errors=READ_FILE_ERRORS)


def make_markdown_fence(content: str, marker: str = "`") -> str:
    """
    Return a fence delimiter that cannot be closed by the file content.

    Markdown files can contain their own fenced code blocks. If we always wrap
    exported content in a plain triple-backtick block, an inner ``` line closes
    the outer export block early. Using a fence longer than any same-marker run
    in the content keeps the entire source file inside one wrapper block.
    """
    longest_run = 0
    current_run = 0

    for character in content:
        if character == marker:
            current_run += 1
            longest_run = max(longest_run, current_run)
        else:
            current_run = 0

    return marker * max(3, longest_run + 1)


def make_file_block(root: Path, path: Path) -> FileBlock:
    rel_path = path.relative_to(root).as_posix()
    language = detect_language(path)
    content = read_text_file(path)
    fence = make_markdown_fence(content)

    block = (
        f"## {rel_path}\n\n"
        f"{fence}{language}\n"
        f"{content}"
        f"\n{fence}\n"
    )

    return FileBlock(
        rel_path=rel_path,
        markdown=block,
        bytes=len(block.encode("utf-8")),
    )


def collect_files(root: Path, ignore_patterns: list[str]) -> list[Path]:
    matcher = IgnoreMatcher(ignore_patterns)
    collected: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)

        kept_dirnames: list[str] = []
        for dirname in sorted(dirnames):
            full_dir = current_dir / dirname
            rel_dir = full_dir.relative_to(root).as_posix()
            if matcher.matches(rel_dir, is_dir=True):
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for filename in sorted(filenames):
            full_file = current_dir / filename
            rel_file = full_file.relative_to(root).as_posix()

            if matcher.matches(rel_file, is_dir=False):
                continue
            if not full_file.is_file():
                continue
            if looks_binary(full_file):
                continue

            collected.append(full_file)

    collected.sort(key=lambda p: p.relative_to(root).as_posix())
    return collected


# ============================================================
# Partitioning
# ============================================================

def partition_by_soft_threshold(
    blocks: list[FileBlock],
    max_files: int,
    max_kb: int,
) -> list[list[FileBlock]]:
    if not blocks:
        return []

    if max_files <= 0:
        raise ValueError("max_files must be > 0")

    max_bytes = None if max_kb < 0 else max_kb * 1024

    # If threshold is disabled, always distribute evenly.
    if max_bytes is None:
        return partition_evenly_sequential(blocks, max_files)

    total_bytes = sum(block.bytes for block in blocks)
    capacity = max_files * max_bytes

    # If total content does not exceed total threshold capacity, do threshold-based packing.
    if total_bytes <= capacity:
        groups: list[list[FileBlock]] = []
        current_group: list[FileBlock] = []
        current_bytes = 0

        for block in blocks:
            would_exceed = current_group and (current_bytes + block.bytes > max_bytes)
            still_can_open_new_group = len(groups) < max_files - 1

            if would_exceed and still_can_open_new_group:
                groups.append(current_group)
                current_group = [block]
                current_bytes = block.bytes
            else:
                current_group.append(block)
                current_bytes += block.bytes

        if current_group:
            groups.append(current_group)

        return groups

    # Otherwise distribute evenly across exactly max_files outputs.
    return partition_evenly_sequential(blocks, max_files)


def partition_evenly_sequential(
    blocks: list[FileBlock],
    parts: int,
) -> list[list[FileBlock]]:
    if parts <= 0:
        raise ValueError("parts must be > 0")
    if not blocks:
        return []

    total_bytes = sum(block.bytes for block in blocks)
    groups: list[list[FileBlock]] = []
    start = 0
    consumed_bytes = 0

    for part_index in range(parts):
        remaining_parts = parts - part_index
        remaining_blocks = len(blocks) - start

        if remaining_blocks <= 0:
            break

        if remaining_parts == 1:
            groups.append(blocks[start:])
            break

        target_for_this_part = max(1, round((total_bytes - consumed_bytes) / remaining_parts))

        current: list[FileBlock] = []
        current_bytes = 0

        while start < len(blocks):
            block = blocks[start]

            must_leave_one_per_remaining_part = (len(blocks) - (start + 1)) >= (remaining_parts - 1)

            if not current:
                current.append(block)
                current_bytes += block.bytes
                start += 1
                continue

            current_diff = abs(target_for_this_part - current_bytes)
            next_diff = abs(target_for_this_part - (current_bytes + block.bytes))

            if must_leave_one_per_remaining_part and next_diff <= current_diff:
                current.append(block)
                current_bytes += block.bytes
                start += 1
            else:
                break

        groups.append(current)
        consumed_bytes += current_bytes

    return [g for g in groups if g]


# ============================================================
# Tree generation
# ============================================================

def build_tree_lines(root: Path, ignore_patterns: list[str]) -> list[str]:
    matcher = IgnoreMatcher(ignore_patterns)
    lines = [f"{root.name}/"]
    lines.extend(_build_tree_lines_recursive(root, root, matcher, prefix=""))
    return lines


def _build_tree_lines_recursive(root: Path, current: Path, matcher: IgnoreMatcher, prefix: str) -> list[str]:
    children = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

    visible_children: list[Path] = []
    for child in children:
        rel = child.relative_to(root).as_posix()
        if matcher.matches(rel, is_dir=child.is_dir()):
            continue
        visible_children.append(child)

    lines: list[str] = []
    for index, child in enumerate(visible_children):
        is_last = index == len(visible_children) - 1
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "
        name = child.name + ("/" if child.is_dir() else "")
        lines.append(prefix + connector + name)

        if child.is_dir():
            lines.extend(_build_tree_lines_recursive(root, child, matcher, prefix + extension))

    return lines


# ============================================================
# Writing output
# ============================================================

def write_tree_file(output_dir: Path, tree_lines: list[str]) -> None:
    content = "# Directory Tree\n\n```text\n" + "\n".join(tree_lines) + "\n```\n"
    (output_dir / TREE_FILE_NAME).write_text(content, encoding="utf-8")


def write_context_files(output_dir: Path, groups: list[list[FileBlock]]) -> None:
    width = max(2, len(str(len(groups))))

    for index, group in enumerate(groups, start=1):
        joined = "\n---\n\n".join(block.markdown.rstrip() for block in group).rstrip() + "\n"
        header = (
            f"# Repository Context Part {index}/{len(groups)}\n\n"
            f"Generated for LLM prompt context.\n\n"
        )
        filename = f"{OUTPUT_FILE_PREFIX}{index:0{width}d}.md"
        (output_dir / filename).write_text(header + joined, encoding="utf-8")


def print_summary(output_dir: Path, files: list[Path], groups: list[list[FileBlock]]) -> None:
    print(f"Export completed: {output_dir}")
    print(f"Included source files: {len(files)}")
    print(f"Context markdown files: {len(groups)}")
    for index, group in enumerate(groups, start=1):
        size_kb = sum(block.bytes for block in group) / 1024
        print(f"  - part {index}: {len(group)} files, {size_kb:.1f} KB")
    print(f"Tree file: {TREE_FILE_NAME}")


# ============================================================
# Main
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export repository code into markdown context files.")
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository root to scan. Defaults to current directory.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=f"Output directory. Defaults to <root>/{OUTPUT_DIR_NAME}",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()

    if not root.exists() or not root.is_dir():
        print(f"Error: root path is not a directory: {root}")
        return 1

    output_dir = Path(args.output_dir).resolve() if args.output_dir else root / OUTPUT_DIR_NAME

    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    files = collect_files(root, EXPORT_IGNORE_PATTERNS)
    blocks = [make_file_block(root, path) for path in files]

    groups = partition_by_soft_threshold(
        blocks,
        MAX_OUTPUT_FILES,
        MAX_OUTPUT_FILE_SIZE_KB,
    )

    tree_lines = build_tree_lines(root, TREE_IGNORE_PATTERNS)

    write_tree_file(output_dir, tree_lines)
    write_context_files(output_dir, groups)
    print_summary(output_dir, files, groups)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
````
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
from .core import ParameterSource as ParameterSource
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
from .exceptions import NoSuchCommand as NoSuchCommand
from .exceptions import NoSuchOption as NoSuchOption
from .exceptions import UsageError as UsageError
from .formatting import HelpFormatter as HelpFormatter
from .formatting import wrap_text as wrap_text
from .globals import get_current_context as get_current_context
from .termui import clear as clear
from .termui import confirm as confirm
from .termui import echo_via_pager as echo_via_pager
from .termui import edit as edit
from .termui import get_pager_file as get_pager_file
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
MAC = sys.platform == "darwin"
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
        elif hasattr(stream, "color"):
            # ._termui_impl.MaybeStripAnsi handles stripping ansi itself,
            # so we don't need to strip it here
            return False
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
---

## src/click/_termui_impl.py

```python
"""
This module contains implementations for the termui module. To keep the
import time of Click down, some infrequently used functionality is
placed in this module and only imported as needed.
"""

from __future__ import annotations

import collections.abc as cabc
import contextlib
import io
import math
import os
import shlex
import sys
import time
import typing as t
from gettext import gettext as _
from io import StringIO
from pathlib import Path
from types import TracebackType

from ._compat import _default_text_stdout
from ._compat import CYGWIN
from ._compat import get_best_encoding
from ._compat import isatty
from ._compat import strip_ansi
from ._compat import term_len
from ._compat import WIN
from .exceptions import ClickException
from .utils import echo

V = t.TypeVar("V")


class _BufferedTextPagerStream(t.Protocol):
    buffer: t.BinaryIO


def _has_binary_buffer(
    stream: t.BinaryIO | t.TextIO,
) -> t.TypeGuard[_BufferedTextPagerStream]:
    # TextIO is wider than TextIOWrapper; text-only streams such as StringIO
    # are valid TextIO values but do not expose a binary buffer to wrap.
    return getattr(stream, "buffer", None) is not None


if os.name == "nt":
    BEFORE_BAR = "\r"
    AFTER_BAR = "\n"
else:
    BEFORE_BAR = "\r\033[?25l"
    AFTER_BAR = "\033[?25h\n"


class ProgressBar(t.Generic[V]):
    def __init__(
        self,
        iterable: cabc.Iterable[V] | None,
        length: int | None = None,
        fill_char: str = "#",
        empty_char: str = " ",
        bar_template: str = "%(bar)s",
        info_sep: str = "  ",
        hidden: bool = False,
        show_eta: bool = True,
        show_percent: bool | None = None,
        show_pos: bool = False,
        item_show_func: t.Callable[[V | None], str | None] | None = None,
        label: str | None = None,
        file: t.TextIO | None = None,
        color: bool | None = None,
        update_min_steps: int = 1,
        width: int = 30,
    ) -> None:
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.bar_template = bar_template
        self.info_sep = info_sep
        self.hidden = hidden
        self.show_eta = show_eta
        self.show_percent = show_percent
        self.show_pos = show_pos
        self.item_show_func = item_show_func
        self.label: str = label or ""

        if file is None:
            file = _default_text_stdout()

            # There are no standard streams attached to write to. For example,
            # pythonw on Windows.
            if file is None:
                file = StringIO()

        self.file = file
        self.color = color
        self.update_min_steps = update_min_steps
        self._completed_intervals = 0
        self.width: int = width
        self.autowidth: bool = width == 0

        if length is None:
            from operator import length_hint

            length = length_hint(iterable, -1)

            if length == -1:
                length = None
        if iterable is None:
            if length is None:
                raise TypeError("iterable or length is required")
            iterable = t.cast("cabc.Iterable[V]", range(length))
        self.iter: cabc.Iterable[V] = iter(iterable)
        self.length = length
        self.pos: int = 0
        self.avg: list[float] = []
        self.last_eta: float
        self.start: float
        self.start = self.last_eta = time.time()
        self.eta_known: bool = False
        self.finished: bool = False
        self.max_width: int | None = None
        self.entered: bool = False
        self.current_item: V | None = None
        self._is_atty = isatty(self.file)
        self._last_line: str | None = None

    def __enter__(self) -> ProgressBar[V]:
        self.entered = True
        self.render_progress()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.render_finish()

    def __iter__(self) -> cabc.Iterator[V]:
        if not self.entered:
            raise RuntimeError("You need to use progress bars in a with block.")
        self.render_progress()
        return self.generator()

    def __next__(self) -> V:
        # Iteration is defined in terms of a generator function,
        # returned by iter(self); use that to define next(). This works
        # because `self.iter` is an iterable consumed by that generator,
        # so it is re-entry safe. Calling `next(self.generator())`
        # twice works and does "what you want".
        return next(iter(self))

    def render_finish(self) -> None:
        if self.hidden or not self._is_atty:
            return
        self.file.write(AFTER_BAR)
        self.file.flush()

    @property
    def pct(self) -> float:
        if self.finished:
            return 1.0
        return min(self.pos / (float(self.length or 1) or 1), 1.0)

    @property
    def time_per_iteration(self) -> float:
        if not self.avg:
            return 0.0
        return sum(self.avg) / float(len(self.avg))

    @property
    def eta(self) -> float:
        if self.length is not None and not self.finished:
            return self.time_per_iteration * (self.length - self.pos)
        return 0.0

    def format_eta(self) -> str:
        if self.eta_known:
            t = int(self.eta)
            seconds = t % 60
            t //= 60
            minutes = t % 60
            t //= 60
            hours = t % 24
            t //= 24
            if t > 0:
                return "{d}{day_label} {h:02}:{m:02}:{s:02}".format(
                    d=t,
                    day_label=_("d"),
                    h=hours,
                    m=minutes,
                    s=seconds,
                )
            else:
                return f"{hours:02}:{minutes:02}:{seconds:02}"
        return ""

    def format_pos(self) -> str:
        pos = str(self.pos)
        if self.length is not None:
            pos += f"/{self.length}"
        return pos

    def format_pct(self) -> str:
        return f"{int(self.pct * 100): 4}%"[1:]

    def format_bar(self) -> str:
        if self.length is not None:
            bar_length = int(self.pct * self.width)
            bar = self.fill_char * bar_length
            bar += self.empty_char * (self.width - bar_length)
        elif self.finished:
            bar = self.fill_char * self.width
        else:
            chars = list(self.empty_char * (self.width or 1))
            if self.time_per_iteration != 0:
                chars[
                    int(
                        (math.cos(self.pos * self.time_per_iteration) / 2.0 + 0.5)
                        * self.width
                    )
                ] = self.fill_char
            bar = "".join(chars)
        return bar

    def format_progress_line(self) -> str:
        show_percent = self.show_percent

        info_bits = []
        if self.length is not None and show_percent is None:
            show_percent = not self.show_pos

        if self.show_pos:
            info_bits.append(self.format_pos())
        if show_percent:
            info_bits.append(self.format_pct())
        if self.show_eta and self.eta_known and not self.finished:
            info_bits.append(self.format_eta())
        if self.item_show_func is not None:
            item_info = self.item_show_func(self.current_item)
            if item_info is not None:
                info_bits.append(item_info)

        return (
            self.bar_template
            % {
                "label": self.label,
                "bar": self.format_bar(),
                "info": self.info_sep.join(info_bits),
            }
        ).rstrip()

    def render_progress(self) -> None:
        if self.hidden:
            return

        if not self._is_atty:
            # Only output the label once if the output is not a TTY.
            if self._last_line != self.label:
                self._last_line = self.label
                echo(self.label, file=self.file, color=self.color)
            return

        buf = []
        # Update width in case the terminal has been resized
        if self.autowidth:
            import shutil

            old_width = self.width
            self.width = 0
            clutter_length = term_len(self.format_progress_line())
            new_width = max(0, shutil.get_terminal_size().columns - clutter_length)
            if new_width < old_width and self.max_width is not None:
                buf.append(BEFORE_BAR)
                buf.append(" " * self.max_width)
                self.max_width = new_width
            self.width = new_width

        clear_width = self.width
        if self.max_width is not None:
            clear_width = self.max_width

        buf.append(BEFORE_BAR)
        line = self.format_progress_line()
        line_len = term_len(line)
        if self.max_width is None or self.max_width < line_len:
            self.max_width = line_len

        buf.append(line)
        buf.append(" " * (clear_width - line_len))
        line = "".join(buf)
        # Render the line only if it changed.

        if line != self._last_line:
            self._last_line = line
            echo(line, file=self.file, color=self.color, nl=False)
            self.file.flush()

    def make_step(self, n_steps: int) -> None:
        self.pos += n_steps
        if self.length is not None and self.pos >= self.length:
            self.finished = True

        if (time.time() - self.last_eta) < 1.0:
            return

        self.last_eta = time.time()

        # self.avg is a rolling list of length <= 7 of steps where steps are
        # defined as time elapsed divided by the total progress through
        # self.length.
        if self.pos:
            step = (time.time() - self.start) / self.pos
        else:
            step = time.time() - self.start

        self.avg = self.avg[-6:] + [step]

        self.eta_known = self.length is not None

    def update(self, n_steps: int, current_item: V | None = None) -> None:
        """Update the progress bar by advancing a specified number of
        steps, and optionally set the ``current_item`` for this new
        position.

        :param n_steps: Number of steps to advance.
        :param current_item: Optional item to set as ``current_item``
            for the updated position.

        .. versionchanged:: 8.0
            Added the ``current_item`` optional parameter.

        .. versionchanged:: 8.0
            Only render when the number of steps meets the
            ``update_min_steps`` threshold.
        """
        if current_item is not None:
            self.current_item = current_item

        self._completed_intervals += n_steps

        if self._completed_intervals >= self.update_min_steps:
            self.make_step(self._completed_intervals)
            self.render_progress()
            self._completed_intervals = 0

    def finish(self) -> None:
        self.eta_known = False
        self.current_item = None
        self.finished = True

    def generator(self) -> cabc.Iterator[V]:
        """Return a generator which yields the items added to the bar
        during construction, and updates the progress bar *after* the
        yielded block returns.
        """
        # WARNING: the iterator interface for `ProgressBar` relies on
        # this and only works because this is a simple generator which
        # doesn't create or manage additional state. If this function
        # changes, the impact should be evaluated both against
        # `iter(bar)` and `next(bar)`. `next()` in particular may call
        # `self.generator()` repeatedly, and this must remain safe in
        # order for that interface to work.
        if not self.entered:
            raise RuntimeError("You need to use progress bars in a with block.")

        if not self._is_atty:
            yield from self.iter
        else:
            for rv in self.iter:
                self.current_item = rv

                # This allows show_item_func to be updated before the
                # item is processed. Only trigger at the beginning of
                # the update interval.
                if self._completed_intervals == 0:
                    self.render_progress()

                yield rv
                self.update(1)

            self.finish()
            self.render_progress()


class MaybeStripAnsi(io.TextIOWrapper):
    def __init__(self, stream: t.IO[bytes], *, color: bool, **kwargs: t.Any):
        super().__init__(stream, **kwargs)
        self.color = color

    def write(self, text: str) -> int:
        if not self.color:
            text = strip_ansi(text)
        return super().write(text)


def _pager_contextmanager(
    color: bool | None = None,
) -> t.ContextManager[tuple[t.BinaryIO | t.TextIO, str, bool]]:
    """Decide what method to use for paging through text."""
    stdout = _default_text_stdout()

    # There are no standard streams attached to write to. For example,
    # pythonw on Windows.
    if stdout is None:
        stdout = StringIO()

    if not isatty(sys.stdin) or not isatty(stdout):
        return _nullpager(stdout, color)

    # Split using POSIX mode (the default) so that quote characters are
    # stripped from tokens and quoted Windows paths are preserved.
    # Non-POSIX mode retains quotes in tokens, and wrapping tokens
    # with shlex.quote re-introduces quoting issues on Windows.
    pager_cmd_parts = shlex.split(os.environ.get("PAGER", ""))
    if pager_cmd_parts:
        if WIN:
            return _tempfilepager(pager_cmd_parts, color)
        return _pipepager(pager_cmd_parts, color)

    if os.environ.get("TERM") in ("dumb", "emacs"):
        return _nullpager(stdout, color)
    if WIN or sys.platform.startswith("os2"):
        return _tempfilepager(["more"], color)
    return _pipepager(["less"], color)


@contextlib.contextmanager
def get_pager_file(color: bool | None = None) -> t.Generator[t.TextIO, None, None]:
    """Context manager.
    Yields a writable file-like object which can be used as an output pager.
    .. versionadded:: 8.4
    :param color: controls if the pager supports ANSI colors or not.  The
                  default is autodetection.
    """
    with _pager_contextmanager(color=color) as (stream, encoding, color):
        # Split streams by capabilities rather than the abstract TextIO /
        # BinaryIO annotations: buffered text streams can be unwrapped to bytes,
        # while text-only streams are yielded as-is.
        if _has_binary_buffer(stream):
            # Text stream backed by a binary buffer.
            stream = MaybeStripAnsi(stream.buffer, color=color, encoding=encoding)
        elif isinstance(stream, t.BinaryIO):
            # Binary stream
            stream = MaybeStripAnsi(stream, color=color, encoding=encoding)
        try:
            yield stream
        finally:
            stream.flush()


@contextlib.contextmanager
def _pipepager(
    cmd_parts: list[str], color: bool | None = None
) -> t.Iterator[tuple[t.BinaryIO | t.TextIO, str, bool]]:
    """Page through text by feeding it to another program.

    Invokes the pager via :class:`subprocess.Popen` with an ``argv`` list
    produced by :func:`shlex.split`. The command is resolved to an absolute
    path with :func:`shutil.which` as recommended by the
    :mod:`subprocess` docs for Windows compatibility.

    Invoking a pager through this might support colors: if piping to
    ``less`` and the user hasn't decided on colors, ``LESS=-R`` is set
    automatically.
    """
    # Split the command into the invoked CLI and its parameters.
    if not cmd_parts:
        stdout = _default_text_stdout() or StringIO()
        yield stdout, "utf-8", False
        return

    import shutil

    cmd = cmd_parts[0]
    cmd_params = cmd_parts[1:]

    cmd_filepath = shutil.which(cmd)
    if not cmd_filepath:
        stdout = _default_text_stdout() or StringIO()
        yield stdout, "utf-8", False
        return

    # Produces a normalized absolute path string.
    # multi-call binaries such as busybox derive their identity from the symlink
    # less -> busybox. resolve() causes them to misbehave. (eg. less becomes busybox)
    cmd_path = Path(cmd_filepath).absolute()
    cmd_name = cmd_path.name

    import subprocess

    # Make a local copy of the environment to not affect the global one.
    env = dict(os.environ)

    # If we're piping to less and the user hasn't decided on colors, we enable
    # them by default we find the -R flag in the command line arguments.
    if color is None and cmd_name == "less":
        less_flags = f"{os.environ.get('LESS', '')}{' '.join(cmd_params)}"
        if not less_flags:
            env["LESS"] = "-R"
            color = True
        elif "r" in less_flags or "R" in less_flags:
            color = True

    if color is None:
        color = False

    c = subprocess.Popen(
        [str(cmd_path)] + cmd_params,
        shell=False,
        stdin=subprocess.PIPE,
        env=env,
        errors="replace",
        text=True,
    )
    stdin = t.cast(t.BinaryIO, c.stdin)
    encoding = get_best_encoding(stdin)
    try:
        yield stdin, encoding, color
    except BrokenPipeError:
        # In case the pager exited unexpectedly, ignore the broken pipe error.
        pass
    except Exception as e:
        # In case there is an exception we want to close the pager immediately
        # and let the caller handle it.
        # Otherwise the pager will keep running, and the user may not notice
        # the error message, or worse yet it may leave the terminal in a broken state.
        c.terminate()
        raise e
    finally:
        # We must close stdin and wait for the pager to exit before we continue
        try:
            stdin.close()
        # Close implies flush, so it might throw a BrokenPipeError if the pager
        # process exited already.
        except BrokenPipeError:
            pass

        # Less doesn't respect ^C, but catches it for its own UI purposes (aborting
        # search or other commands inside less).
        #
        # That means when the user hits ^C, the parent process (click) terminates,
        # but less is still alive, paging the output and messing up the terminal.
        #
        # If the user wants to make the pager exit on ^C, they should set
        # `LESS='-K'`. It's not our decision to make.
        while True:
            try:
                c.wait()
            except KeyboardInterrupt:
                pass
            else:
                break


@contextlib.contextmanager
def _tempfilepager(
    cmd_parts: list[str], color: bool | None = None
) -> t.Iterator[tuple[t.BinaryIO | t.TextIO, str, bool]]:
    """Page through text by invoking a program on a temporary file.

    Used as the primary pager strategy on Windows (where piping to
    ``more`` adds spurious ``\\r\\n``), and as a fallback on other
    platforms. The command is resolved to an absolute path with
    :func:`shutil.which`.
    """
    # Split the command into the invoked CLI and its parameters.
    if not cmd_parts:
        stdout = _default_text_stdout() or StringIO()
        yield stdout, "utf-8", False
        return

    import shutil
    import subprocess

    cmd = cmd_parts[0]

    cmd_filepath = shutil.which(cmd)
    if not cmd_filepath:
        stdout = _default_text_stdout() or StringIO()
        yield stdout, "utf-8", False
        return

    # Produces a normalized absolute path string.
    # multi-call binaries such as busybox derive their identity from the symlink
    # less -> busybox. resolve() causes them to misbehave. (eg. less becomes busybox)
    cmd_path = Path(cmd_filepath).absolute()

    import tempfile

    encoding = get_best_encoding(sys.stdout)
    if color is None:
        color = False
    # On Windows, NamedTemporaryFile cannot be opened by another process
    # while Python still has it open, so we use delete=False and clean up manually
    # rather than using a contextmanager here.
    f = tempfile.NamedTemporaryFile(mode="wb", delete=False)
    try:
        yield t.cast(t.BinaryIO, f), encoding, color
        f.flush()
        f.close()
        subprocess.call([str(cmd_path), f.name])
    finally:
        os.unlink(f.name)


@contextlib.contextmanager
def _nullpager(
    stream: t.TextIO, color: bool | None = None
) -> t.Iterator[tuple[t.TextIO, str, bool]]:
    """Simply print unformatted text.  This is the ultimate fallback."""
    encoding = get_best_encoding(stream)
    if color is None:
        color = False
    yield stream, encoding, color


class Editor:
    def __init__(
        self,
        editor: str | None = None,
        env: cabc.Mapping[str, str] | None = None,
        require_save: bool = True,
        extension: str = ".txt",
    ) -> None:
        self.editor = editor
        self.env = env
        self.require_save = require_save
        self.extension = extension

    def get_editor(self) -> str:
        if self.editor is not None:
            return self.editor
        for key in "VISUAL", "EDITOR":
            rv = os.environ.get(key)
            if rv:
                return rv
        if WIN:
            return "notepad"

        from shutil import which

        for editor in "sensible-editor", "vim", "nano":
            if which(editor) is not None:
                return editor
        return "vi"

    def edit_files(self, filenames: cabc.Iterable[str]) -> None:
        """Open files in the user's editor."""
        import shlex
        import subprocess

        editor = self.get_editor()
        environ: dict[str, str] | None = None

        if self.env:
            environ = os.environ.copy()
            environ.update(self.env)

        try:
            # Split in POSIX mode (the default) for the same reasons as
            # in pager(): strips quotes from tokens and preserves quoted
            # Windows paths.
            c = subprocess.Popen(
                args=shlex.split(editor) + list(filenames),
                env=environ,
            )
            exit_code = c.wait()
            if exit_code != 0:
                raise ClickException(
                    _("{editor}: Editing failed").format(editor=editor)
                )
        except OSError as e:
            raise ClickException(
                _("{editor}: Editing failed: {e}").format(editor=editor, e=e)
            ) from e

    @t.overload
    def edit(self, text: bytes | bytearray) -> bytes | None: ...

    # We cannot know whether or not the type expected is str or bytes when None
    # is passed, so str is returned as that was what was done before.
    @t.overload
    def edit(self, text: str | None) -> str | None: ...

    def edit(self, text: str | bytes | bytearray | None) -> str | bytes | None:
        import tempfile

        if text is None:
            data: bytes | bytearray = b""
        elif isinstance(text, (bytes, bytearray)):
            data = text
        else:
            if text and not text.endswith("\n"):
                text += "\n"

            if WIN:
                data = text.replace("\n", "\r\n").encode("utf-8-sig")
            else:
                data = text.encode("utf-8")

        fd, name = tempfile.mkstemp(prefix="editor-", suffix=self.extension)
        f: t.BinaryIO

        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)

            # If the filesystem resolution is 1 second, like Mac OS
            # 10.12 Extended, or 2 seconds, like FAT32, and the editor
            # closes very fast, require_save can fail. Set the modified
            # time to be 2 seconds in the past to work around this.
            os.utime(name, (os.path.getatime(name), os.path.getmtime(name) - 2))
            # Depending on the resolution, the exact value might not be
            # recorded, so get the new recorded value.
            timestamp = os.path.getmtime(name)

            self.edit_files((name,))

            if self.require_save and os.path.getmtime(name) == timestamp:
                return None

            with open(name, "rb") as f:
                rv = f.read()

            if isinstance(text, (bytes, bytearray)):
                return rv

            return rv.decode("utf-8-sig").replace("\r\n", "\n")
        finally:
            os.unlink(name)


def open_url(url: str, wait: bool = False, locate: bool = False) -> int:
    import subprocess

    def _unquote_file(url: str) -> str:
        from urllib.parse import unquote

        if url.startswith("file://"):
            url = unquote(url[7:])

        return url

    if sys.platform == "darwin":
        args = ["open"]
        if wait:
            args.append("-W")
        if locate:
            args.append("-R")
        args.append(_unquote_file(url))
        null = open("/dev/null", "w")
        try:
            return subprocess.Popen(args, stderr=null).wait()
        finally:
            null.close()
    elif WIN:
        if locate:
            url = _unquote_file(url)
            args = ["explorer", "/select,", url]
            try:
                return subprocess.call(args)
            except OSError:
                return 127
        else:
            try:
                os.startfile(url)  # type: ignore[attr-defined]
            except OSError:
                return 127
            return 0
    elif CYGWIN:
        if locate:
            url = _unquote_file(url)
            args = ["cygstart", os.path.dirname(url)]
        else:
            args = ["cygstart"]
            if wait:
                args.append("-w")
            args.append(url)
        try:
            return subprocess.call(args)
        except OSError:
            # Command not found
            return 127

    try:
        if locate:
            url = os.path.dirname(_unquote_file(url)) or "."
        else:
            url = _unquote_file(url)
        c = subprocess.Popen(["xdg-open", url])
        if wait:
            return c.wait()
        return 0
    except OSError:
        if url.startswith(("http://", "https://")) and not locate and not wait:
            import webbrowser

            webbrowser.open(url)
            return 0
        return 1


def _translate_ch_to_exc(ch: str) -> None:
    if ch == "\x03":
        raise KeyboardInterrupt()

    if ch == "\x04" and not WIN:  # Unix-like, Ctrl+D
        raise EOFError()

    if ch == "\x1a" and WIN:  # Windows, Ctrl+Z
        raise EOFError()


if sys.platform == "win32":
    import msvcrt

    @contextlib.contextmanager
    def raw_terminal() -> cabc.Iterator[int]:
        yield -1

    def getchar(echo: bool) -> str:
        # The function `getch` will return a bytes object corresponding to
        # the pressed character. Since Windows 10 build 1803, it will also
        # return \x00 when called a second time after pressing a regular key.
        #
        # `getwch` does not share this probably-bugged behavior. Moreover, it
        # returns a Unicode object by default, which is what we want.
        #
        # Either of these functions will return \x00 or \xe0 to indicate
        # a special key, and you need to call the same function again to get
        # the "rest" of the code. The fun part is that \u00e0 is
        # "latin small letter a with grave", so if you type that on a French
        # keyboard, you _also_ get a \xe0.
        # E.g., consider the Up arrow. This returns \xe0 and then \x48. The
        # resulting Unicode string reads as "a with grave" + "capital H".
        # This is indistinguishable from when the user actually types
        # "a with grave" and then "capital H".
        #
        # When \xe0 is returned, we assume it's part of a special-key sequence
        # and call `getwch` again, but that means that when the user types
        # the \u00e0 character, `getchar` doesn't return until a second
        # character is typed.
        # The alternative is returning immediately, but that would mess up
        # cross-platform handling of arrow keys and others that start with
        # \xe0. Another option is using `getch`, but then we can't reliably
        # read non-ASCII characters, because return values of `getch` are
        # limited to the current 8-bit codepage.
        #
        # Anyway, Click doesn't claim to do this Right(tm), and using `getwch`
        # is doing the right thing in more situations than with `getch`.

        if echo:
            func = t.cast(t.Callable[[], str], msvcrt.getwche)
        else:
            func = t.cast(t.Callable[[], str], msvcrt.getwch)

        rv = func()

        if rv in ("\x00", "\xe0"):
            # \x00 and \xe0 are control characters that indicate special key,
            # see above.
            rv += func()

        _translate_ch_to_exc(rv)
        return rv

else:
    import termios
    import tty

    @contextlib.contextmanager
    def raw_terminal() -> cabc.Iterator[int]:
        f: t.TextIO | None
        fd: int

        if not isatty(sys.stdin):
            f = open("/dev/tty")
            fd = f.fileno()
        else:
            fd = sys.stdin.fileno()
            f = None

        try:
            old_settings = termios.tcgetattr(fd)

            try:
                tty.setraw(fd)
                yield fd
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                sys.stdout.flush()

                if f is not None:
                    f.close()
        except termios.error:
            pass

    def getchar(echo: bool) -> str:
        with raw_terminal() as fd:
            ch = os.read(fd, 32).decode(get_best_encoding(sys.stdin), "replace")

            if echo and isatty(sys.stdout):
                sys.stdout.write(ch)

            _translate_ch_to_exc(ch)
            return ch

```
---

## src/click/_textwrap.py

```python
from __future__ import annotations

import collections.abc as cabc
import textwrap
from contextlib import contextmanager

from ._compat import _ansi_re
from ._compat import term_len


def _truncate_visible(text: str, n: int) -> str:
    """Return the longest prefix of ``text`` containing at most ``n`` visible
    characters.

    ANSI escape sequences inside the prefix are kept intact and do not count
    toward the visible width. A cut is never placed inside an escape sequence.
    """
    if n <= 0:
        return ""

    visible = 0
    i = 0
    cut = 0
    end = len(text)
    while i < end:
        m = _ansi_re.match(text, i)
        if m is not None:
            i = m.end()
            continue
        visible += 1
        i += 1
        cut = i
        if visible >= n:
            break
    return text[:cut]


class TextWrapper(textwrap.TextWrapper):
    """``textwrap.TextWrapper`` variant that measures widths by visible
    character count.

    ANSI escape sequences embedded in chunks, indents, or the placeholder are
    excluded from the width budget. Without this, styled help text (a styled
    ``Usage:`` prefix, a colorized option name, ...) would be wrapped earlier
    than its visible length warrants and tokens would split mid-word.
    """

    def _handle_long_word(
        self,
        reversed_chunks: list[str],
        cur_line: list[str],
        cur_len: int,
        width: int,
    ) -> None:
        space_left = max(width - cur_len, 1)

        if self.break_long_words:
            last = reversed_chunks[-1]
            cut = _truncate_visible(last, space_left)
            res = last[len(cut) :]
            cur_line.append(cut)
            reversed_chunks[-1] = res
        elif not cur_line:
            cur_line.append(reversed_chunks.pop())

    def _wrap_chunks(self, chunks: list[str]) -> list[str]:
        """Wrap chunks counting widths in visible characters.

        Mirrors the algorithm of :meth:`textwrap.TextWrapper._wrap_chunks`
        with every width measurement routed through
        :func:`click._compat.term_len` instead of :func:`len`, so ANSI escape
        bytes in chunks, indents, or the placeholder do not inflate the count.

        .. seealso::
            :class:`textwrap.TextWrapper` in the Python standard library documentation:
            https://docs.python.org/3/library/textwrap.html#textwrap.TextWrapper

            Reference implementation in CPython:
            https://github.com/python/cpython/blob/main/Lib/textwrap.py
        """
        lines: list[str] = []
        if self.width <= 0:
            raise ValueError(f"invalid width {self.width!r} (must be > 0)")
        if self.max_lines is not None:
            if self.max_lines > 1:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent
            if term_len(indent) + term_len(self.placeholder.lstrip()) > self.width:
                raise ValueError("placeholder too large for max width")

        chunks.reverse()

        while chunks:
            cur_line: list[str] = []
            cur_len = 0

            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent

            width = self.width - term_len(indent)

            if self.drop_whitespace and chunks[-1].strip() == "" and lines:
                del chunks[-1]

            while chunks:
                n = term_len(chunks[-1])

                if cur_len + n <= width:
                    cur_line.append(chunks.pop())
                    cur_len += n

                else:
                    break

            if chunks and term_len(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)
                cur_len = sum(map(term_len, cur_line))

            if self.drop_whitespace and cur_line and cur_line[-1].strip() == "":
                cur_len -= term_len(cur_line[-1])
                del cur_line[-1]

            if cur_line:
                if (
                    self.max_lines is None
                    or len(lines) + 1 < self.max_lines
                    or (
                        not chunks
                        or self.drop_whitespace
                        and len(chunks) == 1
                        and not chunks[0].strip()
                    )
                    and cur_len <= width
                ):
                    lines.append(indent + "".join(cur_line))
                else:
                    while cur_line:
                        if (
                            cur_line[-1].strip()
                            and cur_len + term_len(self.placeholder) <= width
                        ):
                            cur_line.append(self.placeholder)
                            lines.append(indent + "".join(cur_line))
                            break
                        cur_len -= term_len(cur_line[-1])
                        del cur_line[-1]
                    else:
                        if lines:
                            prev_line = lines[-1].rstrip()
                            if (
                                term_len(prev_line) + term_len(self.placeholder)
                                <= self.width
                            ):
                                lines[-1] = prev_line + self.placeholder
                                break
                        lines.append(indent + self.placeholder.lstrip())
                    break

        return lines

    @contextmanager
    def extra_indent(self, indent: str) -> cabc.Iterator[None]:
        old_initial_indent = self.initial_indent
        old_subsequent_indent = self.subsequent_indent
        self.initial_indent += indent
        self.subsequent_indent += indent

        try:
            yield
        finally:
            self.initial_indent = old_initial_indent
            self.subsequent_indent = old_subsequent_indent

    def indent_only(self, text: str) -> str:
        rv = []

        for idx, line in enumerate(text.splitlines()):
            indent = self.initial_indent

            if idx > 0:
                indent = self.subsequent_indent

            rv.append(f"{indent}{line}")

        return "\n".join(rv)

```
---

## src/click/_utils.py

```python
from __future__ import annotations

import enum
import typing as t


class Sentinel(enum.Enum):
    """Enum used to define sentinel values.

    .. seealso::

        `PEP 661 - Sentinel Values <https://peps.python.org/pep-0661/>`_.
    """

    UNSET = object()
    FLAG_NEEDS_VALUE = object()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


UNSET: t.Literal[Sentinel.UNSET] = Sentinel.UNSET
"""Sentinel used to indicate that a value is not set."""

FLAG_NEEDS_VALUE: t.Literal[Sentinel.FLAG_NEEDS_VALUE] = Sentinel.FLAG_NEEDS_VALUE
"""Sentinel used to indicate an option was passed as a flag without a
value but is not a flag option.

``Option.consume_value`` uses this to prompt or use the ``flag_value``.
"""

T_UNSET: t.TypeAlias = t.Literal[Sentinel.UNSET]
"""Type hint for the :data:`UNSET` sentinel value."""

T_FLAG_NEEDS_VALUE: t.TypeAlias = t.Literal[Sentinel.FLAG_NEEDS_VALUE]
"""Type hint for the :data:`FLAG_NEEDS_VALUE` sentinel value."""

```
---

## src/click/_winconsole.py

```python
# This module is based on the excellent work by Adam Bartoš who
# provided a lot of what went into the implementation here in
# the discussion to issue1602 in the Python bug tracker.
#
# There are some general differences in regards to how this works
# compared to the original patches as we do not need to patch
# the entire interpreter but just work in our little world of
# echo and prompt.
from __future__ import annotations

import collections.abc as cabc
import io
import sys
import time
import typing as t
from ctypes import Array
from ctypes import byref
from ctypes import c_char
from ctypes import c_char_p
from ctypes import c_int
from ctypes import c_ssize_t
from ctypes import c_ulong
from ctypes import c_void_p
from ctypes import POINTER
from ctypes import py_object
from ctypes import Structure
from ctypes.wintypes import DWORD
from ctypes.wintypes import HANDLE
from ctypes.wintypes import LPCWSTR
from ctypes.wintypes import LPWSTR
from gettext import gettext as _

from ._compat import _NonClosingTextIOWrapper

assert sys.platform == "win32"
import msvcrt  # noqa: E402
from ctypes import windll  # noqa: E402
from ctypes import WINFUNCTYPE  # noqa: E402

c_ssize_p = POINTER(c_ssize_t)

kernel32 = windll.kernel32
GetStdHandle = kernel32.GetStdHandle
ReadConsoleW = kernel32.ReadConsoleW
WriteConsoleW = kernel32.WriteConsoleW
GetConsoleMode = kernel32.GetConsoleMode
GetLastError = kernel32.GetLastError
GetCommandLineW = WINFUNCTYPE(LPWSTR)(("GetCommandLineW", windll.kernel32))
CommandLineToArgvW = WINFUNCTYPE(POINTER(LPWSTR), LPCWSTR, POINTER(c_int))(
    ("CommandLineToArgvW", windll.shell32)
)
LocalFree = WINFUNCTYPE(c_void_p, c_void_p)(("LocalFree", windll.kernel32))

STDIN_HANDLE = GetStdHandle(-10)
STDOUT_HANDLE = GetStdHandle(-11)
STDERR_HANDLE = GetStdHandle(-12)

PyBUF_SIMPLE = 0
PyBUF_WRITABLE = 1

ERROR_SUCCESS = 0
ERROR_NOT_ENOUGH_MEMORY = 8
ERROR_OPERATION_ABORTED = 995

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

EOF = b"\x1a"
MAX_BYTES_WRITTEN = 32767

if t.TYPE_CHECKING:
    try:
        # Using `typing_extensions.Buffer` instead of `collections.abc`
        # on Windows for some reason does not have `Sized` implemented.
        from collections.abc import Buffer  # type: ignore
    except ImportError:
        from typing_extensions import Buffer

try:
    from ctypes import pythonapi
except ImportError:
    # On PyPy we cannot get buffers so our ability to operate here is
    # severely limited.
    get_buffer = None
else:

    class Py_buffer(Structure):
        _fields_ = [  # noqa: RUF012
            ("buf", c_void_p),
            ("obj", py_object),
            ("len", c_ssize_t),
            ("itemsize", c_ssize_t),
            ("readonly", c_int),
            ("ndim", c_int),
            ("format", c_char_p),
            ("shape", c_ssize_p),
            ("strides", c_ssize_p),
            ("suboffsets", c_ssize_p),
            ("internal", c_void_p),
        ]

    PyObject_GetBuffer = pythonapi.PyObject_GetBuffer
    PyBuffer_Release = pythonapi.PyBuffer_Release

    def get_buffer(obj: Buffer, writable: bool = False) -> Array[c_char]:
        buf = Py_buffer()
        flags: int = PyBUF_WRITABLE if writable else PyBUF_SIMPLE
        PyObject_GetBuffer(py_object(obj), byref(buf), flags)

        try:
            buffer_type = c_char * buf.len
            out: Array[c_char] = buffer_type.from_address(buf.buf)
            return out
        finally:
            PyBuffer_Release(byref(buf))


class _WindowsConsoleRawIOBase(io.RawIOBase):
    def __init__(self, handle: int | None) -> None:
        self.handle = handle

    def isatty(self) -> t.Literal[True]:
        super().isatty()
        return True


class _WindowsConsoleReader(_WindowsConsoleRawIOBase):
    def readable(self) -> t.Literal[True]:
        return True

    def readinto(self, b: Buffer) -> int:
        bytes_to_be_read = len(b)
        if not bytes_to_be_read:
            return 0
        elif bytes_to_be_read % 2:
            raise ValueError(
                "cannot read odd number of bytes from UTF-16-LE encoded console"
            )

        buffer = get_buffer(b, writable=True)
        code_units_to_be_read = bytes_to_be_read // 2
        code_units_read = c_ulong()

        rv = ReadConsoleW(
            HANDLE(self.handle),
            buffer,
            code_units_to_be_read,
            byref(code_units_read),
            None,
        )
        if GetLastError() == ERROR_OPERATION_ABORTED:
            # wait for KeyboardInterrupt
            time.sleep(0.1)
        if not rv:
            raise OSError(_("Windows error: {error}").format(error=GetLastError()))

        if buffer[0] == EOF:
            return 0
        return 2 * code_units_read.value


class _WindowsConsoleWriter(_WindowsConsoleRawIOBase):
    def writable(self) -> t.Literal[True]:
        return True

    @staticmethod
    def _get_error_message(errno: int) -> str:
        if errno == ERROR_SUCCESS:
            return "ERROR_SUCCESS"
        elif errno == ERROR_NOT_ENOUGH_MEMORY:
            return "ERROR_NOT_ENOUGH_MEMORY"
        return _("Windows error: {error}").format(error=errno)

    def write(self, b: Buffer) -> int:
        bytes_to_be_written = len(b)
        buf = get_buffer(b)
        code_units_to_be_written = min(bytes_to_be_written, MAX_BYTES_WRITTEN) // 2
        code_units_written = c_ulong()

        WriteConsoleW(
            HANDLE(self.handle),
            buf,
            code_units_to_be_written,
            byref(code_units_written),
            None,
        )
        bytes_written = 2 * code_units_written.value

        if bytes_written == 0 and bytes_to_be_written > 0:
            raise OSError(self._get_error_message(GetLastError()))
        return bytes_written


class ConsoleStream:
    def __init__(self, text_stream: t.TextIO, byte_stream: t.BinaryIO) -> None:
        self._text_stream = text_stream
        self.buffer = byte_stream

    @property
    def name(self) -> str:
        return self.buffer.name

    def write(self, x: t.AnyStr) -> int:
        if isinstance(x, str):
            return self._text_stream.write(x)
        try:
            self.flush()
        except Exception:
            pass
        return self.buffer.write(x)

    def writelines(self, lines: cabc.Iterable[t.AnyStr]) -> None:
        for line in lines:
            self.write(line)

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self._text_stream, name)

    def isatty(self) -> bool:
        return self.buffer.isatty()

    def __repr__(self) -> str:
        return f"<ConsoleStream name={self.name!r} encoding={self.encoding!r}>"


def _get_text_stdin(buffer_stream: t.BinaryIO) -> t.TextIO:
    text_stream = _NonClosingTextIOWrapper(
        io.BufferedReader(_WindowsConsoleReader(STDIN_HANDLE)),
        "utf-16-le",
        "strict",
        line_buffering=True,
    )
    return t.cast(t.TextIO, ConsoleStream(text_stream, buffer_stream))


def _get_text_stdout(buffer_stream: t.BinaryIO) -> t.TextIO:
    text_stream = _NonClosingTextIOWrapper(
        io.BufferedWriter(_WindowsConsoleWriter(STDOUT_HANDLE)),
        "utf-16-le",
        "strict",
        line_buffering=True,
    )
    return t.cast(t.TextIO, ConsoleStream(text_stream, buffer_stream))


def _get_text_stderr(buffer_stream: t.BinaryIO) -> t.TextIO:
    text_stream = _NonClosingTextIOWrapper(
        io.BufferedWriter(_WindowsConsoleWriter(STDERR_HANDLE)),
        "utf-16-le",
        "strict",
        line_buffering=True,
    )
    return t.cast(t.TextIO, ConsoleStream(text_stream, buffer_stream))


_stream_factories: cabc.Mapping[int, t.Callable[[t.BinaryIO], t.TextIO]] = {
    0: _get_text_stdin,
    1: _get_text_stdout,
    2: _get_text_stderr,
}


def _is_console(f: t.TextIO) -> bool:
    if not hasattr(f, "fileno"):
        return False

    try:
        fileno = f.fileno()
    except (OSError, io.UnsupportedOperation):
        return False

    handle = msvcrt.get_osfhandle(fileno)
    return bool(GetConsoleMode(handle, byref(DWORD())))


def _get_windows_console_stream(
    f: t.TextIO, encoding: str | None, errors: str | None
) -> t.TextIO | None:
    if (
        get_buffer is None
        or encoding not in {"utf-16-le", None}
        or errors not in {"strict", None}
        or not _is_console(f)
    ):
        return None

    func = _stream_factories.get(f.fileno())
    if func is None:
        return None

    b = getattr(f, "buffer", None)

    if b is None:
        return None

    return func(b)

```
