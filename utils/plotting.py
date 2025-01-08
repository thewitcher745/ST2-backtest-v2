from lightweight_charts import Chart
from lightweight_charts.drawings import TwoPointDrawing

import utils.datatypes as dt
from algo_code.order_block import OrderBlock


class PlottingTool:
    def __init__(self):
        self.chart = Chart()
        self.chart.legend(visible=True, ohlc=True, color_based_on_candle=True, font_size=15)

        self.pair_df: dt.PairDf | None = None

        self.ob_drawings: list[TwoPointDrawing] = []

    def register_msb_point_updates(self, msb_points_df: dt.MSBPointsDf):
        # Subscribe to the event of the chart's range change
        self.chart.events.range_change += lambda chart, bars_before, bars_after: self.update_msb_points_on_range_change(chart,
                                                                                                                        bars_before,
                                                                                                                        bars_after,
                                                                                                                        msb_points_df)

    def register_ob_updates(self, order_blocks: list[OrderBlock]):
        self.chart.events.range_change += lambda chart, bars_before, bars_after: self.update_order_blocks_on_range_change(chart,
                                                                                                                          bars_before,
                                                                                                                          bars_after,
                                                                                                                          order_blocks)

    def update_msb_points_on_range_change(self, chart, bars_before, bars_after, msb_points_df: dt.MSBPointsDf):
        if bars_before < 0:
            first_bar_pdi = self.pair_df.iloc[0].name
        else:
            first_bar_pdi = self.pair_df.iloc[int(bars_before)].name

        if bars_after < 0:
            last_bar_pdi = self.pair_df.iloc[-1].name
        else:
            last_bar_pdi = self.pair_df.iloc[-int(bars_after)].name

        range_start_time = self.pair_df.iloc[first_bar_pdi].time.timestamp()  # UNIX
        range_end_time = self.pair_df.iloc[last_bar_pdi].time.timestamp()  # UNIX

        msb_points_in_range = msb_points_df[(msb_points_df.pdi >= first_bar_pdi) & (msb_points_df.pdi <= last_bar_pdi)]
        markers_out_of_range_ids = [marker_id for marker_id in self.chart.markers.keys() if
                                    self.chart.markers[marker_id]['time'] < range_start_time or self.chart.markers[marker_id][
                                        'time'] > range_end_time]

        for marker_id in markers_out_of_range_ids:
            self.chart.remove_marker(marker_id)

        # Draw the markers from msb_points_in_range that aren't already in the marker list.
        current_marker_times = [marker['time'] for marker in self.chart.markers.values()]
        msb_points_in_range_unix_times = self.pair_df.iloc[msb_points_in_range.pdi].time.apply(lambda x: x.timestamp())
        boolfilter = ~msb_points_in_range_unix_times.isin(current_marker_times).reset_index(drop=True)

        msb_points_to_draw = msb_points_in_range.reset_index()[boolfilter]

        self.draw_msb_points(msb_points_to_draw)

    def update_order_blocks_on_range_change(self, chart, bars_before, bars_after, order_blocks: list[OrderBlock]):
        if bars_before < 0:
            first_bar_pdi = self.pair_df.iloc[0].name
        else:
            first_bar_pdi = self.pair_df.iloc[int(bars_before)].name

        if bars_after < 0:
            last_bar_pdi = self.pair_df.iloc[-1].name
        else:
            last_bar_pdi = self.pair_df.iloc[-int(bars_after)].name

        range_start_time = self.pair_df.iloc[first_bar_pdi].time
        range_end_time = self.pair_df.iloc[last_bar_pdi].time

        # Display order blocks if their starts or ends are within the bounds
        order_blocks_in_range = [order_block for order_block in order_blocks if (first_bar_pdi <= order_block.base_candle_pdi <= last_bar_pdi) or
                                 (first_bar_pdi <= order_block.base_candle_pdi + 20 <= last_bar_pdi)]

        # Delete the now-out of range order blocks
        out_of_range_obs = [ob_drawing for ob_drawing in self.ob_drawings if
                            range_end_time < ob_drawing.start_time or ob_drawing.end_time < range_start_time]
        out_of_range_obs_times = [ob_drawing.start_time for ob_drawing in out_of_range_obs]

        for ob_drawing in out_of_range_obs:
            ob_drawing.delete()

        self.ob_drawings = [ob_drawing for ob_drawing in self.ob_drawings if ob_drawing.start_time not in out_of_range_obs_times]

        new_obs_to_draw = [order_block for order_block in order_blocks_in_range if
                           self.pair_df.iloc[order_block.base_candle_pdi].time not in [ob_drawing.start_time for ob_drawing in self.ob_drawings]]

        self.draw_order_blocks(new_obs_to_draw)

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

    def draw_order_blocks(self, order_blocks: list[OrderBlock]):
        for order_block in order_blocks:
            ob_start_time = self.pair_df.iloc[order_block.base_candle_pdi].time
            ob_end_time = self.pair_df.iloc[order_block.end_pdi].time

            ob_formation_time = self.pair_df.iloc[order_block.formation_pdi].time
            ob_start_value = order_block.top
            ob_end_value = order_block.bottom

            color = 'rgba(10, 110, 17, 0.6)' if order_block.type == 'long' else 'rgba(130, 5, 3, 0.6)'
            # inactive_color = 'rgba(10, 110, 17, 0.2)' if order_block.type == 'long' else 'rgba(130, 5, 3, 0.2)'
            border_color = 'rgba(10, 110, 17, 0.9)' if order_block.type == 'long' else 'rgba(130, 5, 3, 0.9)'
            # inactive_border_color = 'rgba(10, 110, 17, 0.6)' if order_block.type == 'long' else 'rgba(130, 5, 3, 0.6)'

            # ob_inactive_drawing = self.chart.box(ob_start_time, ob_start_value, ob_formation_time, ob_end_value, color=inactive_border_color,
            #                                      fill_color=inactive_color)
            ob_drawing = self.chart.box(ob_formation_time, ob_start_value, ob_end_time, ob_end_value, color=border_color, fill_color=color)

            # self.ob_drawings.append(ob_inactive_drawing)
            self.ob_drawings.append(ob_drawing)

    def show(self):
        self.chart.show(block=True)
