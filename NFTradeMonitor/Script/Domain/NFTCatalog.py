class NFTCatalog:

    def __init__(self):
        self.__NFTCatalog = []

    def add_nft(self, item):
        self.__NFTCatalog.append(item)

    @property
    def NFTCatalog(self):
        return self.__NFTCatalog

