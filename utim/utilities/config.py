import configparser
import os


class ConfigException(Exception):
    """
    Config exception
    """

    pass


class Config(object):

    def __init__(self):
        """
        Initialization
        """

        self.parser = configparser.ConfigParser()
        self.file = os.environ.get('UTIM_CONFIG', 'config.ini')
        self.parser.read(self.file)

        try:
            self.__utim_name = self.parser['UTIM']['utimname']
            self.__uhost_name = self.parser['UTIM']['uhostname']
            self.__utim_messaging_protocol = self.parser['UTIM']['messaging_protocol']
            self.__messaging_hostname = self.parser[self.utim_messaging_protocol]['hostname']
            self.__messaging_username = self.parser[self.utim_messaging_protocol]['username']
            self.__messaging_password = self.parser[self.utim_messaging_protocol]['password']
            self.__messaging_reconnect_time = self.parser[self.utim_messaging_protocol]['reconnect_time']

        except KeyError:
            raise ConfigException

    @property
    def utim_name(self):
        return self.__utim_name

    @property
    def uhost_name(self):
        return self.__uhost_name

    @property
    def utim_messaging_protocol(self):
        return self.__utim_messaging_protocol

    @property
    def messaging_hostname(self):
        return self.__messaging_hostname

    @property
    def messaging_username(self):
        return self.__messaging_username

    @property
    def messaging_password(self):
        return self.__messaging_password

    @property
    def messaging_reconnect_time(self):
        return self.__messaging_reconnect_time
