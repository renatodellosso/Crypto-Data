import time as timeModule
from datetime import timedelta
from queue import Queue
from threading import Thread
from coin import Coin
from exchange import getExchangeList
from globals import threadCount, currentIteration


# Threaded HTTP requests
def fetchData():
    global queue, invalidCoins, currentIteration

    try:
        while True:
            coin = queue.get()

            # Get the price for the coin from each exchange
            for exchange in getExchangeList():
                price = exchange.fetchPrice(coin.symbol)
                if price is not None:
                    coin.prices[exchange.name] = price

            # If we have enough data to make calculations
            if coin.isValid():
                # Calculate the maximum price difference
                diff = coin.getPriceDiff()

                # Perform any additional calculations
                diff = coin.onFetch(diff)

                # If the price difference is valid
                if diff is not None and diff.isValid():
                    # Record the difference in price
                    currentDiffs[diff.getId()] = diff.getTimeDelta()
            else:
                # If we don't have enough data, log the coin as invalid
                invalidCoins.append(coin)
            queue.task_done()
    except Exception as ex:
        # Log any exceptions
        print("Error in thread: " + str(ex))
        exit()


# Get the list of all coins from all exchanges
symbols = []
for exchange in getExchangeList():
    # Get the list of coins for an exchange
    coins = exchange.getCoinList()
    # Add each coin to the list of all symbols
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


# Main loop
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
if len(diffTimes) == 0:  # If there are no diffTimes
    print("No differences found")  # Print that no differences were found
    exit()  # Exit the program

avgTime = 0  # Create a variable called avgTime and set it to 0
for time in diffTimes:  # For every time in the diffTimes list
    if time is not None:  # If time is not None
        avgTime += time.total_seconds()  # Add the total seconds of time to avgTime
avgTime /= len(diffTimes)  # Divide avgTime by the length of diffTimes

print("Average Time: " + str(timedelta(seconds=avgTime)))  # Print the average time
