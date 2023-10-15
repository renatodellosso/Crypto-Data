from datetime import datetime, timedelta
from queue import Queue
import requests
import json
import threading
import time
from coin import Coin

# Config
ignoredSymbols = ["USDC", "BUSD", "WBTC"]
minMargin = 1.0022  # Binance charges 0.1% fee, so this is roughly the minimum margin to break even
maxMargin = 1.1
threads = 16


def fetchPrice(paySymbol: str, buySymbol: str) -> float:
    try:
        req = requests.get(
            "https://api.binance.us/api/v3/ticker/price?symbol=" + buySymbol + paySymbol
        )
    except TimeoutError:
        print("Request timed out while fetching", paySymbol, buySymbol)
        return None
    if req.status_code == 400:
        price = fetchPrice(paySymbol, buySymbol)
        if price is None:
            return None
        return 1 / price
    elif req.status_code != 200:
        return None

    data = json.loads(req.text)
    return 1 / float(data["price"])


def calcTriangular(firstSymbol: str, secondSymbol: str) -> float:
    # print("Calculating " + firstSymbol + " " + secondSymbol)

    prices = [
        fetchPrice("USDT", firstSymbol),
        fetchPrice(firstSymbol, secondSymbol),
        fetchPrice(secondSymbol, "USDT"),
    ]

    if None in prices:
        return None
    return prices[0] * prices[1] * prices[2]


def filter(symbols: list, condition: lambda x: bool) -> list:
    return [x for x in symbols if condition(x)]


def fetchThread():
    # Calculate triangular arbitrage for all triangles in fetchQueue and add it to triangleData
    global fetchQueue, triangleData
    while True:
        try:
            triangle = fetchQueue.get()
            triangleData[triangle] = calcTriangular(triangle[0], triangle[1])
            fetchQueue.task_done()
        except Exception as e:
            print("Error:", e)
            exit()


def findTriangles():
    print("Fetching symbols...")
    req = requests.get("https://api.binance.us/api/v3/exchangeInfo?permissions=SPOT")

    if req.status_code != 200:
        print("Error fetching symbols. Status code:", req.status_code)
        if req.status_code == 418 or req.status_code == 429:
            print("WARNING: We are being rate limited")
            waitTime = int(req.headers["Retry-After"])
            print("Waiting", waitTime, "seconds...")
            time.sleep(waitTime)
            print("Wait finished!")
        else:
            return

    data = json.loads(req.text)

    if "symbols" not in data:
        print("Error fetching symbols: 'symbols' not in data")
        return

    print("Filtering out invalid symbols...")
    # Find valid symbols
    symbols = data["symbols"]
    # Filter to symbols that are trading and that are not ignored
    symbols = filter(
        symbols,
        lambda x: x["status"] == "TRADING"
        and not any(
            [x["baseAsset"] in ignoredSymbols, x["quoteAsset"] in ignoredSymbols]
        ),
    )

    print("Filtering out non-USDT symbols...")

    # Filter to symbols that are priced in USDT
    endpoints = filter(symbols, lambda x: x["quoteAsset"] == "USDT")
    symbols = filter(symbols, lambda x: x["quoteAsset"] != "USDT")

    # Find midpoints of triangles
    # Loop through symbols to find pairs where one symbol matches an endpoint
    print("Finding triangles...")
    triangles = []
    for endpoint in endpoints:
        symbol = endpoint["baseAsset"]
        for coin in symbols:
            if coin["baseAsset"] == symbol or coin["quoteAsset"] == symbol:
                # If we find a match, add the midpoint to the list of coins
                triangles.append((coin["baseAsset"], coin["quoteAsset"]))

    # Add triangles to fetchQueue
    global fetchQueue
    for triangle in triangles:
        fetchQueue.put(triangle)

    # Wait for all threads to finish
    while fetchQueue.qsize() > 0:
        pass

    global triangleData

    localTriData = (
        triangleData.copy()
    )  # Create a copy to avoid errors with multithreading

    # Filter to triangles with a margin between minMargin and maxMargin
    localTriData = dict(
        (symbols, value)
        for symbols, value in localTriData.items()
        if value is not None and value > minMargin and value < maxMargin
    )

    # Log all triangles
    print("Triangles:")
    for triangle, value in localTriData.items():
        print(triangle, value)

    triangleData = localTriData  # Update triangleData


def startIteration():
    global startTime
    startTime = datetime.now()

    triangleData.clear()


def finishIteration(final: bool = False):
    global startTime, currentTimes
    timeTaken = datetime.now() - startTime

    for triangle in triangleData.keys():
        if triangle in currentTimes:
            currentTimes[triangle] += timeTaken
        else:
            currentTimes[triangle] = timeTaken

    trianglesToRemove = []
    for triangle in currentTimes.keys():
        if final or triangle not in triangleData:
            trianglesToRemove.append(triangle)

    print("Removing triangles:", len(trianglesToRemove))

    for triangle in trianglesToRemove:
        allTimes.append(currentTimes[triangle])
        currentTimes.pop(triangle)

    timeTaken = datetime.now() - startTime
    print("Time taken: " + str(timeTaken))


# Set up variables for threads
fetchQueue = Queue()
triangleData = dict()
currentTimes = dict()
allTimes = []

# Create threads
for i in range(threads):
    threading.Thread(target=fetchThread, daemon=True).start()

# Main loop
while True:
    try:
        startIteration()
        findTriangles()
        time.sleep(1)
        finishIteration()
    except (
        KeyboardInterrupt
    ):  # Not technically necessary, but it reduces the amount of errors printed to the console
        finishIteration(True)
        break

# Print results
# Print average time taken for each triangle
if any(allTimes):
    avgTime = 0
    for time in allTimes:
        avgTime += time.total_seconds()
    avgTime /= len(allTimes)
    print("Avg Time Open: ", timedelta(seconds=avgTime))
