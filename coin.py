import requests
import json
from price import Price

class Coin:
    # We can't have multiple constructors in Python, so we'll use a flag
    def __init__(self, data):
        self.symbol = data
        self.exchangeCount = 1
        self.prices = {}
    
    def isValid(self):
        return hasattr(self, "prices")

    # Returns the lowest buy price available on all exchanges we found
    def getMinBuyPrice(self):
      if self.isValid():
        minPrice = float("inf")
        for price in self.prices.values():
          if price.isValid():
            minPrice = min(minPrice, price.getBuyPrice())
        return minPrice
      return None

    # Returns the highest sell price available on all exchanges we found
    def getMaxSellPrice(self):
      if self.isValid():
        maxPrice = float("-inf")
        for price in self.prices.values():
          if price.isValid():
            maxPrice = max(maxPrice, price.getSellPrice())
        return maxPrice
      return None

    # Returns sell price minus buy price
    def getPriceDiff(self, buy = -1.0, sell = -1.0):
      if buy == -1.0:
        buy = self.getMinBuyPrice()
      if sell == -1.0:
        sell = self.getMaxSellPrice()

      if buy is None or sell is None:
        return 0

      return float(sell) - float(buy)
    
    def __str__(self):
        if self.isValid():
            msg = self.symbol + ": "

            # Min Buy / Max Sell
            buy = self.getMinBuyPrice()
            sell = self.getMaxSellPrice()
            if buy is not None and sell is not None:
              diff = self.getPriceDiff(buy, sell)
              msg += str(buy) + " / " + str(sell) + " / " + str(diff)
          
            # Exchange prices
            for price in self.prices.values():
                msg += str(price)
              
            return msg
        else:
            return self.symbol