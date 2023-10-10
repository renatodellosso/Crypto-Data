class Price:
    # If no ask is provided, we assume it's a single price
    def __init__(self, bid, ask = -1):
        self.bid = float(bid)
        if float(ask) > -1:
            self.ask = float(ask)

    def spread(self):
        if hasattr(self, "ask"):
            return self.ask - self.bid
        return 0
    
    def isValid(self):
        return self.bid > 0

    def __str__(self):
        if hasattr(self, "ask"):
            return "B: " + str(self.bid) + ", A: " + str(self.ask) + ", S: " + str(self.spread())
        return "P: " + str(self.bid)
