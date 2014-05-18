from .magic import global_state


class LazyAccess(object):
    def __init__(self, name):
        self.name = name

    def __dict__(self, *args, **kwargs):
        global_state[self.name].__dict__(*args, **kwargs)

    def __repr__(self):
        return global_state[self.name].__repr__()


grains = LazyAccess("grains")
pillar = LazyAccess("pillar")
opts = LazyAccess("opts")
