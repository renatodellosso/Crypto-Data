from datetime import datetime, timedelta
from queue import Queue
import requests
import json
import threading
import time

import urllib3

# Config
ignoredSymbols = ["USDC", "BUSD", "WBTC"]
# 0.1% fee on each trade, and we want to make at least 0.1% profit
minMargin = 1.001**3 + 0.001
maxMargin = 1.1
threads = 3
pauseFetches = False
fetchesRemainingLogInterval = 3


def fetch(url: str, expectedErrorCodes=list()) -> requests.Response:
    global pauseFetches

    # print("Fetching", url)

    while pauseFetches:
        time.sleep(0.1)

    try:
        req = requests.get(url)
    except TimeoutError:
        print("Request timed out while fetching", url)
        return None
    except urllib3.exceptions.MaxRetryError:
        print("Connection pool error while fetching", url)
        return None

    if req.status_code != 200 and req.status_code not in expectedErrorCodes:
        print("Error fetching. Status code:", req.status_code, "/ URL:", url)
        if req.status_code == 418 or req.status_code == 429:
            print("WARNING: We are being rate limited")
            waitTime = int(req.headers["Retry-After"])
            print("Waiting", waitTime, "seconds...")

            pauseFetches = True
            time.sleep(waitTime)
            pauseFetches = False

            print("Wait finished!")
            return fetch(url, expectedErrorCodes)
        else:
            return

    return req


def fetchPrice(paySymbol: str, buySymbol: str) -> float:
    req = fetch(
        "https://api.binance.us/api/v3/ticker/price?symbol=" + buySymbol + paySymbol,
        [400],
    )

    if req is not None:
        data = json.loads(req.text)

    if req is None or req.status_code == 400 or "price" not in data:
        price = fetchPrice(buySymbol, paySymbol)
        if price is None:
            return None
        return 1 / price

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

            time.sleep(0.2)
        except Exception as e:
            print("Error:", e)
            exit()


def fetchTriangleList():
    global triangles, ignoredSymbols

    print("Fetching symbols...")

    req = fetch("https://api.binance.us/api/v3/exchangeInfo")
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
                print("Found triangle:", coin["baseAsset"], coin["quoteAsset"])
                # If we find a match, add the midpoint to the list of coins
                triangles.append((coin["baseAsset"], coin["quoteAsset"]))
    print("Found triangles:", len(triangles))


def findTriangles():
    # Add triangles to fetchQueue
    global fetchQueue, triangles, fetchesRemainingLogInterval

    print("Fetching prices for", len(triangles), "triangles...")

    for triangle in triangles:
        fetchQueue.put(triangle)

    # Wait for all threads to finish
    print("Waiting for threads to finish...")
    while fetchQueue.qsize() > 0:
        for i in range(int(fetchesRemainingLogInterval / 0.1)):
            if fetchQueue.qsize() == 0:
                break
            time.sleep(0.1)
        print("Fetches remaining:", fetchQueue.qsize())
    print("Threads finished!")

    # Filter to triangles with a margin between minMargin and maxMargin
    global triangleData
    triangleData = dict(
        (symbols, value)
        for symbols, value in triangleData.items()
        if value is not None and value > minMargin and value < maxMargin
    )


def startIteration():
    print("Starting iteration...")

    global startTime
    startTime = datetime.now()

    triangleData.clear()


def finishIteration(final: bool = False):
    print("Finishing iteration...")

    global triangleData

    # Refilter triangles, just to be safe. We were running into an issue with invalid triangles, so we filter again
    triangleData = dict(
        (symbols, value)
        for symbols, value in triangleData.items()
        if value is not None and value > minMargin and value < maxMargin
    )

    # Log all triangles
    print("Triangles:", len(triangleData))
    for triangle, value in triangleData.items():
        print(triangle, value)

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


fetchTriangleList()

# Set up variables for threads
fetchQueue = Queue()
triangleData = dict()
currentTimes = dict()
allTimes = []

# Create threads
print("Starting threads...")
for i in range(threads):
    threading.Thread(target=fetchThread, daemon=True).start()

# Main loop
print("Starting main loop...")
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
