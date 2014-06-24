# "THE BELGIAN BEER-WARE LICENSE" (Revision 42):
# <cortex@worlddomination.be> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a belgian beer in return -- Laurent Peuch

import sys
import inspect
from types import ModuleType

from .magic import global_state


salt_states = __import__("salt").states


def include(name, in_dawdaw=True):
    global_state["current_state"]["requires"].append({"sls": name})
    global_state["current_state"]["content"].setdefault("include", []).append(name)
    return IncludedModule(name, in_dawdaw=in_dawdaw)


class IncludedModule(object):
    def __init__(self, name, in_dawdaw):
        self.name = name
        self.in_dawdaw = in_dawdaw

    def get(self, module, name):
        if self.in_dawdaw:
            return {module: "%s_%s" % (self.name, name)}
        else:
            return {module: name}


class StateWrapper(object):
    def __init__(self, state, name):
        self.state = state
        self.name = name
        self.functions = {}

        original_salt_state = getattr(salt_states, name)
        if hasattr(original_salt_state, "__virtualname__"):
            self.name = original_salt_state.__virtualname__

    def __getattr__(self, key):
        return self.functions.setdefault(key, FunctionWrapper(getattr(self.state, key), function_name=key, module_name=self.name))


class FunctionWrapper(object):
    def __init__(self, function, function_name, module_name):
        self.function = function
        self.name = function_name
        self.module_name = module_name

    def __call__(self, name, *args, **kwargs):
        name, content, module = self.generate_state(name, *args, **kwargs)
        global_state["current_state"]["content"][name] = content

        reference = {self.module_name: name}

        global_state["current_state"]["requires"].append(reference)

        # this way, you can reuse this in watch clauses
        return reference

    def generate_state(self, name, *args, **kwargs):
        module = "%s.%s" % (self.module_name, self.name)

        values = self.dict_to_salt_lame_list(kwargs)
        values = self.set_requires(values)
        values = self.set_defaults(values)
        values = [{"name": name}] + values

        return "%s_%s" % (global_state["current_state"]["name"], "%s_%s" % (self.module_name, name)), {
            module: values,
        }, module

    def set_requires(self, state_content):
        if not global_state["current_state"]["requires"]:
            return state_content

        existing_require = filter(lambda x: x.keys()[0] == "require", state_content)
        requires = global_state["current_state"]["requires"]
        if not existing_require:
            state_content.append({
                "require": [x.copy() for x in requires],
            })
        else:
            current_requires = existing_require[0].values()[0]
            current_requires.extend([x.copy() for x in requires if x not in current_requires])

        return state_content

    def dict_to_salt_lame_list(self, the_dict):
        to_return = []
        for item in the_dict.items():
            # so lame conversion
            to_return.append({x: y for x, y in [item]})
        return to_return

    def set_defaults(self, values):
        args = inspect.getargspec(self.function).args

        for default in global_state["current_state"]["defaults"]:
            if default in args and default not in [x.keys()[0] for x in values]:
                values.append({default: global_state["current_state"]["defaults"][default]})
        return values


# black magic area, wrap salt state functions on import
class SaltStateWrapperBuilder(dict):
    def __init__(self, globals, baked_args={}):
        self.globals = globals
        self.baked_args = baked_args

    def __getitem__(self, key):
        if key in self.globals:
            return self.globals[key]

        if self.module_exists("salt.states.%s" % key):
            state = StateWrapper(self.get_module("salt.states.%s" % key), name=key)
            self.globals[key] = state
            return state

        raise ImportError("cannot import name %s" % key)

    def module_exists(self, module_name):
        try:
            __import__(module_name)
        except ImportError:
            return False
        else:
            return True

    def get_module(self, path):
        module = __import__(path)
        for i in path.split(".")[1:]:
            module = getattr(module, i)
        return module

class BlackMagicImportHook(ModuleType):
    def __init__(self, self_module, baked_args={}):
        # this code is directly inspired by amoffat/sh
        # see https://github.com/amoffat/sh/blob/80af5726d8aa42017ced548abbd39b489068922a/sh.py#L1695
        for attr in ["__builtins__", "__doc__", "__name__", "__package__"]:
            setattr(self, attr, getattr(self_module, attr))

        # python 3.2 (2.7 and 3.3 work fine) breaks on osx (not ubuntu)
        # if we set this to None. and 3.3 needs a value for __path__
        self.__path__ = []
        self.self_module = self_module
        self._env = SaltStateWrapperBuilder(globals(), baked_args)

    def __getattr__(self, name):
        return self._env[name]

    def __setattr__(self, name, value):
        if hasattr(self, "_env"):
            self._env[name] = value
        ModuleType.__setattr__(self, name, value)


self = sys.modules[__name__]
sys.modules[__name__] = BlackMagicImportHook(self)
