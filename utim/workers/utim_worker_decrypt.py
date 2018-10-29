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
        logging.debug('Decrypting package {0} with key {1}'
                      .format(data[SubprocessorIndex.body.value], utim.get_session_key()))
        res = crypto.decrypt(data[SubprocessorIndex.body.value])
        logging.debug('Decrypted message: {0}'.format(res))
    except ValueError:
        logging.error('Error appeared in decrypting message')
    if res is None:
        return [Address.ADDRESS_UHOST, Address.ADDRESS_UTIM, Status.STATUS_FINALIZED, res]
    else:
        return [Address.ADDRESS_UHOST, Address.ADDRESS_UTIM, Status.STATUS_PROCESS, res]
