Introduction
============

Dawdaw is an experiment to make a [SaltStack](http://www.saltstack.com/) custom [renderer](http://docs.saltstack.com/en/latest/ref/renderers/index.html) (the stuff that allows you to write your states in yaml/jinja2/mako/other) in an attempt to solve those problems:

* current states are extremely too verbose to write
* you often repeat yourself way too much
* really have a linear states declaration for requires
* explicit requires on included states, because global sucks
* namespacing all the things, because global sucks
* indirectly trying to solve the "salt states totally sucks are being redistributed" problem by going full python, you can now use setup.py and pypi/pip to redistribute you work¹

Disadvantages: you move await from full declarative code (which you were
already doing in fact with jinja2 templates) to go back to python code. This
is, on one hand very powerful, on the other hand probably too powerful (and may
be way less easy to understand for devops that don't come from a programming
background). That works for me because I'm a python dev and I'm using this for
my personal usages, but that might not fit your case.

Sample
======

Move from:

```yaml
include:
  - dotfiles

wyrd-pkgs:
  pkg.installed:
    - name: wyrd
    - require:
      - sls: dotfiles

reminds.git:
  git.latest:
    - name: ssh://git@bitbucket.org/psycojoker/reminds.git
    - runas: psycojoker
    - target: /home/psycojoker/reminds/
    - require:
      - pkg: git

cd /home/psycojoker/reminds/ && bash init:
  cmd.run:
    - unless: ls /home/psycojoker/.reminders /home/psycojoker/.reminders.gcl
    - user: psycojoker
    - require:
      - git: reminds.git
```

To:

```python
#!dawdaw_template

from dawdaw.states import pkg, git, cmd, include
from dawdaw.utils import default, test, debug

dotfiles = include("dotfiles")

with default(user="psycojoker", runas="psycojoker"):
    pkg.installed("wyrd",
                  require=[dotfiles.get("pkg", "dotfiles-pkgs")])
    git.latest("ssh://git@bitbucket.org/psycojoker/reminds.git",
               target="/home/psycojoker/reminds/")

    if not test("ls /home/psycojoker/.reminders /home/psycojoker/.reminders.gcl"):
        cmd.run("cd /home/psycojoker/reminds/ && bash init")
```

Installation
============

    pip install dawdaw

    # this is how you install a renderer in salt
    # if you know a better way to distribute it, plz tell me

    # adapt the path to the location of your salt data
    mkdir -p /srv/salt/_renderers
    touch /srv/salt/_renderers/__init__.py

    curl "https://raw.githubusercontent.com/Psycojoker/dawdaw/master/dawdaw_template.py" > /srv/salt/_renderers/dawdaw_template.py

    # if you use salt in master/slave
    salt '*' saltutil.sync_renderers
    # or locally
    salt-call --local saltutil.sync_renderers

Once it's done, you can normally run highstates, this will handle
dawdaw_template like any regular other state.

Documentation
=============

Once you have installed dawdaw (see previous section), to use it, you simply need to put this as the first line of your file (<code>dawdaw_template</code> being the name of the file under which you have redirected the curl command bellow):

```python
#!dawdaw_template
```

States
------

Using states is extremely simple: just import the state module and call the
corresponding function like a python function.

### Example

```yaml
state_name:
  state_module.state_function:
    - argument_1: value_1
    - argument_2: value_2
    - argument_3: value_3
    ...
```

Become:

```python
from dawdaw.states import state_module

state_module.state_function("state_name",
                            argument_1="value_1",
                            argument_2="value_2",
                            argument_3="value_3",
                            ...)
```

### Another example

```yaml
https://github.com/Psycojoker/dawdaw:
  git.latest:
    - target: /tmp/dawdaw
```

Become:

```python
from dawdaw.states import git

git.latest("https://github.com/Psycojoker/dawdaw", target="/tmp/dawdaw")
```

The 'default' context manager
-----------------------------

In salt, you often end up repeating the same arguments a lot, like settings the
prioprietary of the file to the same user a lot. This is boring and not error proof.
Sure, the
'[use](http://docs.saltstack.com/en/latest/ref/states/requisites.html#use)'
exists, but it's awkward and no one knows about it. Thanks to python, we have
context managers and we can use the <code>with</code> keyword to handle that.

The <code>default</code> context manager create a context in which **every
command that waits for some specific keywords will be called with it**.

### Example

```python
from dawdaw.states import git, file
from dawdaw.utils import default


with default(makedirs=True): 
    # git won't received the 'makedirs' keyword
    git.latest("https:/...", target="/some/stuf")

    # file will received it
    file.managed("/some/stuff/subdir/settings_prod.py", source="...")
```

I often end up using it to settings user and groups:

```python
with default(user='psycojoker', group='psycojoker', runas='psycojoker'): 
    # ...
```

Modules
-------

(The stuff you use in the CLI like <code>salt '*' cmd.run "ls /tmp"). As simple
as states, just import it and call it like normal python code (and play with
it's return like in normal python):

```python
from dawdaw.modules import cmd

for f in cmd.run("ls /tmp"):
    # do some stuff with 'f'
```

The 'test' helper
-----------------

Sometime, you need to test if a command return the code '0', you can do it
using <code>cmd.retcode("...")</code> but that's quite boring. Dawdaw provides
a simple helper to do that for you:

```python
from dawdaw.utils import test

if test("ls /tmp/this_file_exist"):
    # do some stuff
```

Requisites
----------

In dawdaw, you don't have to care that much about requisites, a linear
execution of the states in the order in which they are called is enforced. This
mean, that, in this example, <code>module.b</code> will have a require on
<code>module.a</code> and <code>module.c</code> will have a require on
<code>module.b</code> **and** <code>module.c</code>:

```python
module.a("...")
module.b("...")
module.c("...")
```

The requires are only set if the state is actually called, so you can use 'if'
and other control flow structure the way you want like in normal python code.

**If you stil need/want to set explicit requires**, every state return a
reference to itself once it is called, so you can simply do it this way:

```python
a = module.a("...")
module.b("...", require=[a])  # remember, requires are set in a list!
```

Namespacig, watch or more generally: refer to a state
-----------------------------------------------------

In dawdaw, every state has its name namespaced with the name of the file it is
stored in. For example, this state:
<code>git.latest("https://github.com/Psycojoker/dawdaw")</code> in the file
<code>dawdaw.sls</code> will have the name
<code>dawdaw_https://github.com/Psycojoker/dawdaw</code>. **Keep this in mind
if you want to refer to other states in non-dawdaw states.

But when you are in dawdaw you don't have to care about that: every state
returns a reference to itself once called, you can use that without caring
about how it is done and without the risk of making stupide mistake or having
to rename it everywhere. For example:

```python
a = module.a("...")
module.b("...", watch=[a])  # remember, watchs are set in a list!
```

Works for <code>watch</code>, <code>watch_in</code>, <code>require</code>,
<code>require_in</code>, <code>prereq</code>, [the other
requisites](http://docs.saltstack.com/en/latest/ref/states/requisites.html) etc
... Basically everytime you need to reference a state.

If you really need to do that by hand (don't), in reality, the reference is
just a dict, so you can do this this way (don't forget about the namespacing!):

```python
# in file example.sls

module.a("some_name")
module.b("...", watch=[{"module": "example_some_name"}])  # remember, watchs are set in a list!
```

But don't do that.

Include
-------

<code>include</code> works nearly the same than in salt. The only difference is
that you only include one state at once, not a list of states. This allows the
<code>include</code> to return a representation of included sls file to
reference states from this sls file.

In the same fashion than state, every state that follows an include will
require on it to enforce linear execution.

### Example:

```python
from dawdaw.states import include

include("some_state")
include("another_state")
```

### Reference:

An include can be use to reference a state of the included sls file (and it's
recommand to to avoid global namespaced reference) using the <code>.get</code>
method. <code>.get</code> takes 2 parameters: the module and the name.

Example:
```python
from dawdaw.states import include, pkg

some_state = include("some_state")
include("another_state")

pkg.installed("stuff", require=[some_state.get("a_module", "a_name")])
```

**If the included sls file is not a dawdaw file, you must pass the argument
<code>in_dawdaw=False</code> to include because of namespacing.**

Example:
```python
from dawdaw.states import include, pkg

some_state = include("some_state", in_dawdaw=False)

pkg.installed("stuff", watch=[some_state.get("a_module", "a_name")])
```

Pillar, grains and opts
-----------------------

All those 3 salt artifacts are accessible very easily by simply importing them
and they will behave the same way than they behave in jinja2 templates (hint:
they are dictionaries):

```python
from dawdaw import pillar, grains, opts

pillar["stuff"]
```

debug
-----

Dawdaw comes with a helper <code>debug</code> to debug what it does. This helper will simply print
on the shell the generated yaml (you'll see it in the logs or if you run salt
locally using "salt-call --local").

Usage:

```python
from dawdaw.utils import debug

debug()
```

You can pass a boolean argument to <code>debug</code> activated/desactivate debugging:

```python
from dawdaw.utils import debug

debug()

if some_stuff:
    # finally don't need to debug
    debug(False)
```

Licence
-------

Belgian Beerware.

Footnotes
---------

I've had fun writing it, hopes you'll have using it. You don't want to know how it's made.

¹: I have [another experiment](https://github.com/Psycojoker/cellar) that try
to solve this problem, but I'm not writing enough salt right now to move on
it.
