"""
Subprocessor for platform messages
"""

from ..utilities.tag import Tag
from ..utilities.address import Address
from ..utilities.status import Status


class ProcessPlatform(object):
    """
    Subprocessor for platform messages
    """

    def __init__(self, utim):
        """
        Initialization of subprocessor for platform messages
        """

    def process(self, data):
        """
        Process platform message
        :param data: array [source, destination, status
        :return: same as input
        """
