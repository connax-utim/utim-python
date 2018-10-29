import queue
import logging
import threading
import socket
from ..network.manager import NetworkManager, NetworkDataType


class TransportManagerException(Exception):
    """
    General Network Manager exception
    """
    pass


class TransportManagerDataTypeException():
    """
    Transport Manager DataType Exception
    """
    pass


class TransportManagerMethodException(TransportManagerException):
    """
    Required method of object does not exist exception
    """
    pass


class TransportkManagerDataTypeException(TransportManagerException):
    """
    Unknown data type exception
    """

    pass


class TransportManagerInvalidDataException(TransportManagerException):
    """
    Invalid data exception
    """

    pass
'''
class TransportManagerSocketException(er):
    """
    TODO : Socket exception
    """
    if er.errno == 98:
        # [Errno 98] Address already in use
        pass
    if er.errno == -2:
        # Errno -2] Name or service not known
        pass
    if er.errno == 99:
        # [Errno 99] Cannot assign requested address
        pass
    if er.errno == -3:
        # [Errno -3] Temporary failure in name resolution
        pass
'''


class TransportDataType(object):
    """
    List of types of data to process
    """

    DEVICE = 0
    UHOST_SOCKET = 1
    PLATFORM_SOCKET= 2

    @classmethod
    def validate(cls, data_type):
        """

        :param data_type:
        :return bool: True - if data_type is valid, False - otherwise
        """

        # Check type of input datatype
        if isinstance(data_type, int):
            if data_type in [cls.DEVICE, cls.UHOST_SOCKET, cls.PLATFORM_SOCKET]:
                return True

        return False


class TransportManager(object):
    """
    Transport manager class
    """

    def __init__(self, manager):
        """
        Initialization

        :param
        """

        logging.info("Transpor Manager is starting..")

        # Check all required methods
        methods = [
            'receive',
            'send'
        ]
        for method in methods:
            if not (hasattr(manager, method) and callable(getattr(manager, method))):
                raise TransportManagerMethodException

        self.__manager = manager  # NetworkManager instance

        # Threads
        self.__inbound_thread = None
        self.__outbound_thread = None

        # Run event
        self.__run_event = threading.Event()

        # Create queues
        self.__outbound_queue = queue.Queue()
        self.__inbound_queue = queue.Queue()

        # Run processing
        self.__run_event.set()
        logging.info("process_inbound starting..")
        self.__run_process_inbound()
        logging.info("process_outbound starting..")
        self.__run_process_outbound()

        logging.info("TransportManager is initialized!")

    def __run_process_inbound(self):
        """
        Run inbound data processing in another thread
        """

        self.__inbound_thread = threading.Thread(
            target=self.__process_inbound,
            name='THREAD_TRANSPORT_INBOUND_PROCESS'
        )
        self.__inbound_thread.daemon = True
        self.__inbound_thread.start()

    def __run_process_outbound(self):
        """
        Run outbound data processing in another thread
        """

        self.__outbound_thread = threading.Thread(
            target=self.__process_outbound,
            name='THREAD_TRANSPORT_OUTBOUND_PROCESS'
        )
        self.__outbound_thread.daemon = True
        self.__outbound_thread.start()

    def __process_inbound(self):
        """
        Process inbound data queue
        """

        while self.__run_event.is_set():
            data = self.__manager.receive(NetworkDataType.DEVICE)
            if data:
                self.__inbound_processing(data)

        logging.info("Stopping inbound processing..")

    def __process_outbound(self):
        """
        Process outbound data queue
        """

        while self.__run_event.is_set():
            data = self.__outbound_processing()
            if data:
                while not self.__manager.send(data[0], data[1]):
                    pass

        logging.info("Stopping outbound processing..")

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
                    data = data[3:3 + length]
                    if TransportDataType.validate(tag) is True:
                        while not self.__put_data(data):
                            pass
                    else:
                        logging.debug("Unknown data type - %d: %s", tag, str(data))

                else:
                    logging.debug("Invalid data length - %d: %s", data_length, str(data))

            else:
                logging.error("Invalid data type: %s", str(data))

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

    def __outbound_processing(self):
        """
        Process outbound data to send
        :return bytes: Data to send
        """

        try:
            data = self.__outbound_queue.get_nowait()
            destination = data[0]
            body = data[1]
            # Assemble packet
            dest = destination.to_bytes(1, byteorder='big')
            length = len(body).to_bytes(2 , byteorder='big')
            packet = dest + length + body

            tag = None
            if destination == TransportDataType.DEVICE:
                tag = NetworkDataType.DEVICE
            elif destination == TransportDataType.UHOST_SOCKET:
                tag = NetworkDataType.UHOST
            elif destination == TransportDataType.PLATFORM_SOCKET:
                tag = NetworkDataType.PLATFORM

            if tag is not None:
                return [tag, packet]

        except queue.Empty:
            pass

        return None

    def server_socket_state(self,address, port, TransportDataType):
        """
        TODO: Server_socket_state - dict
        :param address:
        :param port:
        :param TransportDataType:
        :return: server_socket_running state (False or True)
        """
        server_socket_state_dict={'address':address,'port':port,'TransportDataType':TransportDataType}


    def create_socket_server(self, address, port,TransportDataType):
        """
        TODO: Start new socket server
        :param bytes hostname or ip address
        :param port must be 0-65535
        """
        buffer_size = 64 # socket buffer , max size is 4096
        max_socket_connections=1

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((address, port))
            self.server_socket.listen(max_socket_connections)

        except Exception as er:
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()

            logging.error(er)
            raise TransportManagerMethodException(er)

        except socket.error as er:  # Some methods for socket.error Exception
            self.server_socket.shutdown(socket.SHUT_RDWR)
            self.server_socket.close()
            logging.error(er)
            # raise  TransportManagerSocketException(er)

    def socket_send(self,address, port, data):
        """
        TODO: Start new socket_send client connection
        :param bytes hostname or ip address
        :param port must be 0-65535
        :param bytes data
        """
        try:
            client_socket = socket.socket()
            client_socket.connect((address, port))
            if isinstance(data, bytes):
                client_socket.send(data)


        except Exception as er:
            logging.error(er)
            raise TransportManagerMethodException(er)

        except socket.error as er:  # Some methods for socket.error Exception
            logging.error(er)
            print(er.errno)
            #raise  TransportManagerSocketException(er)

    def socket_receive(self,address, port):
        """
        TODO: Start new socket_receive client connection
        :param bytes hostname or ip address
        :param port must be 0-65535
        :param bytes data
        """
        try:
            client_socket = socket.socket()
            client_socket.connect((address, port))

            while True:
                connection, address = client_socket.accept()
                # buf = connection.recv(buffer_size)
                # if len(buf) > 0:
                #     print(buf)
                #     if TransportDataType == TransportDataType.UHOST_SOCKET:
                #         pass
                #     elif TransportDataType == TransportDataType.UHOST_SOCKET:
                #         pass



        except Exception as er:
            logging.error(er)
            raise TransportManagerMethodException(er)

        except socket.error as er:  # Some methods for socket.error Exception
            logging.error(er)
            print(er.errno)
            #raise  TransportManagerSocketException(er)

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
        :raises: TransportManagerDataTypeException
        """
        if isinstance(data, bytes):
            try:
                self.__outbound_queue.put_nowait([TransportDataType.DEVICE, data])
                return True
            except queue.Full:
                pass

            return False

        else:
            raise TransportManagerInvalidDataException()

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
