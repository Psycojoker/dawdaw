from dawdaw.utils import salt_render


def render(*args, **kwargs):
    return salt_render(salt=__salt__, grains=__grains__, opts=__opts__, pillar=__pillar__, *args, **kwargs)
