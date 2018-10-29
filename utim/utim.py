"""
Utim main module

The purpose is to provide getters and setters methods to the UTIM object private variables
which are the only stateful items in project.

Functionally this class does the following:
    - initializes the serial_exchanger - the object which does the lowest level processing of the
    communication via Serial.
    This object also provides three thread-safe queues - the only way to communicate with SLS via
    Serial.
    The serial_exchanger routes messages incoming from Serial into one of the inbound queues
    depending on the originator: Uhost- and SLS-originated messages are routed to separate queues to
    be processed separately.

    - initializes the uhost_process - the object which process all commands arriving from Uhost
    by pulling single command from the Uhost queue

    - initializes thr sls_process - the object which processes all commands arriving from SLS
    by pulling single command from the SLS queue

    - Finally spawns serial_exchanger, uhost_process, and sls_process to run in the separate threads
    in cycles.

"""

import threading
import logging
import queue
import os
from .utilities import srp
from .connectivity import manager as conn_manager
from .utilities.exceptions import UtimConnectionException, UtimInitializationError
from .connectivity import TopManagerConnectionStatus
from .connectivity import TopDataType
from .utilities.address import Address
from .utilities.data_indexes import ProcessorIndex
from .utilities import process_item
from .utilities import config


class Utim(object):
    """
    Utim class
    """

    def __init__(self):
        """
        Initialization
        """

        try:
            self.__item_process = None

            self.__config = config.Config()

            # Uhost protocol
            self.__uhost_protocol = self.__config.utim_messaging_protocol.lower()

            # Session key and SLS name of this session
            self.__session_key = None

            # SRP client
            self.__srp_client = None
            # Utim SRP auth step
            self.__srp_step = None
            self.__step_iterations = 10

            # SLS id
            self.__sls_id = None

            # Process platform connection
            self.__platform_connection = None
            self.__platform_process = None
            self.__platform_config = None

            # Process device
            self.__device_process = None

            # Test data
            self.__test_data = None

            # Threads
            self.__inbound_thread = None
            self.__outbound_thread = None

            # Run event
            self.__run_event = threading.Event()

            # Queues
            self.__inbound_queue = queue.Queue()
            self.__outbound_queue = queue.Queue()

            # Name
            self.__utim_name = self.__config.utim_name.upper()

            # Connectivity
            self.__connection = None
            self.__uhost_status = None
            self.__platform_status = None

            # Check master key
            self.__get_master_key()

            # Process Items
            self.__item_process = process_item.ProcessItem(
                self,
                self.__inbound_queue,
                self.__outbound_queue
            )

        except UtimInitializationError:
            raise UtimInitializationError

        except Exception as er:
            logging.error("utim_init_Exception")
            logging.error(er)
            self.stop()

    def connect(self, **kwargs):
        """
        Run connectivity manager

        :param dl_type: DataLink manager connection type
        :param tx: Queue to transmit data
        :param rx: Queue to receive data

        :raise: UtimConnectionException
        """

        self.__connection = conn_manager.ConnectivityManager()

        # Device (another app) connection
        self.__connection.connect(**kwargs)

        # Uhost connection
        self.__uhost_status = self.__connection.run_uhost_connection({
            'utim_name': self.__utim_name,
            'protocol': self.__uhost_protocol
        })

        logging.info("UHOST CONNECTION STATUS: %s", self.__uhost_status)
        if self.__uhost_status != TopManagerConnectionStatus.SUCCESS:
            logging.error("Connection to Uhost could not be established with protocol %s!",
                          self.__uhost_protocol)
            raise UtimConnectionException()

        # Run connectivity processes
        self.__run_event.set()

        self.__inbound_thread = threading.Thread(
            target=self.__inbound_process,
            name='THREAD_UTIM_INBOUND_PROCESS'
        )
        self.__inbound_thread.daemon = True
        self.__inbound_thread.start()

        self.__outbound_thread = threading.Thread(
            target=self.__outbound_process,
            name='THREAD_UTIM_OUTBOUND_PROCESS'
        )
        self.__outbound_thread.daemon = True
        self.__outbound_thread.start()

    def run_platform_connection(self):
        """
        Run platform connection

        :return : Connection status
        """

        self.__platform_status = self.__connection.run_platform_connection(self.__platform_config)

        return self.__platform_status

    def __inbound_process(self):
        """
        Inbound process
        """

        while self.__run_event.is_set():
            if self.__connection:
                data = self.__connection.receive()
                # print("Inbound ", data)
                if data:
                    tag = data[ProcessorIndex.address.value]
                    body = data[ProcessorIndex.body.value]
                    # print("Inbound tag", tag)
                    # print("Inbound body", body)
                    if tag == TopDataType.DEVICE:
                        while not self.__put_data([Address.ADDRESS_DEVICE, body]):
                            pass
                    elif tag == TopDataType.UHOST:
                        while not self.__put_data([Address.ADDRESS_UHOST, body]):
                            pass
                    elif tag == TopDataType.PLATFORM:
                        while not self.__put_data([Address.ADDRESS_PLATFORM, body]):
                            pass
                    else:
                        logging.debug("Unknown inbound tag: %s - %s", tag, body)

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
            if self.__connection:
                try:
                    data = self.__outbound_queue.get_nowait()
                    if data:
                        tag = data[ProcessorIndex.address.value]
                        body = data[ProcessorIndex.body.value]
                        # print("Outbound tag", tag)
                        # print("Outbound body", body)
                        if tag == Address.ADDRESS_DEVICE:
                            # print("TO_DEVICE")
                            self.__connection.send([TopDataType.DEVICE, body])
                        elif tag == Address.ADDRESS_UHOST:
                            self.__connection.send([TopDataType.UHOST, body])
                        elif tag == Address.ADDRESS_PLATFORM:
                            self.__connection.send([TopDataType.PLATFORM, body])
                        else:
                            logging.debug("Unknown outbound tag: %s - %s", tag, body)
                except queue.Empty:
                    pass

    def set_platform_config(self, config_string):
        """
        Set platform id
        """
        try:
            self.__platform_config = dict(config_string)
        except ValueError:
            logging.error('Error setting platform config')

    def get_platform_config(self):
        """
        Get platform id
        """
        return self.__platform_config

    def get_srp_step(self):
        """
        Get SRP step
        """

        return self.__srp_step

    def set_srp_step(self, step):
        """
        Set SRP step
        """

        self.__srp_step = step

    def get_srp_iterations(self):
        """
        Get SRP iterations
        """

        return self.__step_iterations

    def set_srp_iterations(self, iteration):
        """
        Set SRP iterations
        """

        self.__step_iterations = iteration

    @staticmethod
    def __get_master_key():
        """
        Get master key
        """

        try:
            key = os.environ.get('UTIM_MASTER_KEY', None)
            return bytes.fromhex(key)

        except TypeError as ex:
            logging.debug(ex)
            raise UtimInitializationError

    def get_session_key(self):
        """
        Get session key
        """

        return self.__session_key

    def set_session_key(self, key):
        """
        Set session key
        """

        self.__session_key = key

    def get_srp_client(self):
        """
        Get SRP client
        """

        logging.debug("Check sls id is not None")
        if self.__srp_client is None:
            logging.debug("Create new SRP User")
            username = bytes.fromhex(self.__utim_name)
            password = self.__get_master_key()
            logging.debug("Username: %s", username)
            logging.debug("Username: %s", [x for x in username])
            logging.debug("Password: %s", [x for x in password])
            self.__srp_client = srp.User(username, password)

        logging.debug("SRP client type: %s", type(self.__srp_client))
        if self.__srp_client is not None:
            logging.debug("A: %s", str(self.__srp_client.A))

        return self.__srp_client

    def run(self):
        """
        Run Utim
        """

        self.__item_process.run()

    def stop(self):
        """
        Stop Utim
        """

        # Stop item processing
        if self.__item_process:
            self.__item_process.stop()

        # Stop connection
        if self.__connection:
            self.__connection.stop()

        if self.__run_event:
            self.__run_event.clear()

        if self.__inbound_thread:
            self.__inbound_thread.join()
        if self.__outbound_thread:
            self.__outbound_thread.join()

        logging.debug("Utim was stopped !!")

    def utim_die(self):
        """
        Kill UTIM
        """

        self.stop()
