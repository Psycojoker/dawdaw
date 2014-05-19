# "THE BELGIAN BEER-WARE LICENSE" (Revision 42):
# <cortex@worlddomination.be> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a belgian beer in return -- Laurent Peuch

from contextlib import contextmanager

from .magic import global_state


def debug(value=True):
    global_state["current_state"]["debug"] = value


def salt_render(content, localtion, name, env, tmplpath, salt, grains, opts, pillar, **kwargs):
    global_state["salt"] = salt
    global_state["grains"] = grains
    global_state["opts"] = opts
    global_state["pillar"] = pillar
    global_state["current_state"] = {
        "name": name,
        "content": {},
        "debug": False,
        "requires": [],
        "defaults": {},
    }

    # YOLO
    exec(content.read())

    if global_state["current_state"]["debug"]:
        import yaml
        print "debug:"
        print yaml.safe_dump(global_state["current_state"]["content"], default_flow_style=False)

    return global_state["current_state"]["content"]


@contextmanager
def default(**kwargs):
    previous_default = global_state["current_state"]["defaults"].copy()
    global_state["current_state"]["defaults"].update(kwargs)
    yield
    global_state["current_state"]["defaults"] = previous_default


def test(command, *args, **kwargs):
    return global_state["salt"]["cmd.retcode"](command, *args, **kwargs) == 0
