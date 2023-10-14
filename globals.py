# Config
threadCount: int = 16
minPriceDiff: float = 0.02  # Out of 1
maxPriceDiff: float = 0.2  # Out of 1
diffTimeThreshold: int = 60  # Seconds

# Global variables
currentIteration: int = 0
coinDifferences: dict = {}  # Structured as {symbol: PriceDifference}
