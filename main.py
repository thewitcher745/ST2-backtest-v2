import pandas as pd
from line_profiler import profile

from algo_code.algo import Algo
from algo_code.run_algo import run_algo
from utils.general_utils import load_local_data, get_pair_list
from utils import constants
from utils.plotting import PlottingTool

plot_results = False

for pair_name in get_pair_list(constants.timeframe):
    pair_positions = run_algo(pair_name, constants.timeframe)
    # all_positions.to_csv(f'./reports/all_positions_{pair_name}.csv')

# if __name__ == '__main__' and plot_results:
#     pt = PlottingTool()
#     pt.draw_candlesticks(pair_df)
#     # pt.register_msb_point_updates(msb_points_df)
#     pt.register_ob_updates(order_blocks)
#     pt.draw_zigzag(algo.zigzag_df)
#
#     pt.show()
