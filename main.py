from algo_code.algo import Algo
from utils.general_utils import load_local_data
from utils import constants

pair_name = "BTCUSDT"
timeframe = constants.timeframe

pair_df = load_local_data(pair_name, timeframe).iloc[:1000]

algo = Algo(pair_df, pair_name)

algo.init_zigzag()
