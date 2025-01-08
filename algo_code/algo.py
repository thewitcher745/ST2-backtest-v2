import pandas as pd
from logging import Logger
from typing import Optional

from line_profiler import profile

from algo_code.order_block import OrderBlock
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

    def find_relative_pivot(self, pivot_pdi: int, delta: int) -> int | None:
        """
        Finds the relative pivot to the pivot at the given index.

        Args:
            pivot_pdi (int): The pdi of the pivot to find the relative pivot for.
            delta (int): The distance from the pivot to the relative pivot.

        Returns:
            int: The pdi of the relative pivot.
        """

        # zigzag_idx is the zigzag_df index of the current pivot
        try:
            # Get the index of the current pivot
            zigzag_idx = self.zigzag_df.index[self.zigzag_df.pdi == pivot_pdi][0]
            # Return the pdi of the relative pivot
            return self.zigzag_df.iloc[zigzag_idx + delta].pdi

        except IndexError:
            # Handle the case where the index is out of bounds
            return None

    def init_zigzag(self) -> None:
        """
        This function initializes the zigzag dataframe for the algo. The zigzag works by checking windows of a certain constant size in the dataframe,
        and if the last candle in the window sets a higher high or a lower low than the rest of the candles in the window, it is considered a pivot.

        If the pivot is of the same type as the previous pivot, the same direction is extended. Otherwise, the previous pivot is set as a confirmed
        pivot and added to zigzag_df. If a candle sets both a higher low and a lower low, the calculation will depend on the color of the candle. A
        red candle would mean that (probably) the high was set before the low, therefore the lower low is considered as the determining direction, and
        vice versa.
        """

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

        self.zigzag_df = zigzag_df.reset_index().rename(columns={'index': 'pdi'})

    def find_msb_points(self) -> dt.MSBPointsDf:
        """
        This function will look for "MSB points". These are points that are formed when we have a candle which breaks the fib_retracement level of
        a pivot, meaning, for example for a valley, this means a candle wwould have to have a lower low than the fib_retracement level of the valley,
        which is next_peak - (next_peak-current_valley) * (1 + fib_rettracement). Same goes for peaks in the opposite direction. The candle which
        breaks this level sets the formation index for the MSB, which is the index after which the position from the MSB is formed.

        Returns:
            dt.MSBPointsDf: A dataframe
        """

        def find_msb(pivot_type: str, comparison_op, threshold_op):
            msb_df_dict_list = []
            indices = self.zigzag_df[
                (self.zigzag_df.pivot_type == pivot_type) &
                (comparison_op(self.zigzag_df.pivot_type.shift(-1), self.zigzag_df.pivot_type))
                ].pdi.to_numpy()

            for idx in indices[:-1]:
                # The pivot immediately after the current one, of the opposite type.
                next_pivot = self.find_relative_pivot(idx, 1)
                # The pivot after the next pivot, of the same type as the current pivot.
                next_next_pivot = self.find_relative_pivot(idx, 2)

                msb_formation_search_window: dt.PairDf = self.pair_df.iloc[next_pivot:next_next_pivot + 1]

                current_pivot_value = self.zigzag_df.loc[self.zigzag_df.pdi == idx, 'pivot_value'].iat[0]
                next_pivot_value = self.zigzag_df.loc[self.zigzag_df.pdi == next_pivot, 'pivot_value'].iat[0]

                # The threshold that needs to be broken. Calculated separately for each box type  but aggregated.
                msb_threshold = threshold_op(next_pivot_value, abs(next_pivot_value - current_pivot_value))

                try:
                    # The candle that breaks the MSB threshold
                    msb_forming_candle_pdi = msb_formation_search_window.index[msb_formation_search_window.low < msb_threshold][
                        0] if pivot_type == 'valley' else msb_formation_search_window.index[msb_formation_search_window.high > msb_threshold][0]

                    msb_df_dict_list.append({
                        'type': 'short' if pivot_type == 'valley' else 'long',
                        'pdi': idx,
                        'msb_value': current_pivot_value,
                        'formation_pdi': msb_forming_candle_pdi
                    })

                except IndexError:
                    continue

            return msb_df_dict_list

        fib_retracement_increment_factor = 1 + constants.fib_retracement_coeff
        short_msbs = find_msb('valley', lambda x, y: x < y, lambda x, y: x - y * fib_retracement_increment_factor)
        long_msbs = find_msb('peak', lambda x, y: x > y, lambda x, y: x + y * fib_retracement_increment_factor)

        return dt.MSBPointsDf(short_msbs + long_msbs)

    def find_order_blocks(self):
        """
        This function will use the MSB points to find order blocks. The order blocks are formed on the last candle on a leg that has the correct
        color. The leg should start with an MSB point. For "long" MSB points, the order block will form on the last red candle in the leg. For "short"
        the order block's base candle would be the last green candle of the leg.
        """

        order_blocks: list[OrderBlock] = []
        for msb_point in self.find_msb_points().itertuples(index=False):
            msb_point: dt.MSBPoint
            # Form the window to look for order blocks on
            next_pivot_pdi = self.find_relative_pivot(msb_point.pdi, 1)
            ob_base_candle_search_window: dt.PairDf = self.pair_df.iloc[msb_point.pdi:next_pivot_pdi+1]

            # Find the last candle in the leg that has the correct color
            correct_color = 'red' if msb_point.type == 'long' else 'green'

            # The try statement is here to catch cases where no appropriate candle is found
            try:
                base_candle = ob_base_candle_search_window[ob_base_candle_search_window.candle_color == correct_color].iloc[-1]

                ob = OrderBlock(base_candle, msb_point.type, formation_pdi=msb_point.formation_pdi)
                order_blocks.append(ob)

            except IndexError:
                continue

        return order_blocks
