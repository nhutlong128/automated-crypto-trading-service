from pathlib import Path
from freqtrade.configuration import Configuration
from freqtrade.data.history import load_pair_history
from freqtrade.resolvers import ExchangeResolver
from freqtrade.plugins.pairlistmanager import PairListManager
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from dateutil.relativedelta import *
import json
import os
import argparse


class generator:
    STAKE_CURRENCY_NAME = ''
    EXCHANGE_NAME = ''
    config = ''
    exchange = ''
    pairlists = ''
    pairs = ''
    data_location = ''
    DATE_FORMAT = '%Y%m%d'
    DATE_TIME_FORMAT = '%Y%m%d %H:%M:%S'

    def set_config(self):
        self.config = Configuration.from_files([])
        self.config["dataformat_ohlcv"] = "json"
        self.config["timeframe"] = "1d"
        self.config['exchange']['name'] = self.EXCHANGE_NAME
        self.config['stake_currency'] = self.STAKE_CURRENCY_NAME
        self.config['exchange']['pair_whitelist'] = [
            f'.*/{self.STAKE_CURRENCY_NAME}',
            #"DOT/USDT",
            #"ADA/USDT",
            #"SHIB/USDT"
        ]
        self.config['exchange']['pair_blacklist'] = [
            # // Major coins
            "(BTC|ETH)/.*",
            # // BINANCE:
            # // Exchange
            "(BNB)/.*",
            # // Leverage
            ".*(_PREMIUM|BEAR|BULL|DOWN|HALF|HEDGE|UP|[1235][SL])/.*",
            # // Fiat
            "(AUD|BRZ|CAD|CHF|EUR|GBP|HKD|IDRT|JPY|NGN|RUB|SGD|TRY|UAH|USD|ZAR)/.*",
            # // Stable
            "(BUSD|CUSDT|DAI|PAXG|SUSD|TUSD|USDC|USDP|USDT|VAI)/.*",
            # // FAN
            "(ACM|AFA|ALA|ALL|APL|ASR|ATM|BAR|CAI|CITY|FOR|GAL|GOZ|IBFK|JUV|LAZIO|LEG|LOCK-1|NAVI|NMR|NOV|OG|PFL|PSG|ROUSH|STV|TH|TRA|UCH|UFC|YBO)/.*",
            # // Others
            "(CHZ|CTXC|HBAR|NMR|SHIB|SLP|XVS|ONG|ARDR)/.*",

            # // KUCOIN:
            # // Exchange Tokens
            "KCS/.*",
            # // Leverage tokens
            ".*(3|3L|3S|5L|5S)/.*",
            # // Fiat
            "(AUD|EUR|GBP|CHF|CAD|JPY)/.*",
            # // Stable tokens
            "(BUSD|USDT|TUSD|USDC|CUSDT|DAI|USDN|CUSD)/.*",
            # // FAN Tokens
            "(ACM|AFA|ALA|ALL|APL|ASR|ATM|BAR|CAI|CITY|FOR|GAL|GOZ|IBFK|JUV|LEG|LOCK-1|NAVI|NMR|NOV|OG|PFL|PORTO|PSG|ROUSH|STV|TH|TRA|UCH|UFC|YBO)/.*",
            # // Other Coins
            "(CHZ|SLP|XVS|MEM|AMPL|XYM|POLX|CARR|SKEY|MASK|KLV|TLOS)/.*"
        ]
        self.config['pairlists'] = [
            {
                "method": "StaticPairList",
            },
        ]

        self.exchange = ExchangeResolver.load_exchange(self.config['exchange']['name'], self.config, validate=False)
        self.pairlists = PairListManager(self.exchange, self.config)
        self.pairlists.refresh_pairlist()
        self.pairs = self.pairlists.whitelist
        self.data_location = Path(self.config['user_data_dir'], 'data', self.config['exchange']['name'])

        print(f"found {str(len(self.pairs))} pairs on {self.config['exchange']['name']}")

    def get_data_slices_dates(df, start_date_str, end_date_str, interval, self):
        # df_start_date = df.date.min()
        # df_end_date = df.date.max()

        defined_start_date = datetime.strptime(start_date_str, self.DATE_TIME_FORMAT)
        defined_end_date = datetime.strptime(end_date_str, self.DATE_TIME_FORMAT)

        # start_date = df_start_date if defined_start_date < df_start_date else defined_start_date
        # end_date = df_end_date if defined_end_date > df_end_date else defined_end_date

        start_date = defined_start_date
        end_date = defined_end_date

        # time_delta = timedelta(hours=interval_hr)
        if interval == 'monthly':
            time_delta = relativedelta(months=+1)
        elif interval == 'weekly':
            time_delta = relativedelta(weeks=+1)
        elif interval == 'daily':
            time_delta = relativedelta(days=+1)
        else:
            time_delta = relativedelta(months=+1)

        slices = []

        run = True

        while run:
            # slice_start_time = end_date - time_delta
            slice_end_time = start_date + time_delta
            if slice_end_time <= end_date:
                slice_date = {
                    'start': start_date,
                    'end': slice_end_time
                }

                slices.append(slice_date)
                start_date = slice_end_time
            else:
                slice_date = {
                    'start': start_date,
                    'end': defined_end_date
                }

                slices.append(slice_date)
                run = False

        return slices

    def process_candles_data(pairs, filter_price, range_stability_filter_dict, volatility_filter_dict, self):
        full_dataframe = pd.DataFrame()

        for pair in pairs:

            #print(self.data_location)
            #print(self.config["timeframe"])
            #print(pair)

            candles = load_pair_history(
                datadir=self.data_location,
                timeframe=self.config["timeframe"],
                pair=pair,
                data_format="json"
            )

            # Init filter columns
            candles["filter_price"] = 1
            candles["range_stability"] = 1
            candles["volatility"] = 1
            
            if len(candles):
                # Not sure about AgeFilter
                # Apply Price Filter
                
                candles[f"higher_filter_price"] = np.where(candles["close"] > filter_price, 1, 0)
                
                # Apply range stability filter
                range_stability_lookback_days = range_stability_filter_dict["lookback_days"]
                range_stability_min_rate_of_change = range_stability_filter_dict["min_rate_of_change"]
                range_stability_max_rate_of_change = range_stability_filter_dict["max_rate_of_change"]
                candles[f"max_high_by_{range_stability_lookback_days}_days"] = candles["high"].rolling(range_stability_lookback_days).max()
                candles[f"min_low_by_{range_stability_lookback_days}_days"] = candles["low"].rolling(range_stability_lookback_days).min()
                candles[f"rate_of_change_by_{range_stability_lookback_days}_days"] =    (
                                                                                            (
                                                                                                candles[f"max_high_by_{range_stability_lookback_days}_days"]
                                                                                                -
                                                                                                candles[f"min_low_by_{range_stability_lookback_days}_days"]
                                                                                            )
                                                                                            /
                                                                                            (
                                                                                                (
                                                                                                    candles[f"max_high_by_{range_stability_lookback_days}_days"]
                                                                                                    + candles[f"min_low_by_{range_stability_lookback_days}_days"]
                                                                                                )
                                                                                                /
                                                                                                2
                                                                                            ) 
                                                                                        )
                #candles.loc[(candles[f"rate_of_change_by_{range_stability_lookback_days}_days" < range_stability_min_rate_of_change), f"higher_than_min_rate_of_change_{range_stability_min_rate_of_change}"] = 0
                candles["range_stability"] = np.where(  (candles[f"rate_of_change_by_{range_stability_lookback_days}_days"] > range_stability_min_rate_of_change)
                                                        &
                                                        (candles[f"rate_of_change_by_{range_stability_lookback_days}_days"] < range_stability_max_rate_of_change)
                                                        , 1, 0)
                # Apply volatility stability filter
                volatility_lookback_days = volatility_filter_dict["lookback_days"]
                volatility_min = volatility_filter_dict["min_volatility"]
                volatility_max = volatility_filter_dict["max_volatility"]
                candles[f"volatility_over_{volatility_lookback_days}_days"] = candles["close"].rolling(volatility_lookback_days).std(ddof=0)
                candles["volatility"] = np.where(
                                                                                                            (candles[f"volatility_over_{volatility_lookback_days}_days"] > volatility_min)
                                                                                                            &
                                                                                                            (candles[f"volatility_over_{volatility_lookback_days}_days"] < volatility_max),
                                                                                                            1,
                                                                                                            0)
                
                column_name = pair
                candles[column_name] = candles['volume'] * candles["filter_price"] * candles["range_stability"] * candles["volatility"]
                #print(f"Dataframe for pair {pair}")
                #print(candles)
                if full_dataframe.empty:
                    full_dataframe = candles[['date', column_name]].copy()
                else:
                    # this row (as it was in the original) cut off the dataframe depending on the first (hence the how='left' candle of the the pair. Outer merges both including the new timerange of the 2ndary pairs.
                    # full_dataframe = pd.merge(full_dataframe, candles[['date', column_name]].copy(), on='date', how='left')
                    full_dataframe = pd.merge(full_dataframe, candles[['date', column_name]].copy(), on='date',
                                              how='outer')
                # print("Loaded " + str(len(candles)) + f" rows of data for {pair} from {data_location}")
                # print(full_dataframe.tail(1))
        #print("Full Dataframe of all pair")
        #print(full_dataframe.head())

        if "date" in full_dataframe:
            full_dataframe['date'] = full_dataframe['date'].dt.tz_localize(None)

        return full_dataframe

    def process_date_slices(df, date_slices, number_assets, self):
        result = {}
        for date_slice in date_slices:
            df_slice = df[(df.date >= date_slice['start']) & (df.date < date_slice['end'])].copy()
            #print(f"Dataframe slice for {date_slice}")
            #print(df_slice)
            summarised = df_slice.sum()
            #print("Summarized Dataframe")
            #print(summarised)
            summarised = summarised[summarised > 0]
            summarised = summarised.sort_values(ascending=False)

            if len(summarised) > number_assets:
                result_pairs_list = list(summarised.index[:number_assets])
            else:
                result_pairs_list = list(summarised.index)

            if len(result_pairs_list) > 0:
                result[
                    f'{date_slice["start"].strftime(self.DATE_FORMAT)}-{date_slice["end"].strftime(self.DATE_FORMAT)}'] = result_pairs_list

        return result

    def process_date_slice(df, date_slice, number_assets, self):
        result_pairs_list = []
        
        df_slice = df[(df.date >= date_slice['start']) & (df.date < date_slice['end'])].copy()
        #print(f"Dataframe slice for {date_slice}")
        #print(df_slice)
        summarised = df_slice.sum()
        #print("Summarized Dataframe")
        #print(summarised)
        summarised = summarised[summarised > 0]
        summarised = summarised.sort_values(ascending=False)

        if len(summarised) > number_assets:
            result_pairs_list = list(summarised.index[:number_assets])
        else:
            result_pairs_list = list(summarised.index)
        print(result_pairs_list)
        return result_pairs_list
    
    
    def main(self):
        parser = argparse.ArgumentParser()

        #parser.add_argument("-c", "--config", help="config to parse")
        #parser.add_argument("-t", "--timerange", nargs='?',
        #                    help="timerange as per freqtrade format, e.g. 20210401-, 20210101-20210201, etc")
        #parser.add_argument("-o", "--outfile", help="path where output the pairlist", type=argparse.FileType('w'))
        #parser.add_argument("-mp", "--minprice", help="price for price filter")
        #parser.add_argument("-tf", "--timeframe", help="timeframe of loaded candles data")
        #parser.add_argument("-na", "--numberassets", help="number of assets to be filtered")

        parser.add_argument("--exchange", default="binance")
        parser.add_argument("--stake_currency", default="USDT")

        args = parser.parse_args()

        # Make this arg parse-able
        # And add blacklist
        START_DATE_STR = '20200101 00:00:00'
        END_DATE_STR = '20220501 00:00:00'
        # For now it shouldn't be less than a day because it's outputs object with timerage suitable for backtesting
        # for easy copying eg. 20210501-20210602
        INTERVAL_ARR = ['monthly']
        # INTERVAL_ARR = ['weekly']
        # INTERVAL_ARR = ['monthly']
        # ASSET_FILTER_PRICE_ARR = [0, 0.01, 0.02, 0.05, 0.15, 0.5]
        ASSET_FILTER_PRICE_ARR = [0, 0.05, 0.15, 0.5]
        #NUMBER_ASSETS_ARR = [30, 45, 60, 75, 90, 105, 120, 200]
        NUMBER_ASSETS_ARR = [80, 105]

        RANGE_STABILITY_FILTER_DICT = {
            "lookback_days": 3,
            "min_rate_of_change": 0.03,
            "max_rate_of_change": 1000,
        }
        RANGE_STABILITY_FILTER_STR = f"{RANGE_STABILITY_FILTER_DICT['lookback_days']}:{RANGE_STABILITY_FILTER_DICT['min_rate_of_change']}:{RANGE_STABILITY_FILTER_DICT['max_rate_of_change']}"

        VOLATILITY_FILTER_DICT = {
            "lookback_days": 3,
            "min_volatility": 0.02,
			"max_volatility": 0.75,
        }
        VOLATILITY_FILTER_STR = f'{VOLATILITY_FILTER_DICT["lookback_days"]}:{VOLATILITY_FILTER_DICT["min_volatility"]}:{VOLATILITY_FILTER_DICT["max_volatility"]}'
        self.EXCHANGE_NAME = args.exchange
        self.STAKE_CURRENCY_NAME = args.stake_currency

        # ASSET_FILTER_PRICE_ARR = [0]
        # NUMBER_ASSETS_ARR = [90]

        start_string = START_DATE_STR.split(' ')[0]
        end_string = END_DATE_STR.split(' ')[0]

        self.set_config(self)

        for asset_filter_price in ASSET_FILTER_PRICE_ARR:

            volume_dataframe = self.process_candles_data(self.pairs,
                                                        asset_filter_price,
                                                        RANGE_STABILITY_FILTER_DICT,
                                                        VOLATILITY_FILTER_DICT,
                                                        self)

            if volume_dataframe.empty:
                continue

            for interval in INTERVAL_ARR:
                date_slices = self.get_data_slices_dates(volume_dataframe, START_DATE_STR, END_DATE_STR, interval, self)

                for date_slice in date_slices:
                    start_date_slice= str(date_slice["start"]).split(' ')[0]
                    end_date_slice= str(date_slice["end"]).split(' ')[0]
                    for number_assets in NUMBER_ASSETS_ARR:
                        print(f"Processing date_slice {start_date_slice}-{end_date_slice} with num_asset {number_assets} & price filter {asset_filter_price}")
                        result_obj = self.process_date_slice(volume_dataframe, date_slice, number_assets, self)
                        if len(result_obj) < 1:
                            continue
                        # {'timerange': [pairlist]}
                        #print(result_obj)
                        p_json = json.dumps(result_obj, indent=4)
                        file_name = f'user_data/pairlists/{self.EXCHANGE_NAME}/{self.STAKE_CURRENCY_NAME}/{interval}/{interval}_{number_assets}_{self.STAKE_CURRENCY_NAME}_{str(asset_filter_price).replace(".", ",")}_minprice_{RANGE_STABILITY_FILTER_STR}_rangestability_{VOLATILITY_FILTER_STR}_volatility_{start_date_slice}_{end_date_slice}.json'
                        os.makedirs(os.path.dirname(file_name), exist_ok=True)
                        with open(file_name, 'w') as f:
                            f.write(p_json)

        # Save result object as json to --outfile location
        print('Done.')


if __name__ == "__main__":
    generator.main(generator)