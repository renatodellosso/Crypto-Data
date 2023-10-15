class Coin:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.prices = {}

    def __str__(self) -> str:
        msg = self.symbol + ": "
        for symbol, price in self.prices.items():
            msg += "\n\t" + symbol + ": " + str(price)
        return msg
