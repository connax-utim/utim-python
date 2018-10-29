import os

name = "utim"
__version__ = '0.1.0'


def get_root_path():
    """
    Get root path of project
    :return:
    """

    return os.path.dirname(os.path.dirname(__file__))
