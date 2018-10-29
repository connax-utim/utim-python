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

    if (source == Address.ADDRESS_DEVICE and destination == Address.ADDRESS_UTIM and
            status == Status.STATUS_PROCESS):
        tag = body[0:1]
        # length_bytes = body[1:3]
        # length = int.from_bytes(length_bytes, byteorder='big', signed=False)
        # value = body[3:3 + length]

        if tag == Tag.INBOUND.NETWORK_READY:
            # Get SRP step
            srp_step = utim.get_srp_step()

            if srp_step is None:
                # Get SRP client
                srp_client = utim.get_srp_client()

                if srp_client is not None:
                    # Init srp session
                    uname, a = srp_client.start_authentication()
                    command = Tag.UCOMMAND.assemble_hello(a)

                    # Set new SRP step value
                    utim.set_srp_step(1)

                    # Set output parameters
                    source = Address.ADDRESS_UTIM
                    destination = Address.ADDRESS_UHOST
                    status = Status.STATUS_PROCESS
                    body = command

                    print('Starting SRP sequence...')

                    # Return STATUS_TO_SEND result
                    return [source, destination, status, body]

                else:
                    logging.error("SRP client is None")

            else:
                logging.error("Invalid SRP step: %s", str(srp_step))

        else:
            logging.error("Invalid tag: %s", str(tag))

    else:
        logging.error("Invalid metadata: source=%s, destination=%s, status=%s", source, destination,
                      status)

    # Return STATUS_FINALIZED result
    status = Status.STATUS_FINALIZED
    return [source, destination, status, body]
