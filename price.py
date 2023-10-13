class Price:
    # If no ask is provided, we assume it's a single price
    def __init__(self, exchangeName: str, bid: float, ask=-1):
        self.exchangeName = exchangeName
        self.bid = float(bid)
        if float(ask) > -1:
            self.ask = float(ask)

    def spread(self) -> float:
        if hasattr(self, "ask"):
            return self.ask - self.bid
        return 0

    def isValid(self) -> bool:
        return self.bid > 0

    # To be safe, we use the ask price to estimate buying costs
    def getBuyPrice(self) -> float:
        if hasattr(self, "ask"):
            return self.ask
        return self.bid

    # To be safe, we use the bid price to estimate sell value
    def getSellPrice(self) -> float:
        return self.bid

    def __str__(self):
        msg = "\n\t" + self.exchangeName + " - "

        if hasattr(self, "ask"):
            msg += (
                "B: "
                + str(self.bid)
                + ", A: "
                + str(self.ask)
                + ", S: "
                + str(self.spread())
            )
        else:
            msg += "P: " + str(self.bid)

        return msg
