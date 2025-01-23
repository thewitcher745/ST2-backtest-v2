import pandas as pd
from logging import Logger
from typing import Optional, Union
import numpy as np

from algo_code.order_block import OrderBlock
from utils.logger import LoggerSingleton
import utils.datatypes as dt
from utils.general_utils import calc_candle_percentage
from utils import constants

ob_logger: Logger | None = None


class Algo:
    def __init__(self, pair_df: dt.PairDf, symbol: str, params):
        # Set up the logger to be used in this module
        global ob_logger
        if ob_logger is None:
            ob_logger = LoggerSingleton.get_logger("ob_logger")

        self.pair_df: dt.PairDf = pair_df
        self.symbol: str = symbol
        self.zigzag_df: Optional[dt.ZigZagDf] = None
        self.ob_list: Optional[list[OrderBlock]] = None
        self.params = params

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
        rolling_high_max = self.pair_df.high.rolling(window=self.params.zigzag_window_size).max()
        rolling_low_min = self.pair_df.low.rolling(window=self.params.zigzag_window_size).min()

        # Determine peaks and valleys
        hh_sentiments = self.pair_df.iloc[self.params.zigzag_window_size:].high >= rolling_high_max.iloc[self.params.zigzag_window_size:]
        ll_sentiments = self.pair_df.iloc[self.params.zigzag_window_size:].low <= rolling_low_min.iloc[self.params.zigzag_window_size:]

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

        fib_retracement_increment_factor = 1 + self.params.fib_retracement_coeff
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

        ob_list: list[OrderBlock] = []
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

                if self.params.ob_size_lower_limit <= calc_candle_percentage(base_candle) < self.params.ob_size_upper_limit:
                    if not constants.position_type or msb_point.type == constants.position_type:
                        ob = OrderBlock(base_candle, msb_point.type, formation_pdi=msb_point.formation_pdi + 1, params=self.params)
                        ob_list.append(ob)

            except IndexError:
                continue

        self.ob_list = ob_list
        return ob_list

    def process_concurrent_order_blocks(self):
        """
        This function will make sure that only a maximum of max_concurrent number of OB's are always active in each direction. When a new OB is
        introduced, meaning when it's formation_pdi is reached, the oldest OB in the same direction will be closed. That is to say, at all times, only
        the most recent max_concurrent OB's will be active in each direction.
        """
        short_order_blocks = sorted([ob for ob in self.ob_list if ob.type == 'short'], key=lambda ob: ob.formation_pdi)
        long_order_blocks = sorted([ob for ob in self.ob_list if ob.type == 'long'], key=lambda ob: ob.formation_pdi)

        active_long_obs = []
        active_short_obs = []

        for ob in long_order_blocks:
            # print(ob.formation_pdi)
            # Close the oldest OB if the limit is exceeded
            if len(active_long_obs) >= self.params.max_concurrent:
                oldest_ob = active_long_obs.pop(0)
                oldest_ob.end_pdi = ob.formation_pdi - 1
                # print(f'Max concurrent OB reached. Set end_pdi for {oldest_ob} to {ob.formation_pdi - 1}')

            # Add the new OB to the active list
            active_long_obs.append(ob)

        for ob in short_order_blocks:
            # print(ob.formation_pdi)
            # Close the oldest OB if the limit is exceeded
            if len(active_short_obs) >= self.params.max_concurrent:
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

    def calc_events_array(self):
        """
        This function will return an array which represents the events that each candle triggers for each order block. The array will start from the
        formation_pdi of each order block, and will have 0 for entry, -1 for stoploss, 0.5 for no even and >= 1 for each target triggered. This array
        will later get processed to find the order of events and to find profit and loss.
        """

        # This method will use numpy vector operations for faster calculation. The values of the candles used for the events will be the highs and
        # lows.
        pair_df_highs = self.pair_df.high.to_numpy()
        pair_df_lows = self.pair_df.low.to_numpy()

        # The events will be calculated for each order block, and the results will be stored in a numpy array and attributed to the order block
        # as an instance variable, OrderBlock.events_array.
        for ob in self.ob_list:
            ob: OrderBlock

            pair_df_lows_after_formation = pair_df_lows[ob.formation_pdi:]
            pair_df_highs_after_formation = pair_df_highs[ob.formation_pdi:]

            if ob.type == 'long':
                # The entry event will be triggered when the low of the candle is less than or equal to the entry price. These are the indices of
                # candles whose lows are less than or equal to the entry price.
                entry_level_events = pair_df_lows_after_formation <= ob.position.entry_price

                # The entry event will be triggered when the low of the candle is less than or equal to the stoploss. These are the indices of
                # candles whose lows are less than or equal to the stoploss.
                stoploss_events = pair_df_lows_after_formation <= ob.position.stoploss

                # The target_events list is a list whose elements represents events related to each target being hit. Each element is a list of events
                # for that target. This means the 0-th element represents a list of indices of the candles which hit the 1-st target, the 1-st element
                # represents the indices of the candles which hit the 2-nd target, and so on.
                target_list_events = []
                for target in ob.position.target_list:
                    target_list_events.append(pair_df_highs_after_formation >= target)

            else:
                # Same comments as ob.type=="long", in reverse.
                entry_level_events = pair_df_highs_after_formation >= ob.position.entry_price

                stoploss_events = pair_df_highs_after_formation >= ob.position.stoploss

                target_list_events = []
                for target in ob.position.target_list:
                    target_list_events.append(pair_df_lows_after_formation <= target)

            # So now we have n_targets + 2 lists which represent the candles where events have happened. Now we need an array which contains
            # what events EACH candle represents, so for every candle in pair_df there would be at most one event, and there are certain rules:
            # 1) Targets and stop-losses may only happen exclusively after an entry is made, not even on the same candle.
            # 2) Each candle may only have at most 1 sentiment.
            # 3) Stop-losses take priority over targets if they happen on the same candle.

            # The code now generates a numpy array the same size as pair_df - formation_pdi, which contains the order in which the events happened:
            # 0.5 -> No event
            # 0 -> Entry
            # -1 -> Stoploss
            # 1, 2, 3, ... -> Targets

            # Initialize the events array with a default value (e.g., 0.5 for no event)
            events_array = np.full_like(pair_df_lows_after_formation, 0.5)

            # Set the target events (1, 2, 3, ... for targets), which will overwrite entry and stoploss events
            for target_idx, target_events in enumerate(target_list_events):
                events_array[target_events] = target_idx + 1

            # Set the entry events (0 for entry). Entry events overwrite any target events.
            events_array[entry_level_events] = 0

            # Finally, set the stoploss events (-1 for stoploss), which will overwrite entry and target events.
            events_array[stoploss_events] = -1

            ob.events_array = events_array

    def process_events_array(self):
        """
        Processes the events array for each order block. This means logically ordering the events and calculating the profit and loss for each order
        block, as well as the exit statuses.
        There are certain rules for processing the events.
        1) Targets and stoplosses can only occur after entries have happened.
        2) Entries can only happen within the active region, which is after the formation_pdi and before the end_time.
        3) After a full target, an order block is still valid for entry for a maximum of self.params.max_bounces times. The number of remaining
           bounces for each order block will be saved to a property on it, and it will be reduced by 1 every time a full target happens.
        4) After a stoploss, the order block will become unavailable for entry. This is achieved by setting OrderBlock.remaining_bounces to 0 after a
           stoploss event has happened after entry without achieving any targets.
        5) According to the trailing stoploss configuration (self.params.trailing_sl_target_id), the stoploss will be placed at the entry once the
           respective target has been hit. This means if trailing_sl_target_id==1, after target 1 is achieved, the next entry (0 in events_array) to
           be hit would be the stoploss, and would result in the position exiting, but this would not trigger rule #4, and after a trailing stoploss
           is hit, the OB is still valid for entry.

        The OrderBlock.events_array for each block is an array which represents the events that happened after the formation_pdi of the OB. Each
        element of the array represents one candle and its sentiment (event registered by the candle) and it can have values of -1 (for non-trailing
        stoploss), 0 (for entry price level), 0.5 (for no event at all) or 1 through len(OrderBlock.position.target_list) for each target hit.
        """
        # The times array of pair_df, used for registering exit times in Position.exit()
        pair_df_times = self.pair_df.time.to_numpy()

        for ob in self.ob_list:
            ob: OrderBlock

            # The starting index of the event array check window. This gets updated when checking for bounces after the first.
            event_array_start_index = 0

            # The typecasting to float is because the events array is in float form
            n_targets = float(len(ob.position.target_list))

            # If there are bounces remaining for the OB, the entry is still valid. This is set to 0 after a stoploss event and reduced by 1 after each
            # full target.
            while ob.remaining_bounces > 0:
                # The events array after the starting point
                sliced_events_array = ob.events_array[event_array_start_index:]

                # The index of the first entry, local to the sliced events array. This should eventually be added to the event_array_start_index to
                # get the absolute distance from the formation of the OB.
                try:
                    first_entry_index = np.where(sliced_events_array == 0)[0][0]

                    # If an entry is found, register it on the OB's position. The method throws an exception if the entry found isn't between the
                    # formation_pdi and end_pdi of its parent order block.
                    ob.position.enter(first_entry_index + event_array_start_index + ob.formation_pdi)

                # If no entry is found, go on to the next OB.
                except IndexError:
                    break

                # If a stoploss even has happened before any entry event, discard the order block completely.
                try:
                    first_stoploss_index = np.where(sliced_events_array == -1)[0][0]

                    if first_stoploss_index <= first_entry_index:
                        break

                # If no stoploss event is found, continue with the code.
                except IndexError:
                    pass

                events_after_entry = sliced_events_array[first_entry_index:]

                last_target = 0
                trailing_triggered = False
                target_hit_pdis = np.array([], dtype='int')

                for event_index, event in enumerate(events_after_entry):
                    # 0.5 events (NO_EVENT candles) don't do anything.
                    if event == 0.5:
                        continue

                    # Check for full target event
                    if event == n_targets:
                        ob.remaining_bounces -= 1

                        # If a full-target event happens, the rest of the target hit PDI's list should be filled by the current PDI, assuming the
                        # current candle has hit all the remaining targets.
                        exit_pdi = first_entry_index + event_array_start_index + ob.formation_pdi + event_index
                        target_hit_pdis = np.concat((target_hit_pdis, np.array([exit_pdi] * (int(n_targets) - len(target_hit_pdis)))))

                        ob.position.exit(symbol=self.symbol,
                                         pair_df_times=pair_df_times,
                                         exit_status=f'FULL_TARGET_{int(n_targets)}',
                                         exit_pdi=exit_pdi,
                                         target_hit_pdis=target_hit_pdis,
                                         exit_price=ob.position.target_list[-1]
                                         )

                        event_array_start_index += event_index + first_entry_index + 1

                        break

                    # Stoploss events. Register the last_event as the exit status, if it is 0, that means the position didn't hit any targets before
                    # hitting the original stoploss. Otherwise, the exit status is registered with the last_event as it's highest target.
                    elif event == -1:
                        # Stoploss events prevent further bounces.
                        ob.remaining_bounces = 0

                        # If there was any target registered before the stoploss, the exit status is the highest target hit, if not it's 'STOPLOSS'.
                        exit_status = 'STOPLOSS' if last_target == 0 else f'TARGET_{int(last_target)}'
                        ob.position.exit(symbol=self.symbol,
                                         pair_df_times=pair_df_times,
                                         exit_status=exit_status,
                                         exit_pdi=first_entry_index + event_array_start_index + ob.formation_pdi + event_index,
                                         target_hit_pdis=target_hit_pdis,
                                         exit_price=ob.position.stoploss
                                         )

                        break

                    # Target events register a last event as a target. In this case, the stoploss is moved to the entry, so events of 0 will also
                    # trigger a trailing stoploss event.
                    elif event >= 1:
                        # If the now-found target-hitting candle registers a higher target than the previously registered one, append it to the
                        # targets hit.
                        if event > last_target:
                            target_hit_pdis = np.append(target_hit_pdis, first_entry_index + event_array_start_index + ob.formation_pdi + event_index)
                            last_target = event

                        # The price level to put the trailing stoploss at. If the target is at that level, the trailing stoploss variable is set to
                        # true. This means the next time price reaches a 0 event, it will trigger a TRAILING exit status code.
                        if self.params.trailing_sl_target_id != 0 and event == self.params.trailing_sl_target_id:
                            trailing_triggered = True

                    # Entry price level events
                    # If the event is a 0, that means the candle has hit an entry price level.
                    elif event == 0:
                        # If the trailing configuration hasn't triggered, continue to the next candle
                        if not trailing_triggered:
                            continue

                        # If it has, trigger an exit from the position, and reduce remaining bounces by 1, since our OB is still valid for entry.
                        else:
                            ob.remaining_bounces -= 1
                            ob.position.exit(symbol=self.symbol,
                                             pair_df_times=pair_df_times,
                                             exit_status=f'TARGET_{int(last_target)}',
                                             exit_pdi=first_entry_index + event_array_start_index + ob.formation_pdi + event_index,
                                             target_hit_pdis=target_hit_pdis,
                                             exit_price=ob.position.entry_price
                                             )

                            event_array_start_index += event_index + first_entry_index + 1

                            break
                else:
                    break
