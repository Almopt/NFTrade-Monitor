from peewee import CharField, IntegerField, DoubleField, CompositeKey, ForeignKeyField, DateField, TimeField

from NFTradeMonitor.Script.DB.Schemas.Population import Population
from NFTradeMonitor.Script.DB.db import BaseModel


class NFT(BaseModel):
    contractAddress = CharField()
    tokenId = CharField()
    tokenURI = CharField()
    imageUrl = CharField(null=True)
    price = CharField(null=True)
    lastSell = DoubleField(null=True)
    updatedAtDate = DateField()
    updatedAtHour = TimeField()
    url = CharField()  # https://app.nftrade.com/assets/bsc/0x85f0e02cb992aa1f9f47112f815f519ef1a59e2d/10000131707
    horn_prob = DoubleField(default=0)
    color_prob = DoubleField(default=0)
    background_prob = DoubleField(default=0)
    glitter_prob = DoubleField(default=0)
    type_prob = DoubleField(default=0)
    type = CharField(null=True)
    horn = CharField(null=True)
    color = CharField(null=True)
    background = CharField(null=True)
    open_network = CharField(null=True)
    glitter = CharField(null=True)
    special = CharField(null=True)
    population = ForeignKeyField(Population, backref='nfts')

    class Meta:
        primary_key = CompositeKey('contractAddress', 'tokenId')
        table_name = 'NFTs'