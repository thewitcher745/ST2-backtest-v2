from algo_code.algo import Algo
from utils.general_utils import load_local_data
from utils import constants
from utils.plotting import PlottingTool

pair_name = "BTCUSDT"
timeframe = constants.timeframe

pair_df = load_local_data(pair_name, timeframe)

algo = Algo(pair_df, pair_name)
algo.init_zigzag()
msb_points_df = algo.find_msb_points()
print(msb_points_df)
order_blocks = algo.find_order_blocks()
position_list = [ob.position for ob in order_blocks]

if __name__ == '__main__':
    pt = PlottingTool()
    pt.draw_candlesticks(pair_df)
    pt.register_ob_updates(order_blocks)
    pt.draw_zigzag(algo.zigzag_df)

    pt.show()
