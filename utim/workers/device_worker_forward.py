"""
Device forward worker
"""

from ..utilities.address import Address
from ..utilities.status import Status
from ..utilities.data_indexes import SubprocessorIndex


def process(utim, data):
    """
    Run process
    """

    device_data = data[SubprocessorIndex.body.value][1:]
    platform_item = [device_data, {}, '', False]
    outbound_item = [Address.ADDRESS_UTIM, Address.ADDRESS_PLATFORM, Status.STATUS_TO_SEND, platform_item]
    return outbound_item
