import requests
import json

import urllib3
from price import Price


class Exchange:
    def __init__(self, name, baseUrl):
        self.name = name
        self.baseUrl = baseUrl

    def getPriceFetchRoute(self, symbol):
        return self.baseUrl + symbol

    def getCoinListRoute(self):
        return self.baseUrl

    def prepSymbol(self, symbol):
        return symbol

    def unprepSymbol(self, symbol):
        return symbol

    # Returns a list of coin symbols as strings
    def getCoinList(self):
        print("Fetching coin list for " + self.name + "...")

        req = requests.get(self.getCoinListRoute())

        if req.status_code != 200:
            print("Error fetching exchange data: " + str(req.status_code))
            exit()

        coinList = self.handleCoinList(req)

        for i in range(len(coinList)):
            coinList[i] = self.unprepSymbol(coinList[i])

        return coinList

    def handleCoinList(self, req):
        # Parse JSON
        data = json.loads(req.text)

        return data

    def validateCoin(self, data):
        return True

    def fetchPrice(self, symbol):
        symbol = self.prepSymbol(symbol)

        try:
            req = requests.get(self.getPriceFetchRoute(symbol))
        except (requests.exceptions.ConnectionError, urllib3.exceptions.TimeoutError):
            print("Connection error fetching coin (" + symbol + ") from " + self.name)
            return None

        if req.status_code != 200:
            # print("Error fetching coin (" + symbol + ") from " + self.name + ": " + str(req.status_code))
            return None

        data = json.loads(req.text)
        return self.handlePrice(data)

    def handlePrice(self, data):
        return Price(self.name, data["price"])


def getExchangeList():
    if "exchanges" not in locals():
        exchanges = [Binance(), Coinbase()]
    return exchanges


# Exchanges
class Binance(Exchange):
    def __init__(self):
        super().__init__("Binance", "https://api.binance.us/api/v3/")

    def getPriceFetchRoute(self, symbol):
        return self.baseUrl + "ticker/price?symbol=" + symbol

    def getCoinListRoute(self):
        return self.baseUrl + "exchangeInfo"

    def handleCoinList(self, req):
        # Parse JSON
        data = json.loads(req.text)

        symbols = data["symbols"]
        newSymbols = []
        for symbol in symbols:
            if self.validateCoin(symbol):
                newSymbols.append(symbol["symbol"])

        return newSymbols

    def validateCoin(self, data):
        if data["quoteAsset"] == "USDT" and data["status"] == "TRADING":
            return True
        return False

    def prepSymbol(self, symbol):
        return symbol + "USDT"

    def unprepSymbol(self, symbol):
        return symbol[:-4]  # Remove USDT from the end


class Coinbase(Exchange):
    def __init__(self):
        super().__init__("Coinbase", "https://api.coinbase.com/v2/")

    def getPriceFetchRoute(self, symbol):
        return (
            self.baseUrl + "prices/" + symbol + "-usd/spot"
        )  # "exchange-rates?currency=" # buy and ask are also available

    def getCoinListRoute(self):
        return "https://api.exchange.coinbase.com/products"

    def handleCoinList(self, req):
        # Parse JSON
        data = json.loads(req.text)

        symbols = []
        for product in data:
            if product["quote_currency"] == "USD":
                symbols.append(product["base_currency"])

        return symbols

    def handlePrice(self, data):
        return Price(self.name, data["data"]["amount"])
