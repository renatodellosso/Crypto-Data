import datetime
from price import Price
from globals import minPriceDiff, maxPriceDiff, coinDifferences, diffTimeThreshold
from pricedifference import PriceDifference


class Coin:
    # We can't have multiple constructors in Python, so we'll use a flag
    def __init__(self, data):
        self.symbol = data
        self.exchangeCount = 1
        self.prices = {}

    def isValid(self) -> bool:
        return hasattr(self, "prices")

    # Returns the lowest buy price available on all exchanges we found
    def getMinBuyPrice(self) -> Price:
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
    def getMaxSellPrice(self) -> Price:
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
    def getPriceDiff(self, buy=-1.0, sell=-1.0) -> PriceDifference:
        if buy == -1.0:
            buy = self.getMinBuyPrice()
        if sell == -1.0:
            sell = self.getMaxSellPrice()

        if buy is None or sell is None:
            return 0

        return PriceDifference(self.symbol, buy, sell)

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

    def onFetch(self, diff: PriceDifference = None) -> PriceDifference:
        # Check if price difference is above threshold
        global minPriceDiff, maxPriceDiff
        diff = self.getPriceDiff()
        if diff is not None and diff.isValid():
            return self.onDiffFound(diff)
        return None

    def onDiffFound(self, diff: PriceDifference) -> PriceDifference:
        global coinDifferences, diffTimeThreshold

        # Update coinDifferences
        # Set times
        diff.lastTime = datetime.datetime.now()
        if diff.getId() in coinDifferences:
            prevDiff = coinDifferences[diff.getId()]
            if prevDiff.lastTime - diff.lastTime < datetime.timedelta(
                seconds=diffTimeThreshold
            ):
                diff.startTime = prevDiff.startTime
            else:
                diff.startTime = diff.lastTime
        else:
            diff.startTime = diff.lastTime

        coinDifferences[diff.getId()] = diff

        print(diff)
        # print(self)

        return diff
