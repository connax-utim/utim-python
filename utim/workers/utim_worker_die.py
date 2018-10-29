"""

The Worker dedicated to process "die" command arrived from Uhost.

The Worker simply calls the Utim's Die() method which terminates the Utim's execution.

"""

import logging
from ..utilities.address import Address
from ..utilities.status import Status
from ..utilities.data_indexes import SubprocessorIndex


def process(utim, data):
    """
    Run process

    :param bytes data: data to process
    :param Queue outbound_queue: queue to write in
    """

    logging.debug("CommandWorkerDie process data: %s", [x for x in data[SubprocessorIndex.body.value]])

    utim.utim_die()

    res = data
    res[SubprocessorIndex.status.value] = Status.STATUS_FINALIZED
    return res
