import pandas as pd
from line_profiler import profile

from algo_code.algo import Algo
from utils.general_utils import load_local_data, get_pair_list
from utils import constants
from utils.plotting import PlottingTool

plot_results = True

for pair_name in get_pair_list(constants.timeframe)[:1]:
    pair_df = load_local_data(pair_name, constants.timeframe).iloc[-2000:].reset_index()

    def run_algo():
        for _ in range(1):
            algo = Algo(pair_df, pair_name)
            algo.init_zigzag()
            msb_points_df = algo.find_msb_points()
            order_blocks = algo.find_order_blocks()
            algo.process_concurrent_order_blocks()
            algo.calc_events_array()
            algo.process_events_array()

            exit_positions_list = []
            for ob in order_blocks:
                exit_positions_list.extend(ob.exit_positions)

            all_positions = pd.DataFrame(exit_positions_list)
            all_positions.to_csv('./reports/all_positions.csv')

            if __name__ == '__main__' and plot_results:
                pt = PlottingTool()
                pt.draw_candlesticks(pair_df)
                # pt.register_msb_point_updates(msb_points_df)
                pt.register_ob_updates(order_blocks)
                pt.draw_zigzag(algo.zigzag_df)

                pt.show()

    run_algo()


