from peewee import DoubleField, CharField

from NFTradeMonitor.Script.DB.db import BaseModel


class Population(BaseModel):
    rarity = DoubleField(primary_key=True)
    mean = DoubleField(null=True)

    class Meta:
        table_name = 'Population'
