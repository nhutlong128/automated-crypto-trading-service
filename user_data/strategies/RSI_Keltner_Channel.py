# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from functools import reduce

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class RSI_Keltner_Channel(IStrategy):
    """
    https://www.publish0x.com/dutchcryptodad/keltner-channel-and-rsi-strategy-is-this-strategy-profitable-xvyknqq
    
    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_buy_trend, populate_sell_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    Backtest result on top 20 coins in 2022 from 20210131-20211231
    - timeframe, winrate, total profit
    - 1d, 39.3%, 286%
    - 4h, 37.8%, 135%
    - 30m, 31.9%, -10.31%
    - 5m, 26.2%, -84%
    - hyperopt 1d, 48.1%, 300%

    """
    # Required config
    timeframe = '1d'
    minimal_roi = {
        "0": 100
    }
    stoploss = -1
    trailing_stop = False
    trailing_only_offset_is_reached = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.0


    # Hyperopt spaces
    window_range = IntParameter(13, 56, default=16, space="buy")
    atrs_range = IntParameter(1, 8, default=1, space="buy")
    rsi_buy_hline = IntParameter(30, 70, default=61, space="buy")
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Keltner Channel
        for windows in self.window_range.range:
            for atrss in self.atrs_range.range:
                dataframe[f"kc_upperband_{windows}_{atrss}"] = qtpylib.keltner_channel(dataframe, window=windows, atrs=atrss)["upper"]
                dataframe[f"kc_middleband_{windows}_{atrss}"] = qtpylib.keltner_channel(dataframe, window=windows, atrs=atrss)["mid"]

        # Rsi
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)


        # Print stuff for debugging dataframe
        # print(metadata)
        # print(dataframe.tail(20)
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        conditions.append(
           (qtpylib.crossed_above(dataframe['close'], dataframe[f"kc_upperband_{self.window_range.value}_{self.atrs_range.value}"]))
           & (dataframe['rsi'] > self.rsi_buy_hline.value )
           )

        if conditions:
            dataframe.loc[   
                reduce(lambda x, y: x & y, conditions),
                'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        conditions.append(
            (qtpylib.crossed_below(dataframe['close'], dataframe[f"kc_middleband_{self.window_range.value}_{self.atrs_range.value}"]))
           )

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'sell'] = 1

        return dataframe