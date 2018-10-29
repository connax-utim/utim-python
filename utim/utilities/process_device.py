"""
Subprocessor for device messages
"""

from ..utilities.tag import Tag
from ..workers import device_worker_forward
from ..workers import device_worker_startup
from ..utilities.address import Address
from ..utilities.status import Status
from ..utilities.data_indexes import SubprocessorIndex


class ProcessDevice(object):
    """
    Subprocessor for device messages
    """

    def __init__(self, utim):
        """
        Initialization of subprocessor for device messages
        """

        self.__utim = utim

    def process(self, data):
        """
        Process device message
        :param data: array [source, destination, status, body]
        :return: same as input
        """

        # Placeholder for data being processed, that will be returned one day
        res = data

        while (res[SubprocessorIndex.status.value] is not Status.STATUS_TO_SEND and
               res[SubprocessorIndex.status.value] is not Status.STATUS_FINALIZED and
               res[SubprocessorIndex.source.value] is Address.ADDRESS_DEVICE):
            command = res[SubprocessorIndex.body.value][0:1]
            if command == Tag.INBOUND.DATA_TO_PLATFORM:
                res = device_worker_forward.process(self.__utim, res)
            elif command == Tag.INBOUND.NETWORK_READY:
                res = device_worker_startup.process(self.__utim, res)
            else:
                res[SubprocessorIndex.status.value] = Status.STATUS_FINALIZED

            if (res[SubprocessorIndex.status.value] is Status.STATUS_TO_SEND or
                    res[SubprocessorIndex.status.value] is Status.STATUS_FINALIZED):
                break

        return res
