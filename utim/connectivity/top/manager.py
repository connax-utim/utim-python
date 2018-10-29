import logging
import queue
import threading
from .uhost import utim_connection
from ...utilities import exceptions
from .device import utim_device
from .device.utim_device import UtimDeviceInvalidDataException
from .uhost.utim_connection import UtimConnectionInvalidDataException


class TopManagerException(Exception):
    """
    General Top Manager exception
    """

    pass


class TopManagerMethodException(TopManagerException):
    """
    Required method of object does not exist exception
    """

    pass


class TopManagerDataTypeException(TopManagerException):
    """
    Unknown data type exception
    """

    pass


class TopManagerConnectionStatus(object):
    """
    List of Top Manager statuses
    """

    # General
    NOT_INITIALIZED = -1        # Connection is not initialized
    SUCCESS = 0                 # Everything is ok
    INVALID_CONFIG = 1          # Config file does not consist required key
    INVALID_HOST = 2            # Host is not to __connection
    INVALID_CREDENTIALS = 3     # Auth error
    UNKNOWN_PLATFORM_TYPE = 4   # Unknown platform type to create connection

    # Azure
    AZURE_ERROR = 10                  # General Azure error
    AZURE_UNKNOWN_AUTH_METHOD = 11    # Unknown auth method
    AZURE_NO_CONNECTION_STRING = 12   # Can not create connection string

    # Azure
    AWS_ERROR = 20                  # General AWS error
    AWS_UNKNOWN_AUTH_METHOD = 21    # Unknown auth method
    AWS_NO_CONNECTION_STRING = 22   # Can not create connection string

    # Uhost
    UHOST_ERROR = 30                # General Uhost error
    UHOST_CONNECTION_ERROR = 31     # Connection error

    # Device
    DEVICE_ERROR = 90   # General Device error


class TopDataType(object):
    """
    List of types of data to process
    """

    DEVICE = 0
    UHOST = 1
    PLATFORM = 2

    @classmethod
    def validate(cls, data_type):
        """

        :param data_type:
        :return bool: True - if data_type is valid, False - otherwise
        """

        # Check type of input data type
        if isinstance(data_type, int):
            if data_type in [cls.DEVICE, cls.UHOST, cls.PLATFORM]:
                return True

        return False


