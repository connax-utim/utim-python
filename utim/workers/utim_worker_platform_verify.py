import logging
from ..utilities.tag import Tag
from ..utilities.address import Address
from ..utilities.status import Status
from ..utilities.data_indexes import SubprocessorIndex


def process(utim, data):
    """
    Run process

    :param Utim utim: Utim instance
    :param list data: Data to process [source, destination, status, body]
    :return list: [from, to, status, body]
    """

    source = data[SubprocessorIndex.source.value]
    destination = data[SubprocessorIndex.destination.value]
    status = data[SubprocessorIndex.status.value]
    body = data[SubprocessorIndex.body.value]

    if (source == Address.ADDRESS_UHOST and destination == Address.ADDRESS_UTIM and
            status == Status.STATUS_PROCESS):
        tag = body[0:1]
        length_bytes = body[1:3]
        length = int.from_bytes(length_bytes, byteorder='big', signed=False)
        command = body[3:3 + length]

        if tag == Tag.UCOMMAND.TEST_PLATFORM_DATA:
            # Set output parameters
            source = Address.ADDRESS_UTIM
            destination = Address.ADDRESS_PLATFORM
            status = Status.STATUS_TO_SEND
            body = [command, {}, 'verify', True]

            # Return STATUS_TO_SEND result
            logging.debug("Send test data via platform: %s", str(body))
            return [source, destination, status, body]

        else:
            logging.error("Invalid tag: %s", str(tag))

    else:
        logging.error("Invalid metadata: source=%s, destination=%s, status=%s", source, destination,
                      status)

    # Return STATUS_FINALIZED result
    status = Status.STATUS_FINALIZED
    return [source, destination, status, body]
