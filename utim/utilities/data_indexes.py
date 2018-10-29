from enum import Enum


class ProcessorIndex(Enum):
    """
    Processor indexes
    """

    address = 0
    body = 1


class SubprocessorIndex(Enum):
    """
    Subprocessor indexes
    """

    source = 0
    destination = 1
    status = 2
    body = 3
