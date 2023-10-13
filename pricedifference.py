from datetime import timedelta
from globals import minPriceDiff, maxPriceDiff


class PriceDifference:
    def __init__(self, symbol, buy, sell):
        self.symbol = symbol
        self.buy = buy
        self.sell = sell

        self.startTime = None
        self.lastTime = None

    def getDiff(self) -> float:
        return self.sell.getSellPrice() - self.buy.getBuyPrice()

    def getDiffPercent(self) -> float:
        return self.getDiff() / self.buy.getBuyPrice()

    def getId(self) -> str:
        return self.symbol + "-" + self.buy.exchangeName + "-" + self.sell.exchangeName

    def isValid(self) -> bool:
        percent = self.getDiffPercent()
        return percent >= minPriceDiff and percent <= maxPriceDiff

    def getTimeDelta(self) -> timedelta:
        if self.lastTime is None or self.startTime is None:
            return None
        return self.lastTime - self.startTime

    def __str__(self):
        return (
            self.symbol
            + ": "
            + self.buy.exchangeName
            + ": "
            + str(self.buy.getBuyPrice())
            + " / "
            + self.sell.exchangeName
            + ": "
            + str(self.sell.getSellPrice())
            + " / "
            + str(self.getDiff())
            + " ("
            + str(round(self.getDiffPercent(), 5) * 100)
            + "%)"
            + " Time: "
            + str(self.getTimeDelta())
        )
