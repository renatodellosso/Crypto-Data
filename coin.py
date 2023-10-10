import requests
import json
from price import Price

class Coin:
    # We can't have multiple constructors in Python, so we'll use a flag
    def __init__(self, data):
        self.symbol = data
        self.exchangeCount = 1
    
    def isValid(self):
        return hasattr(self, "prices")
    
    def __str__(self):
        if self.isValid():
            msg = self.symbol + " - "
            for price in self.prices:
                msg += str(price) + ", "
            return msg[:-2]
        else:
            return self.symbol