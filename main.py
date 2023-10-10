# Importing libraries
print("Importing libraries...")
import requests
import json
from queue import Queue
from threading import Thread
from coin import Coin
from exchange import getExchangeList

# Config
threadCount = 8
exchanges = getExchangeList()

# Threaded HTTP requests
def fetchData():
    global queue, invalidCoins

    while True:
        coin = queue.get()

        for exchange in exchanges:
            price = exchange.fetchPrice(coin.symbol)
            if price != None:
                coin.prices[exchange.name] = price

        if(coin.isValid()):
            print(coin)
        else:
            invalidCoins.append(coin)
        queue.task_done()

symbols = []
for exchange in exchanges:
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
  
invalidCoins = [] # Reset so we can use again later

print("Fetching data for " + str(len(coins)) + " coins...")

queue = Queue()

# Add coins to queue
for coin in coins:
    queue.put(coin)

# Create threads
threads = []
for i in range(threadCount):
    thread = Thread(target=fetchData)
    thread.daemon = True # Stops the thread when the main thread ends
    thread.start()
    threads.append(thread)

# Wait for queue to be empty
while not queue.empty():
    pass

# Remove invalid coins
print("Invalid coins: " + str(len(invalidCoins)))
for coin in invalidCoins:
    coins.remove(coin)