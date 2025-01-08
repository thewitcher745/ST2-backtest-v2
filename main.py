from lightweight_charts import Chart

from algo_code.algo import Algo
from utils.general_utils import load_local_data, PlottingTool
from utils import constants

pair_name = "BTCUSDT"
timeframe = constants.timeframe

pair_df = load_local_data(pair_name, timeframe).iloc[:5000]

algo = Algo(pair_df, pair_name)
algo.init_zigzag()
msb_points_df = algo.find_msb_points()

if __name__ == '__main__':
    pt = PlottingTool()
    pt.draw_candlesticks(pair_df)
    pt.register_msb_point_updates(msb_points_df)
    pt.draw_zigzag(algo.zigzag_df)

    pt.show()
