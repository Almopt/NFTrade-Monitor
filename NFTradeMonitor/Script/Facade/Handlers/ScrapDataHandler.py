import asyncio
import json

from datetime import datetime
import time as t

import requests
from requests_html import AsyncHTMLSession

from NFTradeMonitor.Script.DB.Schemas.NFT import NFT
from NFTradeMonitor.Script.DB.Schemas.Population import Population
from NFTradeMonitor.Script.DB.db import data_base


class ScrapDataHandler:

    def __init__(self, url, proxyCatalog, userAgent):
        self.__url = url
        self.__proxyCatalog = proxyCatalog
        self.__userAgent = userAgent
        self.__populations = []
        self.__items = []
        self.__data_in_chunks = []

    def scrap_data(self):

        """
        This Function is the entry point to start scraping the nftrade website
        Starting by request all Recently Listed Items, and then persist the new items
        who were nos listed yet.
        :return:
        """

        self.__proxyCatalog.update_proxy_list()  # Proxy List will be updated
        session = requests.session()  # Create Session for request data

        r = session.get(self.__url, headers=self.__userAgent.get_random_user_agent(),
                        proxies=self.__proxyCatalog.get_proxy(), verify=False, timeout=100)

        print(f'NFTrade have {len(json.loads(r.text))} Polychain Monsters Listed!')

        self.__persist_data(json.loads(r.text))

    def __persist_data(self, data):

        """
        This function firstly start by getting the most recent items loaded in our data base
        in order to know in which date and time was listed to compare with new items to not store
        equal items.
        :param data: all recently Listed Items in json format
        :return:
        """

        # Get the most Recent Listed NFT in Data Base
        items = (NFT.select().order_by(NFT.updatedAtDate.desc(), NFT.updatedAtHour.desc()).limit(10))

        idx_while = 0

        # Table NFTs is empty
        if len(items) == 0:
            print('Table NFTs is Empty - Prepare to load Data')
            self.__data_in_chunks = self.__divide_list_by_chuncks(data, 200)
            print(f'Data divided by {len(self.__data_in_chunks)} chunks')

            while len(self.__data_in_chunks) > 0:
                if idx_while > 0:
                    print(f'Sleeping for 10 minutes, in order to get more proxies')
                    t.sleep(600)

                self.__proxyCatalog.update_proxy_list()  # Proxy List will be updated
                asyncio.run(self.__scrap_data())
                print(f'Scraped {len(self.__items)} Items')
                print(f'Scraped {len(self.__populations)} Populations')
                print(f'Still {len(self.__data_in_chunks)} chunks to scrap')
                print(f'---------------------------------------------------')
                idx_while += 1

            print('Loading data into DataBase...')
            self.__populate_db_tables()
            print('NFTs were loaded in Data Base.')

        else:  # Table NFTs have already some data
            print(f'Validating New Listed Items')
            new_data = self.__compare_items_to_add(data, items[0])
            if len(new_data) > 0:
                self.__data_in_chunks = self.__divide_list_by_chuncks(new_data, 200)

                while len(self.__data_in_chunks) > 0:
                    if idx_while > 0:
                        print(f'Sleeping for 10 minutes, in order to get more proxies')
                        t.sleep(600)

                    self.__proxyCatalog.update_proxy_list()  # Proxy List will be updated
                    asyncio.run(self.__scrap_data())
                    populations_list_with_no_duplicates = self.__compare_item_rarity_with_db(self.__populations)
                    self.__populations = populations_list_with_no_duplicates
                    if len(self.__items) > 0 or len(self.__populations) > 0:
                        print(f'{len(self.__items)} New Items')
                        print(f'{len(self.__populations)} New Populations')
                        idx_while += 1

                        print(f'New Items will be store in DB.')
                        self.__populate_db_tables()
                    else:
                        print(f'New Item/s doesnt have the required data')
            else:
                print(f'No New Items to Add')

        return self.__items

    async def __scrap_data(self):
        tasks = []

        for idx, proxy in enumerate(self.__proxyCatalog.proxyList):
            if len(self.__data_in_chunks) > 0:
                tasks.append(asyncio.create_task(self.__scrap_data_aux(proxy, self.__data_in_chunks.pop(0))))
            else:
                break

        await asyncio.gather(*tasks)

    async def __scrap_data_aux(self, proxy, data):
        tasks = []
        session = AsyncHTMLSession()
        header = self.__userAgent.get_random_user_agent()
        sem = asyncio.Semaphore(10)
        for item in data:
            tasks.append(self.__fetch_data_with_sem(session, proxy, item, header, sem))

        await asyncio.gather(*tasks)
        await session.close()

    async def __fetch_data_with_sem(self, session, proxy, item, header,  sem):
        async with sem:
            await self.__fetch_data(session, proxy, item, header)

    async def __fetch_data(self, session, proxy, item, header):
        proxy = {"http": f"https://{proxy.__str__()}"}
        token_id = item['tokenID']
        url = f'https://meta.polkamon.com/meta?id={token_id}'
        resp = await session.get(url, headers=header, proxies=proxy, verify=False, timeout=100)
        attributes = json.loads(resp.text)  # Transform json into text

        if 'initialProbabilities' in attributes:
            item_rarity = round(self.__calculate_rarity(attributes['initialProbabilities']), 5)
            if item_rarity not in self.__populations:
                self.__populations.append(item_rarity)

            self.__items.append(self.__get_item_to_populate(item, attributes, item_rarity))

    def __populate_db_tables(self):
        populations_list_dic = []

        for rarity in self.__populations:
            populations_list_dic.append({'rarity': rarity})

        self.__load_polutations(populations_list_dic, 10000)
        self.__load_items(10000)

    def __compare_item_rarity_with_db(self, rarities):
        rarities_to_persist = []
        population_list = Population.select().dicts()

        for rarity in rarities:
            equal_rarities = 0
            for population in population_list:
                if rarity in population.values():
                    equal_rarities += 1
                    break
            if equal_rarities == 0:
                rarities_to_persist.append(rarity)
                
        return rarities_to_persist

    def __compare_items_to_add(self, data, item_to_compare):

        """
        This function filters the data from NFTrade API
        :param data: All items from NFTrade API
        :param item_to_compare: Last item stored in DB
        :return: List of all items that are not yet on DB
        """

        items_to_persist = []
        for item in data:
            if self.__compare_date_time(item['updatedAt'], item_to_compare.updatedAtDate,
                                        item_to_compare.updatedAtHour):
                items_to_persist.append(item)
            else:
                break
        return items_to_persist

    def __compare_date_time(self, datetime_api, date_db, time_db):

        """
        This function is used to compare 2 dates
        :param datetime_api: DateTime from Api ("2021-10-28T11:45:35.241Z")
        :param date_db: Date from DB ("2021-10-28")
        :param time_db: Time from DB ("11:45:35.241")
        :return: True is the DateTime of the datetime_api is greater then the last item
        stored in DB
        """

        comparator = False
        datetime_aux = datetime.strptime(datetime_api, '%Y-%m-%dT%H:%M:%S.%fZ')
        str_datetime_db = f'{date_db} {time_db}'
        datetime_db_aux = datetime.strptime(str_datetime_db, '%Y-%m-%d %H:%M:%S.%f')
        if datetime_aux > datetime_db_aux:
            comparator = True

        return comparator

    def __load_items(self, batch_size):

        """
        This function is used to load a list of nfts/items in data base
        :param items: A dictionary of all nfts/items to store
        :return:
        """

        # Insert batch_size rows at a time.
        with data_base.atomic():
            for idx in range(0, len(self.__items), batch_size):
                NFT.replace_many(self.__items[idx:idx + batch_size]).execute()

        # with data_base.atomic():
        #     NFT.insert_many(items).execute()

    def __load_polutations(self, populations, batch_size):

        """
        This function is used to load a list of populations in data base
        :param populations: All the populations to store in data base
        :return:
        """

        # Insert batch_size rows at a time.
        with data_base.atomic():
            for idx in range(0, len(populations), batch_size):
                Population.insert_many(populations[idx:idx + batch_size]).execute()

        # with data_base.atomic():
        #     Population.insert_many(populations, fields=[Population.rarity, Population.mean]).execute()


    def __calculate_rarity(self, probabilities):

        """
        This function calculate the value of population of a certain nft/item
        by total sum of 1/each prob value
        :param probabilities: probabilities of each trait
        :return: sum of 1/each prob value
        """

        population = 0
        for attr in probabilities:
            population += 1/probabilities.get(attr)

        return population

    def __get_item_to_populate(self, item, attributes, population):

        """
        This Function load all the necessary data into a dictionary from a item
        to load into DB
        :param item: Current Item/NFT
        :param attributes: Dictionary of traits probabilities
        :param population: Item´s Population
        :return: A dictionary will all information ready to load into DB
        """

        token_id = item['tokenID']
        token_uri = f'https://meta.polkamon.com/meta?id={token_id}'
        date_time = self.__get_separate_date_time(item['updatedAt'])
        dic = {
            'contractAddress': item['contractAddress'],
            'tokenId': item['tokenID'],
            'tokenURI': token_uri,
            'imageUrl': item['image'],
            'price': item['price'],
            'lastSell': item['last_sell'],
            'updatedAtDate': date_time[0],
            'updatedAtHour': date_time[1], 
            'url': f'https://app.nftrade.com/assets/bsc/0x85f0e02cb992aa1f9f47112f815f519ef1a59e2d/{token_id}'
        }

        # Add Probabilities to the Dictionary
        for attr in attributes['initialProbabilities']:
            if attr == 'horn':
                dic['horn_prob'] = attributes['initialProbabilities'].get(attr)
            elif attr == 'color':
                dic['color_prob'] = attributes['initialProbabilities'].get(attr)
            elif attr == 'background':
                dic['background_prob'] = attributes['initialProbabilities'].get(attr)
            elif attr == 'glitter':
                dic['glitter_prob'] = attributes['initialProbabilities'].get(attr)
            else:
                dic['type_prob'] = attributes['initialProbabilities'].get(attr)

        for idx, list_attr in enumerate(attributes['attributes']):
            if idx == 0:
                dic['type'] = list_attr['value']
            elif idx == 1:
                dic['horn'] = list_attr['value']
            elif idx == 2:
                dic['color'] = list_attr['value']
            elif idx == 3:
                dic['background'] = list_attr['value']
            elif idx == 4:
                dic['open_network'] = list_attr['value']
            elif idx == 5:
                dic['glitter'] = list_attr['value']
            else:
                dic['special'] = list_attr['value']

        dic['population'] = population

        return dic

    def __get_separate_date_time(self, date_time):

        """
        This function recieve a datatime in string format and return a
        list with the date and time separated
        :param date_time: "2021-10-28T11:45:35.241Z"
        :return: List with the date and time separated
        """

        return [date_time.split("T")[0], date_time.split("T")[1].split("Z")[0]]

    def __divide_list_by_chuncks(self, data, num_chunks):
        newList = [data[x:x+num_chunks] for x in range(0, len(data), num_chunks)]
        return newList














