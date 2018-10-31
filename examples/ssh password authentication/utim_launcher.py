"""
Example of using received Utim session key to connect to server via ssh

As a result you will see output of executing 'ifconfig' command.

NOTE: Uhost part of this example creates user for Utim (Utim name is a username, Utim session key is a password)
"""

import logging
import queue
import paramiko
from utim.connectivity.manager import ConnectivityConnectError
from utim.utim import Utim
from utim.connectivity import DataLinkManager, TopDataType
from utim.connectivity.manager import ConnectivityManager
from utim.utilities.tag import Tag
from utim.utilities.exceptions import UtimConnectionException, UtimInitializationError

# Edit this values
_SERVER = 'localhost'
_UTIM_NAME = b'test'


def main():
    """
    Main function
    """

    concrete_utim = None
    cm1 = None
    session_key = None

    logging.info("INIT rxQ")
    rx_queue = queue.Queue()
    logging.info("INIT txQ")
    tx_queue = queue.Queue()

    try:
        cm1 = ConnectivityManager()
        cm1.connect(dl_type=DataLinkManager.TYPE_QUEUE, rx=tx_queue, tx=rx_queue)

        concrete_utim = Utim()
        concrete_utim.connect(dl_type=DataLinkManager.TYPE_QUEUE, rx=rx_queue, tx=tx_queue)
        concrete_utim.run()

        data1 = [TopDataType.DEVICE, Tag.INBOUND.NETWORK_READY]

        print("cm1 - send {0}".format(data1))
        cm1.send(data1)

        while True:
            data = cm1.receive()
            if data:
                print("RECEIVED DATA: {0}".format(data))
                session_key = data[1]
                concrete_utim.stop()
                break

        print("RECEIVED SESSION KEY: {key}".format(key=session_key))

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.connect(_SERVER, username=_UTIM_NAME.hex().upper(), password=session_key.hex())
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('ifconfig')
        for line in iter(ssh_stdout.readline, ""):
            print(line, end="")
        ssh.close()

    except ConnectivityConnectError:
        logging.error("Connectivity error")
        print("Connectivity error")

    except UtimConnectionException as er:
        logging.error(er)

    except UtimInitializationError as er:
        logging.error(er)
        print('Invalid UTIM_MASTER_KEY')

    except (KeyboardInterrupt, EOFError):
        logging.info('Program interrupted')
        print('Program interrupted')

    finally:
        if concrete_utim:
            concrete_utim.stop()

        if cm1:
            cm1.stop()


if __name__ == '__main__':
    main()
