"""
Utim device module
"""

import threading
import logging
import queue


class UtimDeviceException(Exception):
    """
    Utim device exception
    """

    pass


class UtimDeviceExceptionInvalidMethods(UtimDeviceException):
    """
    Invalid method exception
    """

    pass


class UtimDeviceInvalidDataException(UtimDeviceException):
    """
    Invalid data exception
    """

    pass


class UtimDevice(object):
    """
    Utim device class
    """

    def __init__(self, transport_receive, transport_send):
        """
        Initialize device

        :param transport_receive: Receive method
        :param transport_send: Send method
        """

        if not callable(transport_receive) or not callable(transport_send):
            raise UtimDeviceExceptionInvalidMethods()

        self.__t_receive = transport_receive
        self.__t_send = transport_send

        self.__running = True

        # Queues
        self.__inbound_queue = queue.Queue()
        self.__outbound_queue = queue.Queue()

        # Threads
        self.__inbound_thread= None
        self.__outbound_thread = None

        # Run event
        self.__run_event = threading.Event()

    def run(self):
        """
        Run data processing
        """

        self.__run_event.set()

        self.__run_inbound_process()
        self.__run_outbound_process()

    def __run_inbound_process(self):
        """
        Run inbound process
        """

        logging.info("Try to run inbound process in another thread")
        self.__inbound_thread = threading.Thread(
            target=self.__inbound_process,
            name='THREAD_UTIM_DEVICE_INBOUND_PROCESS'
        )
        self.__inbound_thread.daemon = True
        self.__inbound_thread.start()

    def __run_outbound_process(self):
        """
        Run outbound process
        """

        logging.info("Try to run outbound process in another thread")
        self.__outbound_thread = threading.Thread(
            target=self.__outbound_process,
            name='THREAD_UTIM_DEVICE_OUTBOUND_PROCESS'
        )
        self.__outbound_thread.daemon = True
        self.__outbound_thread.start()

    def __inbound_process(self):
        """
        Inbound process
        """

        while self.__run_event.is_set():
            data = self.__t_receive()
            if data:
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

    def __outbound_process(self):
        """
        Outbound process
        """

        while self.__run_event.is_set():
            try:
                data = self.__outbound_queue.get_nowait()
                if data:
                    self.__t_send(data)

            except queue.Empty:
                pass

        logging.info("Stopping outbound processing..")

    def stop(self):
        """
        Stop running
        """

        if self.__run_event:
            self.__run_event.clear()

        if self.__inbound_thread:
            self.__inbound_thread.join()
        if self.__outbound_thread:
            self.__outbound_thread.join()

    def receive(self):
        """
        Receive method

        :return bytes|None: Data
        """

        try:
            return self.__inbound_queue.get_nowait()

        except queue.Empty:
            pass

        return None

    def send(self, data):
        """
        Send method

        :param bytes data: data
        :return bool: True if data is sent, False - otherwise
        :raises: UtimDeviceInvalidDataException
        """

        if isinstance(data, bytes):
            try:
                self.__outbound_queue.put_nowait(data)
                return True

            except queue.Full:
                pass

            return False

        else:
            raise UtimDeviceInvalidDataException()
