from NFTradeMonitor.Script.DB.Schemas.NFT import NFT
from NFTradeMonitor.Script.DB.Schemas.Population import Population
from NFTradeMonitor.Script.DB.db import data_base


class CalculationsHandler:

    def __init__(self):
        self.__populations = []

    def calculate_mean(self):

        rarity_and_mean = []
        rarity_and_mean_pop_plus_20 = []
        rarity_and_count_pop_minus_20 = []

        self.__populations = Population.select().dicts()
        
        for population in self.__populations:
            sum_price = 0
            items_from_population = NFT.select().where(NFT.population == population['rarity'],
                                                       ((NFT.price.is_null(False)) | (NFT.lastSell.is_null(False))))
            for item in items_from_population:
                if item.price is not None:
                    sum_price += float(item.price)
                else:
                    if item.lastSell is not None:
                        sum_price += item.lastSell

            if len(items_from_population) >= 20:
                mean = round(sum_price/len(items_from_population), 5)
                rarity_and_mean_pop_plus_20.append({'rarity': population['rarity'], 'mean': mean})
                rarity_and_mean.append({'rarity': population['rarity'], 'mean': mean})
            else:
                rarity_and_count_pop_minus_20.append({'rarity': population['rarity']})

        total_mean_div_rarity = self.__get_total_mean_div_rarity(rarity_and_mean_pop_plus_20)

        for pop_minus_20 in rarity_and_count_pop_minus_20:
            mean = round(total_mean_div_rarity / (len(rarity_and_mean_pop_plus_20) * pop_minus_20['rarity']), 5)
            rarity_and_mean.append({'rarity': pop_minus_20['rarity'],
                                    'mean': mean})

        self.__update_population_table(rarity_and_mean)  # Update Population Table

    def get_items_to_send(self, items):
        items_to_send = []

        for item in items:
            population_item = self.__get_item_population(item['population'])
            if (item['price'] < population_item['mean']) or (item['lastSell'] < population_item['mean']):
                items_to_send.append(item)

        return items_to_send


    def __update_population_table(self, populations):
        with data_base.atomic():
            Population.replace_many(populations, fields=[Population.rarity, Population.mean]).execute()

    def __get_total_mean_div_rarity(self, population_list):
        total = 0
        for population in population_list:
            total += population['mean']/population['rarity']

        return total

    def __get_item_population(self, item_population):
        for population in self.__populations:
            if item_population == population['rarity']:
                return population





