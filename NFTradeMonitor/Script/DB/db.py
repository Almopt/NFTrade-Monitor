from peewee import *

data_base = SqliteDatabase('NFTrade.db')


class BaseModel(Model):
    class Meta:
        database = data_base
