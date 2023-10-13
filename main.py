import time as timeModule
from datetime import timedelta
from queue import Queue
from threading import Thread
from coin import Coin
from exchange import getExchangeList
from globals import threadCount, coinDifferences, currentIteration


# Threaded HTTP requests
def fetchData():
    global queue, invalidCoins, currentIteration

    try:
        while True:
            coin = queue.get()

            for exchange in getExchangeList():
                price = exchange.fetchPrice(coin.symbol)
                if price is not None:
                    coin.prices[exchange.name] = price

            if coin.isValid():
                diff = coin.getPriceDiff()

                diff = coin.onFetch(
                    diff
                )  # Modifications to diff in onFetch() do not seem to automatically aply

                if diff is not None and diff.isValid():
                    currentDiffs[diff.getId()] = diff.getTimeDelta()
            else:
                invalidCoins.append(coin)
            queue.task_done()
    except Exception as ex:
        print("Error in thread: " + str(ex))
        exit()


symbols = []
for exchange in getExchangeList():
    coins = exchange.getCoinList()
    for coin in coins:
        symbols.append(coin)

print("Symbols (to USD or USDT): " + str(len(symbols)))

# Create Coin objects
coins = {}
for symbol in symbols:
    if symbol not in coins:
        coins[symbol] = Coin(symbol)
    else:
        coins[symbol].exchangeCount += 1

coins = list(coins.values())

# Remove invalid coins
print("Validating coins...")
invalidCoins = []
for coin in coins:
    if coin.exchangeCount < 2:
        invalidCoins.append(coin)

print("Removing " + str(len(invalidCoins)) + " invalid coins...")
for coin in invalidCoins:
    coins.remove(coin)

invalidCoins = []  # Reset so we can use again later

print("Fetching data for " + str(len(coins)) + " coins...")

# Create variables that threads use
queue = Queue()
prevDiffs = {}  # Stored as {symbol: TimeDelta}
currentDiffs = {}  # Stored as {symbol: TimeDelta}
diffTimes = []

# Create threads
threads = []
for i in range(threadCount):
    thread = Thread(target=fetchData)
    thread.daemon = True  # Stops the thread when the main thread ends
    thread.start()
    threads.append(thread)


def finishIteration(final=False):
    global timeModule
    timeModule.sleep(0.5)

    global prevDiffs, currentDiffs, diffTimes

    # Compare current and prev diffs

    # Update times for continuing diffs and remove finished diffs
    toRemove = []
    for diff, time in prevDiffs.items():
        if final or diff not in currentDiffs.keys():
            print("Closing diff:", diff, "Time:", time)
            diffTimes.append(time)
            toRemove.append(diff)

    print("Differences Removed:", str(len(toRemove)))
    for diff in toRemove:
        del prevDiffs[diff]

    # Add new diffs
    for diff, time in currentDiffs.items():
        if diff not in prevDiffs:
            print("Opening diff: " + diff)
        prevDiffs[diff] = time

    print("Current Differences Found:", str(len(currentDiffs)))
    print("Total Closed Differences:", str(len(diffTimes)))

    currentDiffs = {}


while True:
    try:
        currentIteration += 1
        print(
            "-" * 20
            + "\nStarting iteration "
            + str(currentIteration)
            + "...\n"
            + "-" * 20
        )

        # Add coins to queue
        for coin in coins:
            queue.put(coin)

        # Wait for queue to be empty
        while not queue.empty():
            pass

        finishIteration()

    except KeyboardInterrupt:
        print("Keyboard interrupt detected, ending program...")
        finishIteration(True)
        break

# Find avg time
if len(diffTimes) == 0:
    print("No differences found")
    exit()

avgTime = 0
for time in diffTimes:
    if time is not None:
        avgTime += time.total_seconds()
avgTime /= len(diffTimes)

print("Average Time: " + str(timedelta(seconds=avgTime)))
