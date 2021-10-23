class NFT:

    def __init__(self, contract_address, token_id, image_url, price):
        self.__contractAddress = contract_address
        self.__tokenId = token_id
        self.__imageUrl = image_url
        self.__price = price