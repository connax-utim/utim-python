import logging
import queue
import threading


class NetworkManagerException(Exception):
    """
    General Network Manager exception
    """

    pass


class NetworkManagerMethodException(NetworkManagerException):
    """
    Required method of object does not exist exception
    """

    pass


class NetworkManagerDataTypeException(NetworkManagerException):
    """
    Unknown data type exception
    """

    pass


class NetworkManagerInvalidDataException(NetworkManagerException):
    """
    Invalid data exception
    """

    pass


class NetworkDataType(object):
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


class NetworkManager(object):
    """
    Network manager class
    """

    def __init__(self, manager):
        """
        Initialization

        :param DataLinkManager manager: Data link manager instance
        """

        logging.info("NetworkManager is starting..")

        logging.info("DataLinkManager checking..")
        # Check all required methods
        methods = [
            'receive',
            'send'
        ]
        for method in methods:
            if not (hasattr(manager, method) and callable(getattr(manager, method))):
                raise NetworkManagerMethodException

        self.__manager = manager    # DataLinkManager instance

        # Threads
        self.__inbound_thread = None
        self.__outbound_thread = None

        # Run event
        self.__run_event = threading.Event()

        # Create queues
        self.__outbound_queue = queue.Queue()
        self.__device_queue = queue.Queue()
        self.__uhost_queue = queue.Queue()
        self.__platform_queue = queue.Queue()

        # Run processing
        self.__run_event.set()
        logging.info("process_inbound starting..")
        self.__run_process_inbound()
        logging.info("process_outbound starting..")
        self.__run_process_outbound()

        logging.info("NetworkManager is initialized!")

    def __run_process_inbound(self):
        """
        Run inbound data processing in another thread
        """

        self.__inbound_thread = threading.Thread(
            target=self.__process_inbound,
            name='THREAD_NETWORK_INBOUND_PROCESS'
        )
        self.__inbound_thread.daemon = True
        self.__inbound_thread.start()

    def __run_process_outbound(self):
        """
        Run outbound data processing in another thread
        """

        self.__outbound_thread = threading.Thread(
            target=self.__process_outbound,
            name='THREAD_NETWORK_OUTBOUND_PROCESS'
        )
        self.__outbound_thread.daemon = True
        self.__outbound_thread.start()

    def __process_inbound(self):
        """
        Process inbound data queue in loop
        """

        while self.__run_event.is_set():
            data = self.__manager.receive()
            self.__inbound_processing(data)

        logging.info("Stopping inbound processing..")

    def __inbound_processing(self, data):
        """
        Process received inbound data

        :param bytes data: Data to process
        """

        if data is not None:
            # Data must be bytes type
            if isinstance(data, bytes):
                # Data must be 3 bytes at a minimum
                data_length = len(data)
                if data_length >= 3:
                    tag_bytes = data[0:1]
                    tag = int.from_bytes(tag_bytes, byteorder='big', signed=False)
                    length_bytes = data[1:3]
                    length = int.from_bytes(length_bytes, byteorder='big', signed=False)
                    data = data[3:3+length]

                    if tag == NetworkDataType.DEVICE:
                        while not self.__put_data(self.__device_queue, data):
                            pass

                    elif tag == NetworkDataType.UHOST:
                        while not self.__put_data(self.__uhost_queue, data):
                            pass

                    elif tag == NetworkDataType.PLATFORM:
                        while not self.__put_data(self.__platform_queue, data):
                            pass

                    else:
                        logging.debug("Unknown data type - %d: %s", tag, str(data))
                else:
                    logging.debug("Invalid data length - %d: %s", data_length, str(data))

            else:
                logging.error("Invalid data type: %s", str(data))

    def __put_data(self, type_queue, data):
        """
        Put data

        :param Queue type_queue: Queue
        :param data:
        :return bool:
        """

        try:
            type_queue.put_nowait(data)
        except queue.Full:
            return False

        return True

    def __process_outbound(self):
        """
        Process outbound data queue
        """

        while self.__run_event.is_set():
            data = self.__outbound_processing()
            if data:
                while not self.__manager.send(data):
                    pass

        logging.info("Stopping outbound processing..")

    def __outbound_processing(self):
        """
        Process outbound data to send

        :return bytes: Data to send
        """

        try:
            data = self.__outbound_queue.get_nowait()
            length = len(data[1]).to_bytes(2, byteorder='big')
            destination = data[0].to_bytes(1, byteorder='big')
            packet = destination + length + data[1]
            return packet

        except queue.Empty:
            pass

        return None

    def receive(self, data_type):
        """
        Receive method

        :param NetworkDataType data_type: Network data type
        :return bytes|None: Data
        :raises: NetworkManagerDataTypeException
        """

        if NetworkDataType.validate(data_type):
            try:
                if data_type is NetworkDataType.DEVICE:
                    return self.__device_queue.get_nowait()

                elif data_type is NetworkDataType.UHOST:
                    return self.__uhost_queue.get_nowait()

                elif data_type is NetworkDataType.PLATFORM:
                    return self.__platform_queue.get_nowait()
            except queue.Empty:
                pass

            return None

        else:
            raise NetworkManagerDataTypeException()

    def send(self, destination, data):
        """
        Send method

        :param NetworkDataType destination: Network data type
        :param bytes data: data
        :return bool: True if data is sent, False - otherwise
        :raises: NetworkManagerDataTypeException
        """

        if NetworkDataType.validate(destination):
            if isinstance(data, bytes):
                try:
                    self.__outbound_queue.put_nowait([destination, data])
                    return True

                except queue.Full:
                    pass

                return False

            else:
                raise NetworkManagerInvalidDataException()

        else:
            raise NetworkManagerDataTypeException()

    def stop(self):
        """
        Stop
        """

        if self.__run_event:
            self.__run_event.clear()

        if self.__inbound_thread:
            self.__inbound_thread.join()
        if self.__outbound_thread:
            self.__outbound_thread.join()
