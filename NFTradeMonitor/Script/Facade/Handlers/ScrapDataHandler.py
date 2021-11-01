import datetime
import json

import datetime

import datetime as datetime
import requests

from NFTradeMonitor.Script.DB.Schemas.NFT import NFT
from NFTradeMonitor.Script.DB.Schemas.Population import Population
from NFTradeMonitor.Script.DB.db import data_base


class ScrapDataHandler:

    def __init__(self, url, nftCatalog, proxyCatalog, userAgent):
        self.__url = url
        self.__nftCatalog = nftCatalog
        self.__proxyCatalog = proxyCatalog
        self.__userAgent = userAgent

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

        print('Loading data into DataBase...')
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
        items = (NFT.select().order_by(NFT.updatedAtDate.desc(), NFT.updatedAtHour.desc()).limit(10))  # Get all NFTs of the current date

        # Table NFTs is empty
        if len(items) == 0:
            print('Table NFTs is Empty - Prepare to load Data')
            self.__populate_tables(data)
            print('NFTs were loaded in Data Base.')
        else:  # Table NFTs have already some data
            if (len(data) - len(items)) == 0:
                print(f'There are no new data to add.')
            else:
                print(f'Validating {len(data) - len(items)} New Items')
                new_data = self.__compare_items_to_add(data, items[0])
                print(f'{len(new_data)} New Items will be store in DB.')
                self.__populate_tables_new_items(new_data)

    def __populate_tables(self, data):
        session = requests.session()
        header = self.__userAgent.get_random_user_agent()
        proxy = self.__proxyCatalog.get_proxy()
        populations_list = []
        populations_list_dic = []
        items = []

        for item in data:
            r = session.get(item['tokenURI'], headers=header, proxies=proxy, verify=False, timeout=100)
            attributes = json.loads(r.text)  # Transform json into text

            if 'initialProbabilities' in attributes:
                item_rarity = round(self.__calculate_rarity(attributes['initialProbabilities']), 5)
                if item_rarity not in populations_list:
                    populations_list.append(item_rarity)
                else:
                    print(f'The rarity {item_rarity} is repeated.')
                                                  
                items.append(self.__get_item_to_populate(item, attributes, item_rarity))

        for rarity in populations_list:
            populations_list_dic.append({'rarity': rarity})

        self.__load_polutations(populations_list_dic)
        self.__load_items(items)

    def __populate_tables_new_items(self, data):
        session = requests.session()
        header = self.__userAgent.get_random_user_agent()
        proxy = self.__proxyCatalog.get_proxy()
        populations_list = []
        populations_list_dic = []
        items = []

        for item in data:
            r = session.get(item['tokenURI'], headers=header, proxies=proxy, verify=False, timeout=100)
            attributes = json.loads(r.text)  # Transform json into text

            if 'initialProbabilities' in attributes:
                item_rarity = round(self.__calculate_rarity(attributes['initialProbabilities']), 5)
                if item_rarity not in populations_list:
                    populations_list.append(item_rarity)
                else:
                    print(f'The rarity {item_rarity} is repeated on New Items.')

                items.append(self.__get_item_to_populate(item, attributes, item_rarity))

        populations_list_with_no_duplicates = self.__compare_item_rarity_with_db(populations_list)

        for rarity in populations_list_with_no_duplicates:
            populations_list_dic.append({'rarity': rarity})



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
        datetime_aux = datetime.datetime.strptime(datetime_api, '%Y-%m-%dT%H:%M:%S.%fZ')
        str_datetime_db = f'{date_db} {time_db}'
        datetime_db_aux = datetime.datetime.strptime(str_datetime_db, '%Y-%m-%d %H:%M:%S.%f')
        if datetime_aux > datetime_db_aux:
            comparator = True

        return comparator

    def __load_items(self, items):

        """
        This function is used to load a list of nfts/items in data base
        :param items: A dictionary of all nfts/items to store
        :return:
        """

        with data_base.atomic():
            NFT.insert_many(items).execute()

    def __load_polutations(self, populations):

        """
        This function is used to load a list of populations in data base
        :param populations: All the populations to store in data base
        :return:
        """

        with data_base.atomic():
            Population.insert_many(populations, fields=[Population.rarity, Population.mean]).execute()


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
        date_time = self.__get_separate_date_time(item['updatedAt'])
        dic = {
            'contractAddress': item['contractAddress'],
            'tokenId': item['tokenID'],
            'tokenURI': item['tokenURI'],
            'imageUrl': item['image'],
            'price': item['price'],
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














