"""
Process Item module
"""

import logging
import queue
import threading
from .address import Address
from .status import Status
from . import process_device
from . import process_uhost
from . import process_platform
from .data_indexes import ProcessorIndex, SubprocessorIndex


class ProcessItemException(Exception):
    """
    General ProcessItemException
    """

    pass


class InputParametersException(ProcessItemException):
    """
    Input parameters exception
    """

    pass


class ProcessItem(object):
    """
    Process Item class
    """

    def __init__(self, utim, in_queue, out_queue):
        """
        Initialization

        :param Utim utim: Utim instance
        :param Queue in_queue: Inbound queue
        :param Queue out_queue: Outbound queue
        """

        # Check input parameters
        if not (isinstance(in_queue, queue.Queue) and isinstance(out_queue, queue.Queue)):
            raise InputParametersException()

        # Set utim
        self.__utim = utim

        # Threads
        self.__run_thread = None

        # Run event
        self.__run_event = threading.Event()

        # Queues
        self.__inbound_queue = in_queue
        self.__outbound_queue = out_queue

        # Handlers
        self.__device = process_device.ProcessDevice(self.__utim)
        self.__uhost = process_uhost.ProcessUhost(self.__utim)
        self.__platform = process_platform.ProcessPlatform(self.__utim)

        logging.info("Process Item is initialized!")

    def __process(self, data):
        """
        Inbound data processing and

        :param list data: Data to process [Source, Body]
        :return list: Processed data
        """

        source = data[ProcessorIndex.address.value]
        destination = Address.ADDRESS_UTIM
        status = Status.STATUS_PROCESS
        body = data[ProcessorIndex.body.value]

        # [From, To, Status, Message]
        data_to_process = [source, destination, status, body]
        logging.info("Data TO PROCESS {}".format(data_to_process))

        address = source
        while data_to_process[SubprocessorIndex.status.value] not in\
                (Status.STATUS_TO_SEND, Status.STATUS_FINALIZED):
            if address == Address.ADDRESS_DEVICE:
                data_to_process = self.__device.process(data_to_process)

            elif address == Address.ADDRESS_UHOST:
                data_to_process = self.__uhost.process(data_to_process)

            elif address == Address.ADDRESS_PLATFORM:
                data_to_process = self.__platform.process(data_to_process)

            if isinstance(data_to_process, list) and len(data_to_process) == 4:
                if (data_to_process[SubprocessorIndex.source.value] == Address.ADDRESS_UTIM and
                        data_to_process[SubprocessorIndex.destination.value] != Address.ADDRESS_UTIM):
                    address = data_to_process[SubprocessorIndex.destination.value]

                elif (data_to_process[SubprocessorIndex.source.value] != Address.ADDRESS_UTIM and
                      data_to_process[SubprocessorIndex.destination.value] == Address.ADDRESS_UTIM):
                    address = data_to_process[SubprocessorIndex.source.value]

                else:
                    data_to_process = self.__error_handler(data_to_process)

            else:
                break

        # print("Data PROCESSED", data_to_process)
        return self.__return_item(data_to_process)

    def __return_item(self, data):
        """
        Assemble answer

        :param data: Data
        :return list|None:
        """

        if isinstance(data, list) and len(data) == 4:
            if (data[SubprocessorIndex.destination.value] is not Address.ADDRESS_UTIM and
                    data[SubprocessorIndex.status.value] is not Status.STATUS_FINALIZED):
                return [
                    data[SubprocessorIndex.destination.value],
                    data[SubprocessorIndex.body.value]
                ]

        if data is not None:
            logging.error("Invalid data to return: %s %s", type(data), str(data))

        return None

    def run(self):
        """
        Run
        """

        self.__run_event.set()

        self.__run_thread = threading.Thread(
            target=self.__run2,
            name='THREAD_PROCESS_ITEM_RUN'
        )
        self.__run_thread.daemon = True
        self.__run_thread.start()

    def __run2(self):
        """
        Run2
        """

        while self.__run_event.is_set():
            try:
                data = self.__inbound_queue.get_nowait()
                res = self.__process(data)
                if res:
                    while not self.__put_data(res):
                        pass
            except queue.Empty:
                pass

        logging.info("Stopping processing..")

    def __put_data(self, data):
        """
        Put data

        :param data:
        :return bool:
        """

        try:
            self.__outbound_queue.put_nowait(data)
        except queue.Full:
            return False

        return True

    def stop(self):
        """
        Stop
        """

        if self.__run_event:
            self.__run_event.clear()

        if self.__run_thread:
            self.__run_thread.join()

    def __error_handler(self, data):
        """
        Error handler

        :param data: Data
        """

        logging.error("Item processing error: %s", str(data))

        if isinstance(data, list) and len(data) == 4:
            data[SubprocessorIndex.status.value] = Status.STATUS_FINALIZED
            return data

        return None