class TopManager(object):
    """
    Top manager class
    """

    def __init__(self, manager):
        """
        Initialization

        :param TransportManager manager: Transport manager instance
        """

        logging.info("NetworkManager is starting..")

        logging.info("TransportManager checking..")
        # Check all required methods
        methods = [
            'receive',
            'send'
        ]
        for method in methods:
            if not (hasattr(manager, method) and callable(getattr(manager, method))):
                raise TopManagerMethodException

        self.__manager = manager  # TransportManager instance

        # Connections
        self.__device_connection = None
        self.__uhost_connection = None
        self.__platform_connection = None

        # Connection statuses
        self.__device_status = TopManagerConnectionStatus.NOT_INITIALIZED
        self.__uhost_status = TopManagerConnectionStatus.NOT_INITIALIZED
        self.__platform_status = TopManagerConnectionStatus.NOT_INITIALIZED

        # Run connections
        self.__run_device_connection()

        # Threads
        self.__inbound_thread = None
        self.__outbound_thread = None

        # Run event
        self.__run_event = threading.Event()

        # Queues
        self.__inbound_queue = queue.Queue()
        self.__outbound_queue = queue.Queue()

        # Run processing
        self.__run_event.set()
        logging.info("process_inbound starting..")
        self.__run_process_inbound()
        logging.info("process_outbound starting..")
        self.__run_process_outbound()

    def __run_process_inbound(self):
        """
        Run inbound data processing in another thread
        """

        self.__inbound_thread = threading.Thread(
            target=self.__process_inbound,
            name='THREAD_TOP_INBOUND_PROCESS'
        )
        self.__inbound_thread.daemon = True
        self.__inbound_thread.start()

    def __run_process_outbound(self):
        """
        Run outbound data processing in another thread
        """

        self.__outbound_thread = threading.Thread(
            target=self.__process_outbound,
            name='THREAD_TOP_OUTBOUND_PROCESS'
        )
        self.__outbound_thread.daemon = True
        self.__outbound_thread.start()

    def __process_inbound(self):
        """
        Process inbound data queue in loop
        """

        while self.__run_event.is_set():
            if (self.__device_connection and
                    self.__device_status == TopManagerConnectionStatus.SUCCESS):
                data_device = self.__device_connection.receive()
                if data_device is not None:
                    while not self.__put_data([TopDataType.DEVICE, data_device]):
                        pass

            if (self.__uhost_connection and
                    self.__uhost_status == TopManagerConnectionStatus.SUCCESS):
                data_uhost = self.__uhost_connection.receive()
                if data_uhost is not None:
                    while not self.__put_data([TopDataType.UHOST, data_uhost]):
                        pass

            if (self.__platform_connection and
                    self.__platform_status == TopManagerConnectionStatus.SUCCESS):
                data_platform = self.__platform_connection.receive()
                if data_platform is not None:
                    while not self.__put_data([TopDataType.PLATFORM, data_platform]):
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
        Process outbound data queue
        """

        while self.__run_event.is_set():
            self.__outbound_processing()

        logging.info("Stopping outbound processing..")

    def __outbound_processing(self):
        """
        TODO:Process outbound data to send  (Need return True / False ?? + act.status logging? )

        :return bytes: Data to send
        """

        try:
            data = self.__outbound_queue.get_nowait()
            data_type = data[0]
            data = data[1]
            if TopDataType.validate(data_type):
                try:
                    if (data_type == TopDataType.DEVICE and
                            self.__device_status == TopManagerConnectionStatus.SUCCESS):
                        while not self.__device_connection.send(data):
                            pass
                    elif (data_type == TopDataType.UHOST and
                          self.__uhost_status == TopManagerConnectionStatus.SUCCESS):
                        while not self.__uhost_connection.send(data):
                            pass

                    else:
                        logging.debug("TopManager has no active status connections !")

                except UtimConnectionInvalidDataException:
                    pass
                except UtimDeviceInvalidDataException:
                    pass
            else:
                logging.debug("Unknown data type - %d: %s", data_type, str(data))

        except queue.Empty:
            pass

    def __run_device_connection(self):
        """
        Run device connection in another thread
        """

        try:
            self.__device_connection = utim_device.UtimDevice(
                self.__manager.receive,
                self.__manager.send
            )
            self.__device_connection.run()

            self.__device_status = TopManagerConnectionStatus.SUCCESS

            logging.debug("Device connection works")

        except utim_device.UtimDeviceExceptionInvalidMethods:
            self.__device_status = TopManagerConnectionStatus.DEVICE_ERROR
            logging.error("Invalid transport manager methods")

    def run_uhost_connection(self, config):
        """
        Run uhost connection in another thread

        :param dict config: Config of uhost connection
        """

        try:
            # Get values
            utim_name = config['utim_name']
            protocol = config['protocol']

            # Establish connection
            self.__uhost_connection = utim_connection.UtimConnection(
                utim_name,
                protocol
            )
            self.__uhost_connection.connect()
            self.__uhost_connection.run()

            # Return result

            self.__uhost_status = TopManagerConnectionStatus.SUCCESS

        except KeyError:
            logging.error('Invalid config file: %s', config)
            self.__uhost_status = TopManagerConnectionStatus.INVALID_CONFIG

        except exceptions.UtimConnectionException:
            logging.error('Utim connection exception')
            self.__uhost_status = TopManagerConnectionStatus.UHOST_CONNECTION_ERROR

        except exceptions.UtimUnknownException:
            logging.error('Utim unknown exception')
            self.__uhost_status = TopManagerConnectionStatus.UHOST_ERROR

        return self.__uhost_status

    def send(self, data):
        """
        Send method

        :return bool: True if data is sent, False - otherwise
        :raises: TopManagerDataTypeException
        """
        data_type = data[0]
        if TopDataType.validate(data_type):
            try:
                self.__outbound_queue.put_nowait(data)
                return True

            except queue.Full:
                pass

            return False

        else:
            raise TopManagerDataTypeException()

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

    def stop(self):
        """
        Stop
        """

        if self.__device_connection:
            self.__device_connection.stop()
        if self.__uhost_connection:
            self.__uhost_connection.stop()

        if self.__run_event:
            self.__run_event.clear()

        if self.__inbound_thread:
            self.__inbound_thread.join()
        if self.__outbound_thread:
            self.__outbound_thread.join()
