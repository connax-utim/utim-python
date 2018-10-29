"""
Queue realisation of DataLink layer
"""

import queue
from .exceptions import *


class DataLinkQueue(object):
    """
    DalaLink queue class
    """

    def __init__(self):
        """
        Initialize DataLinkQueue
        """
        self.__tx = None
        self.__rx = None

    def connect(self, **kwargs):
        """
        Connect to queues!
        :param kwargs: tx - transmitting queue, rx - receiving queue
        """
        if 'tx' not in kwargs.keys() or 'rx' not in kwargs.keys():
            raise DataLinkRealisationWrongArgsException()
        if not isinstance(kwargs['tx'], queue.Queue) or not isinstance(kwargs['rx'], queue.Queue):
            raise DataLinkRealisationWrongArgsException()
        self.__tx = kwargs['tx']
        self.__rx = kwargs['rx']

    def receive(self):
        """
        Get first message from queue
        """
        if self.__rx is None:
            raise DataLinkRealisationConnectionException()

        try:
            return self.__rx.get_nowait()

        except queue.Empty:
            pass

        return None

    def send(self, message):
        """
        Send message
        """
        if type(message) is not bytes:
            raise DataLinkRealisationWrongArgsException()
        if self.__tx is None:
            raise DataLinkRealisationConnectionException()

        try:
            self.__tx.put_nowait(message)

        except queue.Full:
            return False

        return True

    def stop(self):
        """
        Stop
        """

        pass
