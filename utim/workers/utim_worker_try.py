"""
The Worker dedicated to process command "Try" arrived from Uhost. The command means "Do calculate the SRP challenge"

The Worker checks if the SRP-client is still available, Worker parses the challenge extracting
two parameters, prepares them and tries to calculate the response by calling SRP-client's method
the corresponding SRP-client's method. In case the response was calculated successfully
the Worker builds the command "check" (meaning request to Uhost to validate the response),
packages it into TLV with the Tag "Data to be sent to Uhost" (Tag 0x2D)
and finally puts the message into the outbound queue.

in case the challenge response calculation failed the Worker builds the "error" command to Uhost
explaining the reason of failure, wraps it into TLV with Tag "Data to be sent to Uhost" (Tag 0x2D)
and puts it into the outbound queue.


"""

import logging
from ..utilities.tag import Tag
from ..utilities.address import Address
from ..utilities.status import Status
from ..utilities.data_indexes import SubprocessorIndex


def process(utim, data):
    """
    Run process

    :param Utim utim : utim
    :param bytes data: data to process
    """

    packet = None
    uhost_data = data[SubprocessorIndex.body.value]

    tag1 = uhost_data[0:1]
    length_bytes1 = uhost_data[1:3]
    length1 = int.from_bytes(length_bytes1, byteorder='big', signed=False)
    value1 = uhost_data[3:3 + length1]

    tag2 = uhost_data[3 + length1:4 + length1]
    length_bytes2 = uhost_data[4 + length1: 6 + length1]
    length2 = int.from_bytes(length_bytes2, byteorder='big', signed=False)
    value2 = uhost_data[6 + length1:6 + length1 + length2]

    # Logging
    logging.debug('Tag1: %s', str(tag1))
    logging.debug('Length1: %d', length1)
    logging.debug('Value1: %s', [x for x in value1])
    logging.debug('Tag2: %s', str(tag2))
    logging.debug('Length2: %d', length2)
    logging.debug('Value2: %s', [x for x in value2])

    # Check real data length
    if (length1 == len(value1) and tag1 == Tag.UCOMMAND.TRY_FIRST and
        length2 == len(value2) and tag2 == Tag.UCOMMAND.TRY_SECOND):
        # Get SRP client
        srp_client = utim.get_srp_client()
        if srp_client is not None:
            # Calculate
            M = srp_client.process_challenge(value1, value2)
            logging.debug(str(M))
            logging.debug("M: %s", None if not isinstance(M, bytes) else [x for x in M] )

            # Answer
            if M is None:
                logging.debug('error try processing')
                packet = Tag.UCOMMAND.assemble_error('try processing'.encode('utf-8'))
            else:
                # Set new SRP step value
                utim.set_srp_step(2)

                packet = Tag.UCOMMAND.assemble_check(M)
        else:
            logging.debug('SRP client is None')
            return [data[0], data[1], Status.STATUS_FINALIZED, data[3]]

    else:
        logging.debug('error try wrong_parameters')
        command = Tag.UCOMMAND.assemble_error('try wrong_parameters'.encode('utf-8'))
        packet = Tag.OUTBOUND.assemble_for_network(command)

    # Put packet to the queue
    if packet is not None:
        logging.debug('put answer to outbound queue')
        return [Address.ADDRESS_UTIM, Address.ADDRESS_UHOST, Status.STATUS_PROCESS, packet]
