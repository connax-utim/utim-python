"""

The Worker dedicated to process the "error" command arriving from Uhost.

Currently does nothing except for reporting the error (while being in debug mode)
then permanently discards the command.


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

    logging.debug("WorkerError process data: %s", [x for x in data[SubprocessorIndex.body.value]])

    # Allow start SRP authentication if error is 'hello', 'check' or 'trusted' type
    try:
        uhost_data = data[SubprocessorIndex.body.value]
        tag = uhost_data[0:1]
        length = uhost_data[1:3]
        value = uhost_data[3:]
        data_split = value.decode('utf-8').split(' ', 1)
        if data_split[0] in ('hello', 'check', 'trusted'):
            utim.set_srp_iterations(10)
            utim.set_srp_step(None)
    except UnicodeDecodeError as ex:
        logging.error(ex)
    res = data
    res[SubprocessorIndex.status.value] = Status.STATUS_FINALIZED
    return res
