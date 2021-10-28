import datetime
import json
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
        current_date = datetime.date.today()  # Current Date
        try:
            items = (NFT.select().where(NFT.updatedAtDate == current_date).order_by(NFT.updatedAtHour.desc()))  # Get all NFTs of the current date
        except Exception as e:
            print(f"Exception found '{e}'")

        for nft in items:
            print(nft.updatedAtHour)

        # Table NFTs is empty
        if len(items) == 0:
            print('Table NFTs is Empty - Prepare to load Data')
            self.__populateTables(data)
            print('NFTs were loaded in Data Base.')
        else:  # Table NFTs have already some data
            print(f'Table NFTs have {len(items)} rows')
            if (len(data) - len(items)) == 0:
                print(f'There are no new data to add.')
            else:
                print(f'Prepare to load {len(data) - len(items)} new Items')
                items_to_add = self.__compare_items_to_add(data, items[0])

    def __populateTables(self, data):
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
                    print(f'A raridade {item_rarity} esta repetida')

                items.append(self.__get_item_to_populate(item, attributes, item_rarity))

        for rarity in populations_list:
            populations_list_dic.append({'rarity': rarity})

        self.__load_polutations(populations_list_dic)
        self.__load_items(items)

        print("tewste")


    def __compare_items_to_add(self, data, item_to_compare):
        return []

    def __prepare_data_to_load_in_db(self, data):
        pass

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














