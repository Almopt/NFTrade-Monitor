import urllib3

from NFTradeMonitor.Script.Monitor import Monitor


def run():
    nft_monitor = Monitor()
    nft_monitor.start()


if __name__ == '__main__':
    urllib3.disable_warnings()
    run()