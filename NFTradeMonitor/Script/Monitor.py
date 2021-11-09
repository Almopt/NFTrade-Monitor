import time as t

from NFTradeMonitor.Script.DB.Schemas.NFT import NFT
from NFTradeMonitor.Script.DB.Schemas.Population import Population
from NFTradeMonitor.Script.DB.db import data_base
from NFTradeMonitor.Script.Domain.NFTCatalog import NFTCatalog
from NFTradeMonitor.Script.Domain.ProxyCatalog import ProxyCatalog
from NFTradeMonitor.Script.Domain.UserAgent4Scrap import UserAgent4Scrap
import dotenv

from NFTradeMonitor.Script.Facade.Handlers.CalculationsHandler import CalculationsHandler
from NFTradeMonitor.Script.Facade.Handlers.ScrapDataHandler import ScrapDataHandler


class Monitor:

    CONFIG = dotenv.dotenv_values()

    def __init__(self):
        self.__proxyCatalog = ProxyCatalog()
        self.__userAgent = UserAgent4Scrap()
        self.__nftCatalog = NFTCatalog()

    def start(self):
        print('STARTING NFTRADE MONITOR')

        data_base.connect()  # Connect to data base
        #data_base.drop_tables([Population, NFT])  # Drop Tables
        data_base.create_tables([Population, NFT])  # Create Tables

        while True:
            try:

                print('###################### START SCRAP #########################')

                scraper = ScrapDataHandler(self.CONFIG['URL'], self.__proxyCatalog, self.__userAgent)
                new_scrapped_items = scraper.scrap_data()

                #calculator = CalculationsHandler()
                #calculator.calculate_mean()
                #items_to_send = calculator.get_items_to_send(new_scrapped_items)


                # User set delay
                delay = float(self.CONFIG['DELAY'])
                print(f'Sleeping for {delay} seconds...')
                t.sleep(delay)

            except Exception as e:
                print(f"Exception found '{e}'")
                #logging.error(e)
