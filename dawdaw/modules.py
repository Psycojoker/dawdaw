# "THE BELGIAN BEER-WARE LICENSE" (Revision 42):
# <cortex@worlddomination.be> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a belgian beer in return -- Laurent Peuch

import sys
from types import ModuleType

from .magic import global_state


class ModuleWrapper(object):
    def __init__(self, name):
        self.name = name
        self.functions = {}

    def __getattr__(self, key):
        return self.functions.setdefault(key, FunctionWrapper(function_name=key, module_name=self.name))


class FunctionWrapper(object):
    def __init__(self, function_name, module_name):
        self.name = function_name
        self.module_name = module_name

    def __call__(self, *args, **kwargs):
        return global_state["salt"]["%s.%s" % (self.module_name, self.name)](*args, **kwargs)


# black magic area, wrap salt module functions on import
class SaltModuleWrapperBuilder(dict):
    def __init__(self, globals, baked_args={}):
        self.globals = globals
        self.baked_args = baked_args

    def __getitem__(self, key):
        if key in self.globals:
            return self.globals[key]

        if key in set([x.split(".")[0] for x in global_state["salt"]]):
            module = ModuleWrapper(key)
            self.globals[key] = module
            return module

        raise ImportError("cannot import name %s" % key)

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
        self._env = SaltModuleWrapperBuilder(globals(), baked_args)

    def __getattr__(self, name):
        return self._env[name]

    def __setattr__(self, name, value):
        if hasattr(self, "_env"):
            self._env[name] = value
        ModuleType.__setattr__(self, name, value)


self = sys.modules[__name__]
sys.modules[__name__] = BlackMagicImportHook(self)
