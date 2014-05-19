# "THE BELGIAN BEER-WARE LICENSE" (Revision 42):
# <cortex@worlddomination.be> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a belgian beer in return -- Laurent Peuch

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
