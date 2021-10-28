from peewee import CharField, IntegerField, DoubleField, CompositeKey, ForeignKeyField, DateField, TimeField

from NFTradeMonitor.Script.DB.Schemas.Population import Population
from NFTradeMonitor.Script.DB.db import BaseModel


class NFT(BaseModel):
    contractAddress = CharField()
    tokenId = CharField()
    tokenURI = CharField()
    imageUrl = CharField()
    price = CharField()
    lastSell = DoubleField(null=True)
    updatedAtDate = DateField()
    updatedAtHour = TimeField()
    url = CharField()  # https://app.nftrade.com/assets/bsc/0x85f0e02cb992aa1f9f47112f815f519ef1a59e2d/10000131707
    horn_prob = DoubleField()
    color_prob = DoubleField()
    background_prob = DoubleField()
    glitter_prob = DoubleField()
    type_prob = DoubleField()
    type = CharField()
    horn = CharField()
    color = CharField()
    background = CharField()
    open_network = CharField()
    glitter = CharField()
    special = CharField()
    population = ForeignKeyField(Population, backref='nfts')

    class Meta:
        primary_key = CompositeKey('contractAddress', 'tokenId')
        table_name = 'NFTs'