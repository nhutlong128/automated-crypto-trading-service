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

class RSI_Bollinger_Bands(IStrategy):
    """
    Strategy that get buy & sell signal from dual indicatiors RSI & Bollinger Bands.
    
    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_buy_trend, populate_sell_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*


    """
    # Required config
    timeframe = ''
    minimal_roi = {
        "0": 0.1,
        "106": 0.08,
        "337": 0.072,
        "1015": 0
    }
    stoploss = -0.1
    trailing_stop = False
    trailing_only_offset_is_reached = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.0


    # Hyperoptable parameters
    buy_rsi = IntParameter(low=10, high=50, default=30, space='buy')
    buy_rsi_enabled = BooleanParameter(default=True, space="buy")
    bb_lower_enabled = BooleanParameter(default=True, space="buy")
    macd_cross_above_signal_enabled = BooleanParameter(default=True, space="buy")
    
    sell_rsi = IntParameter(low=60, high=80, default=70, space='sell')
    sell_rsi_enabled = BooleanParameter(default=True, space='sell')
    bb_upper_enabled = BooleanParameter(default=True, space="sell")
    macd_cross_below_signal_enabled = BooleanParameter(default=True, space="sell")
    
    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # Sell signal with ROI interact
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Optional order type mapping.
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)
        
        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe["bb_percent"] = (
            (dataframe["close"] - dataframe["bb_lowerband"]) /
            (dataframe["bb_upperband"] - dataframe["bb_lowerband"])
        )
        dataframe["bb_width"] = (
            (dataframe["bb_upperband"] - dataframe["bb_lowerband"]) / dataframe["bb_middleband"]
        )

        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        return dataframe
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        # GUARDS AND TRENDS
        if self.buy_rsi_enabled.value:
            conditions.append(dataframe["rsi"] < self.buy_rsi.value)
        if self.bb_lower_enabled.value:
            conditions.append(qtpylib.crossed_below(dataframe["close"], dataframe["bb_lowerband"]))
        """
        if self.macd_cross_above_signal_enabled.value:
            conditions.append(qtpylib.crossed_above(dataframe["macd"], dataframe["macdsignal"]))
        """
        # Check that volume is not 0
        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'buy'] = 1
        
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        # GUARDS AND TRENDS
        if self.sell_rsi_enabled.value:
            conditions.append(dataframe["rsi"] > self.sell_rsi.value)
        if self.bb_upper_enabled.value:
            conditions.append(qtpylib.crossed_above(dataframe["close"], dataframe["bb_upperband"]))
        """
        if self.macd_cross_below_signal_enabled.value:
            conditions.append(qtpylib.crossed_below(dataframe["macd"], dataframe["macdsignal"]))
        """
        # Check that volume is not 0
        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'sell'] = 1
        
        return dataframe