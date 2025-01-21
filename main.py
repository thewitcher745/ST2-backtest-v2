import pandas as pd

from algo_code.algo import Algo
from algo_code.run_algo import run_algo
from utils.general_utils import load_local_data, get_pair_list
from utils import constants
from utils.plotting import PlottingTool

plot_results = False

all_pairs_exit_positions = []
pair_counter = 1
n_pairs = len(get_pair_list(constants.timeframe))

for pair_name in get_pair_list(constants.timeframe):
    print(f'Processing {pair_counter} / {n_pairs}: {pair_name}')

    pair_df = load_local_data(pair_name, constants.timeframe).reset_index()

    algo_outputs = run_algo(pair_name, pair_df, constants)
    pair_exit_positions = algo_outputs[0]
    algo = algo_outputs[1]
    all_pairs_exit_positions.extend(pair_exit_positions)

    pair_counter += 1

all_positions_df = pd.DataFrame(all_pairs_exit_positions)
all_positions_df['Target hit times'] = all_positions_df['Target hit times'].apply(lambda x: pd.DatetimeIndex(x).tz_localize(None).to_list())

all_positions_df.to_excel(f'./reports/{constants.output_filename}')

if __name__ == '__main__' and plot_results:
    pt = PlottingTool()
    pt.draw_candlesticks(algo.pair_df)
    # pt.register_msb_point_updates(msb_points_df)
    pt.register_ob_updates(algo.ob_list)
    pt.draw_zigzag(algo.zigzag_df)

    pt.show()
