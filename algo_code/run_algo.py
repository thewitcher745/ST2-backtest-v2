import pandas as pd

from algo_code.algo import Algo
from utils.general_utils import load_local_data


def run_algo(pair_name, timeframe) -> pd.DataFrame:
    pair_df = load_local_data(pair_name, timeframe).reset_index()
    algo = Algo(pair_df, pair_name)
    algo.init_zigzag()
    algo.find_msb_points()
    order_blocks = algo.find_order_blocks()
    algo.process_concurrent_order_blocks()
    algo.calc_events_array()
    algo.process_events_array()

    exit_positions_list = []
    for ob in order_blocks:
        exit_positions_list.extend(ob.exit_positions)

    pair_positions = pd.DataFrame(exit_positions_list)

    return pair_positions