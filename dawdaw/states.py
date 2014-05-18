import sys
from types import ModuleType

from .magic import current_state


class StateWrapper(object):
    def __init__(self, state, name):
        self.state = state
        self.name = name
        self.functions = {}

    def __getattr__(self, key):
        return self.functions.setdefault(key, FunctionWrapper(getattr(self.state, key), function_name=key, module_name=self.name))


class FunctionWrapper(object):
    def __init__(self, function, function_name, module_name):
        self.function = function
        self.name = function_name
        self.module_name = module_name

    def __call__(self, name, *args, **kwargs):
        current_state["current_state"]["content"][name] = {
            "%s.%s" % (self.module_name, self.name): self.dict_to_salt_lame_list(kwargs)
        }
        print current_state

    def dict_to_salt_lame_list(self, the_dict):
        to_return = []
        for item in the_dict.items():
            # so lame conversion
            to_return.append({x: y for x, y in [item]})
        return to_return


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
