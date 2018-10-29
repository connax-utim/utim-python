"""
Keepalive worker
"""

import logging
from ..utilities.address import Address
from ..utilities.status import Status
from ..utilities.tag import Tag
from ..utilities.data_indexes import SubprocessorIndex


def process(utim, data):
    """
    Run process
    """

    logging.info('Got keepalive!')
    outbound_item = [Address.ADDRESS_UTIM, Address.ADDRESS_UHOST, Status.STATUS_PROCESS, Tag.UCOMMAND.KEEPALIVE_ANSWER]
    return outbound_item
