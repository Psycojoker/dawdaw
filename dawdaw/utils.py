import yaml
from .magic import global_state


def debug(value=True):
    global_state["current_state"]["debug"] = value


def salt_render(content, localtion, name, env, tmplpath, **kwargs):
    global_state["current_state"] = {
        "name": name,
        "content": {},
        "debug": False,
        "requires": [],
    }

    # YOLO
    exec(content.read())

    if global_state["current_state"]["debug"]:
        print "debug:"
        print yaml.safe_dump(global_state["current_state"]["content"], default_flow_style=False)

    return global_state["current_state"]["content"]
