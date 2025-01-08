from lightweight_charts import Chart

from algo_code.algo import Algo
from utils.general_utils import load_local_data
from utils.plotting import PlottingTool
from utils import constants

pair_name = "BTCUSDT"
timeframe = constants.timeframe

pair_df = load_local_data(pair_name, timeframe)[:70000]

algo = Algo(pair_df, pair_name)
algo.init_zigzag()
msb_points_df = algo.find_msb_points()
order_blocks = algo.find_order_blocks()

if __name__ == '__main__':
    pt = PlottingTool()
    pt.draw_candlesticks(pair_df)
    pt.register_ob_updates(order_blocks)
    pt.draw_zigzag(algo.zigzag_df)

    pt.show()
