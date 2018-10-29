"""
Encryption worker
"""

import logging
from ..utilities.cryptography import CryptoLayer
from ..utilities.address import Address
from ..utilities.status import Status
from ..utilities.data_indexes import SubprocessorIndex


def process(utim, data):
    """
    Run process
    """

    res = None
    try:
        crypto = CryptoLayer(utim.get_session_key())
        logging.debug('Unsigning package {0} with key {1}'
                      .format(data[SubprocessorIndex.body.value], utim.get_session_key()))
        res = crypto.unsign(data[SubprocessorIndex.body.value])
        logging.debug('Unsigned message: {0}'.format(res))
    except TypeError:
        logging.error('Error appeared in unsigning message')
    if res is None:
        return [Address.ADDRESS_UHOST, Address.ADDRESS_UTIM, Status.STATUS_FINALIZED, res]
    else:
        return [Address.ADDRESS_UHOST, Address.ADDRESS_UTIM, Status.STATUS_PROCESS, res]
