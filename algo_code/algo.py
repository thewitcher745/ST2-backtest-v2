import pandas as pd
from logging import Logger
from typing import Optional

from utils.logger import LoggerSingleton
import utils.datatypes as dt
from utils import constants

ob_logger: Logger | None = None


class Algo:
    def __init__(self, pair_df: dt.PairDf, symbol: str):
        # Set up the logger to be used in this module
        global ob_logger
        if ob_logger is None:
            ob_logger = LoggerSingleton.get_logger("ob_logger")

        self.pair_df: dt.PairDf = pair_df
        self.symbol: str = symbol
        self.zigzag_df: Optional[dt.ZigZagDf] = None

    def init_zigzag(self) -> dt.ZigZagDf:
        """
        This function initializes the zigzag dataframe for the pair. The zigzag works by checking windows of a certain constant size in the dataframe,
        and if the last candle in the window sets a higher high or a lower low than the rest of the candles in the window, it is considered a pivot.

        If the pivot is of the same type as the previous pivot, the same direction is extended. Otherwise, the previous pivot is set as a confirmed
        pivot and added to zigzag_df. If a candle sets both a higher low and a lower low, the calculation will depend on the color of the candle. A
        red candle would mean that (probably) the high was set before the low, therefore the lower low is considered as the determining direction, and
        vice versa.

        Returns:
            pd.DataFrame: A dataframe containing the zigzag points with their times, values and pivot types (peak/valley)
        """

        # To find the first pivot, we form a rolling window series and the first candle which has a higher high or a lower low than its preceding
        # window will be assumed to be the first pivot.
        checking_windows = self.pair_df.rolling(window=constants.zigzag_window_size)

        # Compute rolling max and min for high and low columns
        rolling_high_max = self.pair_df.high.rolling(window=constants.zigzag_window_size).max()
        rolling_low_min = self.pair_df.low.rolling(window=constants.zigzag_window_size).min()

        # Determine peaks and valleys
        hh_sentiments = self.pair_df.iloc[constants.zigzag_window_size:].high >= rolling_high_max.iloc[constants.zigzag_window_size:]
        ll_sentiments = self.pair_df.iloc[constants.zigzag_window_size:].low <= rolling_low_min.iloc[constants.zigzag_window_size:]

        # Check peak and valley conditions. The pure_ prefix means the candles which ONLY register a peak or a valley, not both. the bidir_ prefix
        # denotes candles that register both.
        pure_peak_boolfilter = hh_sentiments & ~ll_sentiments
        pure_valley_boolfilter = ~hh_sentiments & ll_sentiments
        bidir_boolfilter = hh_sentiments & ll_sentiments

        peak_boolfilter = pure_peak_boolfilter | (bidir_boolfilter & (self.pair_df.candle_color == 'green'))
        valley_boolfilter = pure_valley_boolfilter | (bidir_boolfilter & (self.pair_df.candle_color == 'red'))

        zigzag_df: dt.ZigZagDf = dt.ZigZagDf(pd.DataFrame(index=self.pair_df.index))
        zigzag_df['time'] = self.pair_df.time
        zigzag_df['pivot_type'] = ''

        # Apply the peak and valley boolean filter
        zigzag_df.loc[peak_boolfilter, 'pivot_type'] = 'peak'
        zigzag_df.loc[valley_boolfilter, 'pivot_type'] = 'valley'

        # Filter out the non-set values
        zigzag_df = zigzag_df[zigzag_df.pivot_type != '']

        # Each zigzag pivot is confirmed whenever the next pivot is of a different type. This is done by shifting the pivot_type column by 1 and
        # comparing it to the current pivot_type column. If they are different, the pivot is confirmed. The formation time of the current pivot is
        # set to the time of the next pivot. This line sets the formation of each pivot to the time of its next row, and the consecutive
        # non-changing rows are later filtered out.
        zigzag_df['formation_time'] = zigzag_df.shift(-1).time

        # Set the pivot_value column of the zigzag_df to the corresponding candle's high from self.pair_df if it is a peak, and the low if it's a
        # valley.
        zigzag_df.loc[peak_boolfilter, 'pivot_value'] = self.pair_df.high
        zigzag_df.loc[valley_boolfilter, 'pivot_value'] = self.pair_df.low

        # Only keep the rows from zigzag_df which don't have the same pivot_type as the next row
        zigzag_df = zigzag_df[zigzag_df.pivot_type != zigzag_df.pivot_type.shift(-1)]

        return zigzag_df
