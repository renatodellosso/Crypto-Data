symbol=$1

echo "Checking $symbol..."

binance="https://api.binance.us/api/v3/ticker/price?symbol=${symbol}USDT"
echo "Curling $binance ..."
curl $binance

coinbase="https://api.coinbase.com/v2/prices/${symbol}-usd/spot"
echo "Curling $coinbase ..."
curl $coinbase