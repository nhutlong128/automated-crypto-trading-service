# automated-crypto-trading-service

# Add config files
Add your config files into /user_data/configs

# Add new strategies
Put your new strategies into /user_data/strategies

# Download historical data
Run the command below
```
docker-compose run --rm freqtrade download-data --user-data-dir /freqtrade/user_data --datadir /freqtrade/user_data/data/{EXCHANGE_PLATFORM}/{FOLDER_TO_GET_DOWNLOADED_DATA} --config /freqtrade/user_data/configs/{CONFIG_FILE} --timerange {TIME_RANGE} --exchange {EXCHANGE_PLATFORM}
--pairs-file {FILE}
```
Example
```
docker-compose run --rm freqtrade download-data --user-data-dir /freqtrade/user_data --datadir /freqtrade/user_data/data/binance/ --config /freqtrade/user_data/configs/local-nhutlong128-baseline-config.json --timerange 20200101- --exchange binance --pairs-file /freqtrade/user_data/data/tradable_binance_pair_list.json -t 1d
```

# Perform backtesting strategies on historical data
Run the command below
```
docker-compose run --rm freqtrade backtesting --user-data-dir /freqtrade/user_data --config /freqtrade/user_data/configs/local-nhutlong128-baseline-config.json --timerange 20220401-20220410 --datadir /freqtrade/user_data/data/binance --strategy NostalgiaForInfinityX
```

# Tune parameters from config and strategy files
Run the command below
```
docker-compose run --rm freqtrade hyperopt --user-data-dir /freqtrade/user_data --config /freqtrade/user_data/configs/local-nhutlong128-baseline-config.json --timerange 20210101-20211231 --datadir /freqtrade/user_data/data/binance/ --strategy RSI_Keltner_Channel --hyperopt-loss SharpeHyperOptLossDaily --job-workers -1 --epochs 100 --print-all
```

# Perform backtesting strategies on latest historical data
Run the command below
```
docker-compose run --rm freqtrade backtesting --user-data-dir /freqtrade/user_data --config /freqtrade/user_data/configs/local-nhutlong128-baseline-config.json --timerange 20220101-20220401 --datadir /freqtrade/user_data/data/binance --strategy RSI_Keltner_Channel
```

# Plot indicator and buy sell behaviors
Run the command below
```
docker-compose run --rm freqtrade plot-dataframe --strategy RSI_Bollinger_Bands_1d --export-filename /freqtrade/user_data/backtest_results/backtest-result-2022-04-12_06-14-40.json -p BTC/USDT
```
# Run service in dry-run mode

# Run service in real trading mode