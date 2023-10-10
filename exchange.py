import requests
import json
from price import Price

class Exchange:
    def __init__(self, name, baseUrl):
        self.name = name
        self.baseUrl = baseUrl

    def getPriceFetchRoute(self):
        return self.baseUrl
    
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

        symbols = data['symbols']
        newSymbols = []
        for symbol in symbols:
            if symbol['quoteAsset'] == 'USDT':
                newSymbols.append(symbol["symbol"])

        return newSymbols

    def fetchPrice(self, symbol):
        symbol = self.prepSymbol(symbol)

        req = requests.get(self.getPriceFetchRoute() + symbol)
        
        if req.status_code != 200:
            # print("Error fetching coin (" + symbol + ") from " + self.name + ": " + str(req.status_code))
            return None
        
        data = json.loads(req.text)
        return self.handlePrice(data)

    def handlePrice(self, data):
        return Price(self.name, data['bidPrice'], data['askPrice'])

def getExchangeList():
    return [Binance(), Coinbase()]

# Exchanges
class Binance(Exchange):
    def __init__(self):
        super().__init__("Binance", "https://api.binance.us/api/v3/")

    def getPriceFetchRoute(self):
        return self.baseUrl + "ticker/24hr?symbol="
    
    def getCoinListRoute(self):
        return self.baseUrl + "exchangeInfo"
    
    def prepSymbol(self, symbol):
        return symbol + "USDT"
    
    def unprepSymbol(self, symbol):
        return symbol[:-4] # Remove USDT from the end
    
class Coinbase(Exchange):
    def __init__(self):
        super().__init__("Coinbase", "https://api.coinbase.com/v2/")

    def getPriceFetchRoute(self):
        return self.baseUrl + "exchange-rates?currency="
    
    def getCoinListRoute(self):
        return "https://api.exchange.coinbase.com/products"
    
    def handleCoinList(self, req):
        # Parse JSON
        data = json.loads(req.text)

        symbols = []
        for product in data:
            if product['quote_currency'] == 'USD':
                symbols.append(product['base_currency'])

        return symbols
    
    def handlePrice(self, data):
        rates = data['data']['rates']
        if 'USD' not in rates:
            return None
        return Price(self.name, rates['USD'])