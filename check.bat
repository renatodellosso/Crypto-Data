@echo off

set symbol=%1%

echo Checking %symbol%...

set binance=https://api.binance.us/api/v3/ticker/price?symbol=%symbol%USDT
echo Curling %binance% ...
curl %binance%

set coinbase=https://api.coinbase.com/v2/prices/%symbol%-usd/spot
echo.
echo Curling %coinbase% ...
curl %coinbase%