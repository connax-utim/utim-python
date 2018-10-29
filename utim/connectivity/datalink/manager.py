"""
DataLink Manager
"""

import logging
import queue
import threading
from .queue import DataLinkQueue
from .uart import DataLinkUART
from .exceptions import *


class DataLinkManager(object):
    """
    DataLink Manager class
    """

    TYPE_UART = b'U'
    TYPE_QUEUE = b'Q'

    def __init__(self, mode):
        """
        Initialization
        """

        # Creating connection
        self.__current_mode = mode
        try:
            if mode == self.TYPE_QUEUE:
                self.__datalink = DataLinkQueue()
            elif mode == self.TYPE_UART:
                self.__datalink = DataLinkUART()
            else:
                raise DataLinkManagerWrongTypeException()
        except DataLinkRealisationException:
            raise DataLinkManagerInitializationException()

        # Creating queues
        self.__inbound_queue = queue.Queue()
        self.__outbound_queue = queue.Queue()

        # Threads
        self.__inbound_thread = None
        self.__outbound_thread = None

        # Run event
        self.__run_event = threading.Event()

    def connect(self, **kwargs):
        """
        Connection

        kwargs:
        for queue: rx,tx - queue
        TODO for uart: only god knows
        """
        self.__datalink.connect(**kwargs)
        self.__run_event.set()
        self.__run_process_inbound()
        self.__run_process_outbound()

    def __run_process_inbound(self):
        """
        Start in new thread
        """
        self.__inbound_thread = threading.Thread(
            target=self.__process_inbound,
            name='THREAD_DATALINK_INBOUND_PROCESS'
        )
        self.__inbound_thread.daemon = True
        self.__inbound_thread.start()

    def __run_process_outbound(self):
        """
        Start in new thread
        """
        self.__outbound_thread = threading.Thread(
            target=self.__process_outbound,
            name='THREAD_DATALINK_OUTBOUND_PROCESS'
        )
        self.__outbound_thread.daemon = True
        self.__outbound_thread.start()

    def __process_inbound(self):
        """
        Infinite cycle
        """

        while self.__run_event.is_set():
            data = self.__datalink.receive()
            if data is not None:
                while not self.__put_data(data):
                    pass

        logging.info("Stopping inbound processing..")

    def __put_data(self, data):
        """
        Put data

        :param data:
        :return bool:
        """

        try:
            self.__inbound_queue.put_nowait(data)
        except queue.Full:
            return False

        return True

    def __process_outbound(self):
        """
        Infinite cycle
        """

        while self.__run_event.is_set():
            try:
                data = self.__outbound_queue.get_nowait()
                while not self.__datalink.send(data):
                    pass

            except DataLinkRealisationWrongArgsException:
                logging.error('Somehow message {0} wasn\'t meant to be delivered'.format(data))

            except queue.Empty:
                pass

        logging.info("Stopping outbound processing..")

    def receive(self):
        """
        Get first message from queue
        """

        try:
            return self.__inbound_queue.get_nowait()

        except queue.Empty:
            pass

        return None

    def send(self, message):
        """
        Send message
        """
        if type(message) is not bytes:
            raise DataLinkManagerWrongTypeException()

        try:
            self.__outbound_queue.put_nowait(message)
        except queue.Full:
            return False

        return True

    def stop(self):
        """
        Stop
        """

        if self.__datalink:
            self.__datalink.stop()

        if self.__run_event:
            self.__run_event.clear()

        if self.__inbound_thread:
            self.__inbound_thread.join()
        if self.__outbound_thread:
            self.__outbound_thread.join()
