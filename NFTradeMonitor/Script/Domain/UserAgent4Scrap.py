from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, HardwareType


class UserAgent4Scrap:

    def __init__(self):
        self.__software_names = [SoftwareName.CHROME.value]
        self.__hardware_type = [HardwareType.MOBILE__PHONE, HardwareType.COMPUTER]
        self.__user_agent_rotator = UserAgent(software_names=self.__software_names, hardware_type=self.__hardware_type)

    def get_random_user_agent(self):
        return {'User-Agent': self.__user_agent_rotator.get_random_user_agent(),
                'accept': 'application/json, text/plain, */*',
                'accept-encoding': 'gzip, deflate, br',
                'accept-language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7'}