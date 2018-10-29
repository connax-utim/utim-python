import logging
from .datalink import manager as dl_manager, exceptions as dl_exceptions
from .network import manager as net_manager
from .transport import manager as tr_manager
from .top import manager as top_manager


class ConnectivityException(Exception):
    """
    General connectivity exception
    """

    pass


class ConnectivityWrongArgsException(ConnectivityException):
    """
    Wrong arguments
    """

    pass


class ConnectivityConnectError(ConnectivityException):
    """
    Connection error
    """

    pass


class ConnectivityManager(object):
    """
    Connectivity manager class
    """

    def __init__(self):
        """
        Initialization
        """

        self.__datalink_manager = None
        self.__network_manager = None
        self.__transport_manager = None
        self.__top_manager = None

    def connect(self, **kwargs):
        """

        :param dl_type: DataLink manager connection type
        :param tx: Queue to transmit data
        :param rx: Queue to receive data
        :return:
        """

        try:
            # Init DataLinkManager
            if 'dl_type' not in kwargs.keys():
                raise ConnectivityWrongArgsException()
            if kwargs['dl_type'] not in (dl_manager.DataLinkManager.TYPE_QUEUE,
                                         dl_manager.DataLinkManager.TYPE_UART):
                raise ConnectivityWrongArgsException()

            self.__datalink_manager = dl_manager.DataLinkManager(
                dl_manager.DataLinkManager.TYPE_QUEUE
            )
            self.__datalink_manager.connect(**kwargs)

            # Init NetworkManager
            self.__network_manager = net_manager.NetworkManager(self.__datalink_manager)

            # Init TransportManager
            self.__transport_manager = tr_manager.TransportManager(self.__network_manager)

            # Init TopManager
            self.__top_manager = top_manager.TopManager(self.__transport_manager)

        except (dl_exceptions.DataLinkRealisationWrongArgsException,
                dl_exceptions.DataLinkRealisationException) as ex:
            logging.error("Cannot create DataLink manager: %s", ex)
            raise ConnectivityConnectError()

        except net_manager.NetworkManagerMethodException as ex:
            logging.error("Cannot create Network manager: %s", ex)
            raise ConnectivityConnectError()

        except tr_manager.TransportManagerMethodException as ex:
            logging.error("Cannot create Transport manager: %s", ex)
            raise ConnectivityConnectError()

        except top_manager.TopManagerMethodException as ex:
            logging.error("Cannot create Top manager: %s", ex)
            raise ConnectivityConnectError()

    def send(self, data):
        """
        Send method

        :param data: Data to send
        :return bool:
        """

        return self.__top_manager.send(data)

    def receive(self):
        """
        Receive method

        :return:
        """

        return self.__top_manager.receive()

    def run_uhost_connection(self, config):
        """
        Run Uhost connection

        :param dict config: Config
        :return:
        """

        return self.__top_manager.run_uhost_connection(config)

    def run_platform_connection(self, config):
        """
        Run Uhost connection

        :param dict config: Config
        :return:
        """

        return self.__top_manager.run_platform_connection(config)

    def stop(self):
        """
        Stop
        """

        if self.__top_manager:
            self.__top_manager.stop()
        if self.__transport_manager:
            self.__transport_manager.stop()
        if self.__network_manager:
            self.__network_manager.stop()
        if self.__datalink_manager:
            self.__datalink_manager.stop()
