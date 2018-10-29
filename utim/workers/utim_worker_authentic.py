"""
The command worker
"""

import logging
from ..utilities.tag import Tag
from ..utilities.address import Address
from ..utilities.status import Status
from ..utilities.data_indexes import SubprocessorIndex

           
def process(utim, data):
    """
    Run  process
    """

    logging.debug("UTIM is authentic now!")
    res = data
    res[SubprocessorIndex.status.value] = Status.STATUS_FINALIZED

    logging.debug(data)
    packet = [Address.ADDRESS_UTIM, Address.ADDRESS_DEVICE, Status.STATUS_TO_SEND, utim.get_session_key()]

    # Put packet to the queue
    if packet is not None:
        logging.debug('put answer to device queue')
        return packet
    return res
