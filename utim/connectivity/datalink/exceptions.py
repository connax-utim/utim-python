"""
DataLink layer exceptions
"""


class DataLinkManagerException(Exception):
    """
    Base DataLinkManagerException
    """
    pass


class DataLinkManagerWrongTypeException(DataLinkManagerException):
    """
    DataLink Wrong Type exception
    """
    pass


class DataLinkManagerWrongArgsException(DataLinkManagerException):
    """
    DataLink Manager Wrong arguments Exception
    """
    pass


class DataLinkManagerInitializationException(DataLinkManagerException):
    """
    DataLink Initialization Exception
    """
    pass


class DataLinkRealisationException(Exception):
    """
    Base DataLink Layer Realisation Exception
    Крч если будут Queue и Uart кидать исключения, наследовать отсюда
    """
    pass


class DataLinkRealisationConnectionException(DataLinkRealisationException):
    """
    DataLink Realisation Connection Exception
    """
    pass


class DataLinkRealisationWrongArgsException(DataLinkRealisationException):
    """
    DataLink Realisation Wrong arguments Exception
    """
    pass
