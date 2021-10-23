from NFTradeMonitor.Script.Domain.NFTCatalog import NFTCatalog
from NFTradeMonitor.Script.Domain.ProxyCatalog import ProxyCatalog
from NFTradeMonitor.Script.Domain.UserAgent4Scrap import UserAgent4Scrap
import dotenv

from NFTradeMonitor.Script.Facade.Handlers.ScrapDataHandler import ScrapDataHandler


class Monitor:

    CONFIG = dotenv.dotenv_values()

    def __init__(self):
        self.__proxyCatalog = ProxyCatalog()
        self.__userAgent = UserAgent4Scrap()
        self.__nftCatalog = NFTCatalog()

    def start(self):
        print('STARTING PYTHON SCRIPT')

        # Ensures that first scrape does not notify all products
        start = 1

        while True:
            try:

                if start == 0:
                    print('###################### RELOAD SCRAP ########################')
                else:
                    print('###################### START SCRAP #########################')

                scraper = ScrapDataHandler(self.CONFIG['URL'], self.__nftCatalog, self.__proxyCatalog, self.__userAgent)
                scraper.scrap_data()


                #items = remove_duplicates(asyncio.run(scrape_main_site(proxies.getProxies())))

                # print('SCRAP COMPLETED: Found ' + str(len(items)) + ' items.')
                #
                # for item in items:
                #
                #     if keywords[0] == "":
                #         # If no keywords set, checks whether item status has changed
                #         comparitor(item, start, proxies.getProxies())
                #
                #     else:
                #         # For each keyword, checks whether particular item status has changed
                #         for key in keywords:
                #             if key.lower() in item[6].lower():
                #                 print('ITEM -> ' + item[6] + ' - ' + item[1] + ' MATCH THE KEYWORD.')
                #                 comparitor(item, start, proxies.getProxies())
                #
                # print(str(len(INSTOCK)) + ' ITEMS IN STOCK')

                # Allows changes to be notified
                start = 0

                # User set delay
                #time.sleep(float(CONFIG['DELAY']))

            except Exception as e:
                print(f"Exception found '{e}'")
                #logging.error(e)
