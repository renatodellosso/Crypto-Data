import requests
import json
from price import Price

class Coin:
    # We can't have multiple constructors in Python, so we'll use a flag
    def __init__(self, data, isJson = True):
        if isJson:
            self.setDataFromJson(data)
        else:
            self.symbol = data
    
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