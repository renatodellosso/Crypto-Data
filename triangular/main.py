import requests
import json
import matplotlib.pyplot as plot
from coin import Coin

# Config
ignoredSymbols = ["USDC", "BUSD", "WBTC"]
minMargin = 1.002
maxMargin = 1.1


def fetchPrice(paySymbol: str, buySymbol: str) -> float:
    req = requests.get(
        "https://api.binance.us/api/v3/ticker/price?symbol=" + buySymbol + paySymbol
    )
    if req.status_code == 400:
        return 1 / fetchPrice(buySymbol, paySymbol)
    elif req.status_code != 200:
        return None
    data = json.loads(req.text)
    return 1 / float(data["price"])


def calcTriangular(firstSymbol: str, secondSymbol: str) -> float:
    print("Calculating " + firstSymbol + " " + secondSymbol)
    return (
        fetchPrice("USDT", firstSymbol)
        * fetchPrice(firstSymbol, secondSymbol)
        * fetchPrice(secondSymbol, "USDT")
    )


def filter(symbols: list, condition: lambda x: bool) -> list:
    return [x for x in symbols if condition(x)]


req = requests.get("https://api.binance.us/api/v3/exchangeInfo?permissions=SPOT")
data = json.loads(req.text)


# Find valid symbols
symbols = data["symbols"]
# Filter to symbols that are trading and that are not ignored
symbols = filter(
    symbols,
    lambda x: x["status"] == "TRADING"
    and not any([x["baseAsset"] in ignoredSymbols, x["quoteAsset"] in ignoredSymbols]),
)

# Filter to symbols that are priced in USDT
endpoints = filter(symbols, lambda x: x["quoteAsset"] == "USDT")
symbols = filter(symbols, lambda x: x["quoteAsset"] != "USDT")
coins = dict(
    (x["baseAsset"], Coin(x["baseAsset"])) for x in endpoints
)  # This syntax is called dictionary comprehension

# Find midpoints of triangles
# Loop through symbols to find pairs where one symbol matches an endpoint
triangles = []
for endpoint in endpoints:
    symbol = endpoint["baseAsset"]
    for coin in symbols:
        if coin["baseAsset"] == symbol or coin["quoteAsset"] == symbol:
            # If we find a match, add the midpoint to the list of coins
            triangles.append((coin["baseAsset"], coin["quoteAsset"]))

# Calculate triangular arbitrage
triangleData = dict((x, calcTriangular(x[0], x[1])) for x in triangles)

print(
    "Triangles: "
    + str(len(triangleData.keys()))
    + " "
    + str(len(triangleData.values()))
)

subplot = plot.subplots()[1]
subplot.add_line(plot.Line2D([0, len(triangleData.keys())], [1, 1]))
subplot.add_line(plot.Line2D([0, len(triangleData.keys())], [minMargin, minMargin]))
subplot.add_line(plot.Line2D([0, len(triangleData.keys())], [maxMargin, maxMargin]))
subplot.scatter([str(x) for x in triangleData.keys()], triangleData.values())

# Filter to triangles with a margin between minMargin and maxMargin
triangleData = dict(
    (symbols, value)
    for symbols, value in triangleData.items()
    if value > minMargin and value < maxMargin
)

# Log all triangles
print("Triangles:")
for triangle, value in triangleData.items():
    print(triangle, value)

plot.show()
