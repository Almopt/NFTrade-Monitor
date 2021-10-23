import json
import requests


class ScrapDataHandler:

    def __init__(self, url, nftCatalog, proxyCatalog, userAgent):
        self.__url = url
        self.__nftCatalog = nftCatalog
        self.__proxyCatalog = proxyCatalog
        self.__userAgent = userAgent

    def scrap_data(self):
        self.__proxyCatalog.update_proxy_list()  # Proxy List will be updated

        r = requests.get(self.__url)

        data = json.loads(r.text)

        print(f'NFTrade have {len(data)} Polychain Monsters Listed!')
        print('test')




