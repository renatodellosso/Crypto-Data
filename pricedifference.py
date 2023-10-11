class PriceDifference:
    def __init__(self, buy, sell):
        self.buy = buy
        self.sell = sell

    def getDiff(self):
        return self.sell.getSellPrice() - self.buy.getBuyPrice()

    def getDiffPercent(self):
        return self.getDiff() / self.buy.getBuyPrice()

    def __str__(self):
        return (
            self.buy.exchangeName
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
        )
