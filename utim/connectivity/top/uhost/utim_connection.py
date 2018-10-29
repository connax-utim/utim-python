"""
Utim Connection module

This module implements Utim connection and messaging through the MQTT or AMQP
"""

import time
import logging
import queue
import threading
from ....utilities import connmanager, config


class UtimConnectionException(Exception):
    """
    Exception of UtimConnection
    """

    pass


class UtimConnectionInvalidDataException(UtimConnectionException):
    """
    UtimConnection invalid data exception
    """

    pass


class UtimConnection(object):
    """
    MQTT class
    """

    def __init__(self, name, type):
        """
        Initialize MQTT connection
        """

        self.__inbound_queue = queue.Queue()  # Queue for inbound data
        self.__outbound_queue = queue.Queue()  # Queue for outbound data
        self.__utim_name = name
        self.__type = type
        self.__client = None

        # Threads
        self.__run2_thread = None

        # Run event
        self.__run_event = threading.Event()

        self.__config = config.Config()

    def connect(self):
        """
        Establish connection
        :return:
        """

        self.__client = connmanager.ConnManager(self.__type)

    def stop(self):
        """
        Stop
        """

        if self.__client:
            self.__client.disconnect()

        if self.__run_event:
            self.__run_event.clear()

        if self.__run2_thread:
            self.__run2_thread.join()

    def run(self):
        """
        Run subscribe and publish to MQTT-broker
        """

        logging.info("Try to run in another thread")
        self.__run_event.set()

        self.__run2_thread = threading.Thread(
            target=self.__run2,
            name='THREAD_UTIM_CONNECTION_RUN'
        )
        self.__run2_thread.daemon = True
        self.__run2_thread.start()

    def __run2(self):
        """
        Run listening and writing to Serial port
        Use it in another thread.
        """

        # Subscribe to topic
        self.__client.subscribe(self.__utim_name, self, self._on_message)
        logging.debug("Subscribed to topic: %s", self.__utim_name)

        logging.info("Start Running")
        while self.__run_event.is_set():
            self.__publish()
            time.sleep(1)

        logging.info("Stopping processing..")

    def __publish(self):
        """
        Publish
        """

        while not self.__outbound_queue.empty():
            try:
                message = self.__outbound_queue.get_nowait()
                logging.debug("Publish item: %s", message)

                destination = bytes.fromhex(self.__config.uhost_name)
                logging.debug("Message: %s", message)
                logging.debug("Type message: %s", type(message))
                self.__client.publish(self.__utim_name.encode(), destination.decode(), message)
                logging.debug("Message %s was published to %s", str(destination), str(message))

            except queue.Empty:
                pass

    def _on_message(self, conn, sender, message):
        """
        Message receiving callback

        :param sender: Message sender
        :param message: The message

        Author: kanphis@gmail.com
        Created: 16.08.2017
        Edited: 16.08.2017
        """
        logging.info("Received message {0} from {1}".format(message, sender))
        while not self.__put_data(message):
            pass

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

    def receive(self):
        """
        Receive method

        :param TopDataType data_type: Top data type
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

        :param bytes data: Data to send
        :return bool: True if data is sent, False - otherwise
        :raise: UtimConnectionInvalidDataException
        """

        if isinstance(data, bytes):
            try:
                self.__outbound_queue.put_nowait(data)
                return True

            except queue.Full:
                pass

            return False

        else:
            raise UtimConnectionInvalidDataException()
