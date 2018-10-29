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
        cs_tag = body[0:1]
        cs_length_bytes = body[1:3]
        cs_length = int.from_bytes(cs_length_bytes, byteorder='big', signed=False)
        cs = body[3:3 + cs_length]

        if cs_tag == Tag.UCOMMAND.CONNECTION_STRING:
            # Parse platform tag
            pl_tag = cs[0:1]
            pl_length_bytes = cs[1:3]
            pl_length = int.from_bytes(pl_length_bytes, byteorder='big', signed=False)
            command = cs[3:3 + pl_length]

            if pl_tag in (Tag.UPLATFORM.PL_AZURE, Tag.UPLATFORM.PL_AWS):

                # Set output parameters
                source = Address.ADDRESS_UHOST
                destination = Address.ADDRESS_UTIM
                status = Status.STATUS_PROCESS
                body = command

                print('Connecting to cloud...')

                # Return STATUS_PROCESS result
                return [source, destination, status, body]

            else:
                logging.error("Invalid pl_tag: %s", str(pl_tag))

        else:
            logging.error("Invalid cs_tag: %s", str(cs_tag))

    else:
        logging.error("Invalid metadata: source=%s, destination=%s, status=%s", source, destination,
                      status)

    # Return STATUS_FINALIZED result
    status = Status.STATUS_FINALIZED
    return [source, destination, status, body]
