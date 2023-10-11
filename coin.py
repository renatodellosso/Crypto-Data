import requests
import json
from price import Price
from config import priceDiffThreshold
from pricedifference import PriceDifference


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
            minPrice = None
            for price in self.prices.values():
                if (price.isValid() and minPrice is None) or (
                    minPrice is not None
                    and minPrice.getBuyPrice() > price.getBuyPrice()
                ):
                    minPrice = price
            return minPrice
        return None

    # Returns the highest sell price available on all exchanges we found
    def getMaxSellPrice(self):
        if self.isValid():
            maxPrice = None
            for price in self.prices.values():
                if (price.isValid() and maxPrice is None) or (
                    maxPrice is not None
                    and maxPrice.getSellPrice() < price.getSellPrice()
                ):
                    maxPrice = price
            return maxPrice
        return None

    # Returns sell price minus buy price
    def getPriceDiff(self, buy=-1.0, sell=-1.0):
        if buy == -1.0:
            buy = self.getMinBuyPrice()
        if sell == -1.0:
            sell = self.getMaxSellPrice()

        if buy is None or sell is None:
            return 0

        return PriceDifference(buy, sell)

    def __str__(self):
        if self.isValid():
            msg = self.symbol + ": "

            # Min Buy / Max Sell
            buy = self.getMinBuyPrice()
            sell = self.getMaxSellPrice()
            if buy is not None and sell is not None:
                diff = self.getPriceDiff(buy, sell)
                if diff.getDiff() > 0:
                    msg += str(diff)

            # Exchange prices
            for price in self.prices.values():
                msg += str(price)

            return msg
        else:
            return self.symbol

    def onFetch(self):
        # Check if price difference is above threshold
        global priceDiffThreshold
        diff = self.getPriceDiff()
        if diff.getDiffPercent() > priceDiffThreshold:
            self.onDiffFound(diff)

    def onDiffFound(self, diff):
        print(self)
