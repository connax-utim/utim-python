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
        logging.debug('Signing message {0} with key {1}'
                      .format(data[SubprocessorIndex.body.value], utim.get_session_key()))
        res = crypto.sign(CryptoLayer.SIGN_MODE_SHA1, data[SubprocessorIndex.body.value])
        logging.debug('Signed package: {0}'.format(res))
    except TypeError:
        logging.error('Error appeared in signing message')
    if res is None:
        return [Address.ADDRESS_UTIM, Address.ADDRESS_UHOST, Status.STATUS_FINALIZED, res]
    else:
        return [Address.ADDRESS_UTIM, Address.ADDRESS_UHOST, Status.STATUS_TO_SEND, res]
