import pandas as pd

from algo_code.algo import Algo
import utils.datatypes as dt


def run_algo(pair_name: str, pair_df: dt.PairDf, params) -> tuple[list, Algo]:
    algo = Algo(pair_df, pair_name, params)
    algo.init_zigzag()
    algo.find_msb_points()
    order_blocks = algo.find_order_blocks()
    algo.process_concurrent_order_blocks()
    algo.calc_events_array()
    algo.process_events_array()

    pair_exit_positions = []
    for ob in order_blocks:
        pair_exit_positions.extend(ob.exit_positions)

    return pair_exit_positions, algo
