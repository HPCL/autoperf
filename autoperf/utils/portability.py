import os


def fix_path(inp:str):
    """
    Make hard-coded Unix paths more portable (Windows-friendly)

    :param inp: The string with hard-coded Unix path, e.g., "some/path"
    :return: OS-appropriate path
    """
    parts = inp.split('/')
    return os.path.sep.join(parts)