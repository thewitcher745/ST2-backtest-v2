from algo_code.algo import Algo
from utils.general_utils import load_local_data, get_pair_list
from utils import constants
from utils.plotting import PlottingTool

for pair_name in get_pair_list(constants.timeframe):
    pair_df = load_local_data(pair_name, constants.timeframe)

    algo = Algo(pair_df, pair_name)
    algo.init_zigzag()
    msb_points_df = algo.find_msb_points()
    order_blocks = algo.find_order_blocks()

# if __name__ == '__main__':
#     pt = PlottingTool()
#     pt.draw_candlesticks(pair_df)
#     pt.register_msb_point_updates(msb_points_df)
#     pt.draw_zigzag(algo.zigzag_df)
#     pt.draw_order_blocks(order_blocks)
#
#     pt.show()
