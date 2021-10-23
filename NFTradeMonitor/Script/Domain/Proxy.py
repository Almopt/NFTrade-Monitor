class Proxy:

    def __init__(self, ip, port):
        self.__ip = ip
        self.__port = port

    @property
    def ip(self):
        return self.__ip

    @property
    def port(self):
        return self.__port

    def __str__(self):
        return f'{self.__ip}:{self.__port}'
    