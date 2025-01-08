import pandas as pd
from lightweight_charts import Chart

import utils.datatypes as dt


def load_local_data(pair_name: str = "BTCUSDT", timeframe: str = "15m") -> dt.PairDf:
    """
    Imports the .hdf5 files associated with the indicated pair in the give timeframe.

    Args:
        pair_name (str): The symbol of the pair to load
        timeframe (str): Standardized timeframe

    Returns:
        pd.DataFrame: A dataframe containing all the OHLC data of the give pair

    """
    hdf_path: str = f"./cached_data/{timeframe}/{pair_name}.hdf5"

    pair_df = pd.DataFrame(pd.read_hdf(hdf_path))

    # Add the candle color to the return value
    pair_df['candle_color'] = pair_df.apply(lambda row: 'green' if row.close > row.open else 'red', axis=1)

    return dt.PairDf(pair_df)


class PlottingTool:
    def __init__(self):
        self.chart = Chart()
        self.chart.legend(visible=True, ohlc=True, color_based_on_candle=True, font_size=15)

        self.pair_df: dt.PairDf | None = None

    def register_msb_point_updates(self, msb_points_df: dt.MSBPointsDf):
        # Subscribe to the even of the chart's range change
        self.chart.events.range_change += lambda chart, bars_before, bars_after: self.update_markers_on_range_change(chart,
                                                                                                                     bars_before,
                                                                                                                     bars_after,
                                                                                                                     msb_points_df)

    def update_markers_on_range_change(self, chart, bars_before, bars_after, msb_points_df: dt.MSBPointsDf):
        # Clear all the markers
        self.chart.clear_markers()

        if bars_before < 0:
            first_bar_pdi = self.pair_df.iloc[0].name
        else:
            first_bar_pdi = self.pair_df.iloc[int(bars_before)].name

        if bars_after < 0:
            last_bar_pdi = self.pair_df.iloc[-1].name
        else:
            last_bar_pdi = self.pair_df.iloc[-int(bars_after)].name

        msb_points_in_range = msb_points_df[(msb_points_df.pdi >= first_bar_pdi) & (msb_points_df.pdi <= last_bar_pdi)]

        self.draw_msb_points(msb_points_in_range)
        print(len(self.chart.markers))

    def draw_candlesticks(self, pair_df: dt.PairDf):
        self.pair_df = pair_df
        self.chart.set(pair_df)

    def draw_zigzag(self, zigzag_df: dt.ZigZagDf):
        line = self.chart.create_line('pivot_value')
        line.set(zigzag_df[['time', 'pivot_value']])

    def draw_msb_points(self, msb_points_df: dt.MSBPointsDf):
        plotting_df = msb_points_df.sort_values(by=['pdi'])
        for _, msb_point in msb_points_df.iterrows():
            time = self.pair_df.iloc[msb_point.pdi].time
            if msb_point.type == 'long':
                marker = self.chart.marker(time, position='above', shape='arrow_up', color='green')
            else:
                marker = self.chart.marker(time, position='below', shape='arrow_down', color='red')

    # def update_msb_points(self, msb_points_df: dt.MSBPointsDf):

    def show(self):
        self.chart.show(block=True)


def convert_timestamp_to_readable(timestamp: pd.Timestamp) -> str:
    """
    Converts a pd.Timestamp object to a readable string to be used in ID strings.

    Args:
        timestamp: The timestamp to convert.

    Returns:
        str: A string of the timestamp made readable.
    """
    utc = timestamp.to_pydatetime()

    def two_char_long(num):
        # Make the single-digit hours, minutes and seconds to double digits.
        if num >= 10:
            return str(num)
        else:
            return "0" + str(num)

    readable_format = f"{utc.year}.{utc.month}.{utc.day}/{two_char_long(utc.hour)}:{two_char_long(utc.minute)}:{two_char_long(utc.second)}"

    return readable_format
