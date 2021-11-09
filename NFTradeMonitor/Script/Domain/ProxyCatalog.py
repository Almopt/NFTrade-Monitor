import requests
import random
from lxml.html import fromstring
from NFTradeMonitor.Script.Domain.Proxy import Proxy


class ProxyCatalog:

    def __init__(self):
        self.__proxyList = []

    @property
    def proxyList(self):
        return self.__proxyList

    def get_proxy(self):
        n = random.randint(0, len(self.__proxyList) - 1)
        return {"http": f"https://{self.__proxyList[n]}"}

    def update_proxy_list(self):

        """ This funtion is used to update the proxy list
        in order to have updated proxies
        """

        if len(self.__proxyList) > 0:
            self.__proxyList.clear()
        self.__get_free_proxies()

    def __get_free_proxies(self):

        """ This function is used to scrap a website who provide
        free proxies to use.
        """

        url = 'https://free-proxy-list.net/'
        response = requests.get(url)
        parser = fromstring(response.text)
        for i in parser.xpath('//tbody/tr')[:45]:
            if i.xpath('.//td[5][contains(text(),"elite proxy")]') or i.xpath('.//td[5][contains(text(),"anonymous")]'):
                # Grabbing IP and corresponding PORT
                #proxyStr = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
                proxy = Proxy(i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0])
                if len(self.__proxyList) < 25:
                    self.__proxyList.append(proxy)

