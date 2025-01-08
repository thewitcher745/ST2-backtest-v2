import pandas as pd
from logging import Logger
from typing import Optional, Union
import numpy as np
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
        self.order_blocks: Optional[list[OrderBlock]] = None

    def find_relative_pivot(self, zigzag_pdi, idx, delta) -> int | None:
        """
            Finds the relative pivot index in the zigzag pattern.

            Args:
                zigzag_pdi (np.ndarray): Array of pivot indices.
                idx (int): Current pivot index.
                delta (int): Number of pivots to move forward or backward.

            Returns:
                int | None: The pivot index after moving `delta` pivots from the current pivot, or None if out of bounds.
            """
        try:
            zigzag_idx = np.where(zigzag_pdi == idx)[0][0]
            return int(zigzag_pdi[zigzag_idx + delta])
        except IndexError:
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
        a pivot, meaning, for example for a valley, this means a candle would have to have a lower low than the fib_retracement level of the valley,
        which is next_peak - (next_peak-current_valley) * (1 + fib_rettracement). Same goes for peaks in the opposite direction. The candle which
        breaks this level sets the formation index for the MSB, which is the index after which the position from the MSB is formed.

        Returns:
            dt.MSBPointsDf: A dataframe
        """

        zigzag_pdi = self.zigzag_df['pdi'].to_numpy()
        next_pdi = np.roll(zigzag_pdi, -1)[:-1]
        next_next_pdi = np.roll(zigzag_pdi, -2)[:-2]
        pivot_types = self.zigzag_df['pivot_type'].to_numpy()
        pivot_values = self.zigzag_df['pivot_value'].to_numpy()
        next_pivot_values = np.roll(pivot_values, -1)[:-1]
        next_next_pivot_values = np.roll(pivot_values, -2)[:-2]

        pair_df_low = self.pair_df['low'].to_numpy()
        pair_df_high = self.pair_df['high'].to_numpy()

        def find_msb(pivot_type_to_find: str, comparison_op, threshold_op):
            msb_list = []

            # Set indices to be the indices of the pivot points of the specified type, and those that pass the comparison test. The comparison test
            # filters out the valleys that are followed by lower valleys, and peaks that are followed by higher peaks. The [0] is there because
            # np.where returns a tuple, one element for each dimension of the array, but this is a 1-D array.
            potential_msb_zigzag_indices = np.where(
                (pivot_types[:-2] == pivot_type_to_find) & comparison_op(pivot_values[:-2], next_next_pivot_values))[0]

            # Calculate the MSB threshold for each pivot that has an index in potential_msb_indices
            msb_thresholds = threshold_op(pivot_values[:-1], next_pivot_values)[potential_msb_zigzag_indices]

            # Form search windows for each zigzag pivot index in potential_msb_zigzag_indices. Then in that search window, look for candles that
            # break the msb_threshold. Each search window is a series of highs or lows, depending on the pivot type, from the next pivot to the
            # next-next pivot.

            pair_df_of_type = pair_df_high
            if pivot_type_to_find == 'valley':
                pair_df_of_type = pair_df_low

            for counter, zigzag_idx in enumerate(potential_msb_zigzag_indices):
                # These indices can apparently go out of bounds, so we need to catch that
                try:
                    search_window = pair_df_of_type[next_pdi[zigzag_idx]:next_next_pdi[zigzag_idx] + 1]
                    msb_threshold = msb_thresholds[counter]
                except IndexError:
                    continue

                if pivot_type_to_find == 'valley':
                    msb_breaking_candles_search_window_idx = np.where(search_window < msb_threshold)[0]
                else:
                    msb_breaking_candles_search_window_idx = np.where(search_window > msb_threshold)[0]

                if len(msb_breaking_candles_search_window_idx) > 0:
                    first_breaking_candle_search_window_idx = msb_breaking_candles_search_window_idx[0]

                    # msb_breaking_candle_search_window_idx is the index of the candle LOCAL TO SEARCH WINDOW which breaks the MSB threshold.
                    # This has to be converted to regular PDI to be usable. This can be easily done by summing its value with the next_pdi value.
                    formation_pdi = next_pdi[zigzag_idx] + first_breaking_candle_search_window_idx

                    msb_list.append({
                        'type': 'short' if pivot_type_to_find == 'valley' else 'long',
                        'pdi': zigzag_pdi[zigzag_idx],
                        'msb_value': pivot_values[zigzag_idx],
                        'formation_pdi': formation_pdi
                    })

            return msb_list

        fib_retracement_increment_factor = 1 + constants.fib_retracement_coeff
        short_msbs = find_msb('valley', lambda current_val, next_next_val: next_next_val < current_val,
                              lambda current_val, next_val: next_val - (next_val - current_val) * fib_retracement_increment_factor)
        long_msbs = find_msb('peak', lambda current_val, next_next_val: next_next_val > current_val,
                             lambda current_val, next_val: next_val + (current_val - next_val) * fib_retracement_increment_factor)

        return dt.MSBPointsDf(short_msbs + long_msbs)

    def find_order_blocks(self) -> list[OrderBlock]:
        """
        This function will use the MSB points to find order blocks. The order blocks are formed on the last candle on a leg that has the correct
        color. The leg should start with an MSB point. For "long" MSB points, the order block will form on the last red candle in the leg. For "short"
        the order block's base candle would be the last green candle of the leg.
        """

        order_blocks: list[OrderBlock] = []
        candle_colors = self.pair_df['candle_color'].to_numpy()
        candle_color_numeric = np.where(candle_colors == 'green', 1, -1)

        pair_df_highs = self.pair_df['high'].to_numpy()
        pair_df_lows = self.pair_df['low'].to_numpy()
        pair_df_times = self.pair_df['time'].to_numpy()
        zigzag_pdi = self.zigzag_df['pdi'].to_numpy()
        for msb_point in self.find_msb_points().itertuples(index=False):
            msb_point: dt.MSBPoint
            # Form the window to look for order blocks on
            try:
                zigzag_idx = np.where(zigzag_pdi == msb_point.pdi)[0][0]
                next_pivot_pdi = int(zigzag_pdi[zigzag_idx + 1])
            except IndexError:
                continue

            search_window_candle_colors = candle_color_numeric[msb_point.pdi:next_pivot_pdi + 1]

            # Find the last candle in the leg that has the correct color
            correct_color = -1 if msb_point.type == 'long' else 1

            # The try statement is here to catch cases where no appropriate candle is found
            try:
                base_candle_pdi: int = int(np.where(search_window_candle_colors == correct_color)[0][-1]) + msb_point.pdi
                base_candle_time = pd.Timestamp(pair_df_times[base_candle_pdi])
                base_candle_high = pair_df_highs[base_candle_pdi]
                base_candle_low = pair_df_lows[base_candle_pdi]

                base_candle = dt.Candle(pdi=base_candle_pdi,
                                        time=base_candle_time,
                                        high=base_candle_high,
                                        low=base_candle_low)
                ob = OrderBlock(base_candle, msb_point.type, formation_pdi=msb_point.formation_pdi)
                order_blocks.append(ob)

            except IndexError:
                continue

        self.order_blocks = order_blocks
        return order_blocks

    def process_concurrent_order_blocks(self):
        """
        This function will make sure that only a maximum of max_concurrent number of OB's are always active in each direction. When a new OB is
        introduced, meaning when it's formation_pdi is reached, the oldest OB in the same direction will be closed. That is to say, at all times, only
        the most recent max_concurrent OB's will be active in each direction.
        """
        short_order_blocks = sorted([ob for ob in self.order_blocks if ob.type == 'short'], key=lambda ob: ob.formation_pdi)
        long_order_blocks = sorted([ob for ob in self.order_blocks if ob.type == 'long'], key=lambda ob: ob.formation_pdi)

        active_long_obs = []
        active_short_obs = []

        for ob in long_order_blocks:
            # print(ob.formation_pdi)
            # Close the oldest OB if the limit is exceeded
            if len(active_long_obs) >= constants.max_concurrent:
                oldest_ob = active_long_obs.pop(0)
                oldest_ob.end_pdi = ob.formation_pdi - 1
                # print(f'Max concurrent OB reached. Set end_pdi for {oldest_ob} to {ob.formation_pdi - 1}')

            # Add the new OB to the active list
            active_long_obs.append(ob)

        for ob in short_order_blocks:
            # print(ob.formation_pdi)
            # Close the oldest OB if the limit is exceeded
            if len(active_short_obs) >= constants.max_concurrent:
                oldest_ob = active_short_obs.pop(0)
                oldest_ob.end_pdi = ob.formation_pdi - 1
                # print(f'Max concurrent OB reached. Set end_pdi for {oldest_ob} to {ob.formation_pdi - 1}')

            # Add the new OB to the active list
            active_short_obs.append(ob)

    def convert_pdis_to_times(self, pdis: Union[int, list[int]]) -> Union[pd.Timestamp, list[pd.Timestamp], None]:
        """
        Convert a list (or a single) of PDIs to their corresponding times using algo_code.pair_df.

        Args:
            pdis (list[int]): List of PDIs to convert.

        Returns:
            list[pd.Timestamp]: List of corresponding times.
        """

        if pdis is None:
            return None

        if not isinstance(pdis, list):
            pdis = [pdis]

        if len(pdis) == 0:
            return []

        # Map PDIs to their corresponding times
        times = [self.pair_df.iloc[pdi].time for pdi in pdis]

        # If it's a singular entry, return it as a single timestamp
        if len(times) == 1:
            return times[0]

        return list(times)
