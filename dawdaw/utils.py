from .magic import global_state


def salt_render(content, localtion, name, env, tmplpath, **kwargs):
    global_state["current_state"] = {
        "name": name,
        "content": {},
    }

    # YOLO
    exec(content.read())

    return global_state["current_state"]["content"]
