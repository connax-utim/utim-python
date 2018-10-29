"""
Subprocessor for uhost messages
"""

import logging
from ..utilities.tag import Tag
from ..workers import utim_worker_try
from ..workers import utim_worker_init
from ..workers import utim_worker_connection_string
from ..workers import utim_worker_error
from ..workers import utim_worker_platform_verify
from ..workers import utim_worker_authentic
from ..workers import utim_worker_encrypt
from ..workers import utim_worker_decrypt
from ..workers import utim_worker_sign
from ..workers import utim_worker_unsign
from ..workers import utim_worker_keepalive
from ..utilities.data_indexes import SubprocessorIndex
from ..utilities.address import Address
from ..utilities.status import Status


class ProcessUhost(object):
    """
    Subprocessor for uhost messages
    """

    def __init__(self, utim):
        """
        Initialization of subprocessor for uhost messages
        """

        self.__utim = utim

    def process(self, data):
        """
        Process uhost message
        :param data: array [source, destination, status
        :return: same as input
        """

        res = data

        logging.info('Data to decipher: {}'.format(res))

        if (res[SubprocessorIndex.source.value] is Address.ADDRESS_UHOST and
                res[SubprocessorIndex.status.value] is Status.STATUS_PROCESS):
            res = utim_worker_unsign.process(self.__utim, res)
        if (res[SubprocessorIndex.source.value] is Address.ADDRESS_UHOST and
                res[SubprocessorIndex.status.value] is Status.STATUS_PROCESS):
            res = utim_worker_decrypt.process(self.__utim, res)

        logging.info('Data after deciphering: {}'.format(res))

        while (res[SubprocessorIndex.status.value] is not Status.STATUS_TO_SEND and
               res[SubprocessorIndex.status.value] is not Status.STATUS_FINALIZED and
               res[SubprocessorIndex.source.value] is Address.ADDRESS_UHOST):
            command = res[SubprocessorIndex.body.value][0:1]
            if command == Tag.UCOMMAND.TRY_FIRST:
                res = utim_worker_try.process(self.__utim, res)
            elif command == Tag.UCOMMAND.INIT:
                res = utim_worker_init.process(self.__utim, res)
            elif command == Tag.UCOMMAND.CONNECTION_STRING:
                res = utim_worker_connection_string.process(self.__utim, res)
            elif command == Tag.UCOMMAND.TEST_PLATFORM_DATA:
                res = utim_worker_platform_verify.process(self.__utim, res)
            elif command == Tag.UCOMMAND.AUTHENTIC:
                res = utim_worker_authentic.process(self.__utim, res)
            elif command == Tag.UCOMMAND.ERROR:
                res = utim_worker_error.process(self.__utim, res)

            elif command == Tag.UCOMMAND.KEEPALIVE:
                res = utim_worker_keepalive.process(self.__utim, res)

            else:
                res[SubprocessorIndex.status.value] = Status.STATUS_FINALIZED

        if (res[SubprocessorIndex.destination.value] == Address.ADDRESS_UHOST
                and res[SubprocessorIndex.status.value] == Status.STATUS_PROCESS):
            res = utim_worker_encrypt.process(self.__utim, res)
            res = utim_worker_sign.process(self.__utim, res)

        return res
