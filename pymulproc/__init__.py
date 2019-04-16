VERSION = (0, 1, 1)


def get_version():
    """Return the VERSION as a string, e.g. for VERSION == (0, 1, 0),
    return '0.1.0'.
    """
    return '.'.join(map(str, VERSION))


__version__ = get_version()
