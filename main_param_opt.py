import os
from datetime import timedelta
import time
import pandas as pd

from algo_code.run_algo import run_algo
from param_opt.fitness_function import calc_fitness_parameters
from param_opt.param_set_generator import parameter_sets
from utils import constants
from utils.general_utils import get_pair_list, load_local_data

plot_results = False

# List to store rows of parameter optimization data
results = []
start_time = time.time()

print("Size of parameter space: ", len(parameter_sets))
counter = 1

pair_list = get_pair_list(constants.timeframe)
all_pairs_data = {pair: load_local_data(pair, constants.timeframe) for pair in pair_list}

for params, permutation_params_dict in parameter_sets:
    print(f"Running simulation {counter} of {len(parameter_sets)}")
    if counter % 10 == 0:
        seconds_elapsed = int(time.time() - start_time)
        seconds_remaining = int(seconds_elapsed / counter * (len(parameter_sets) - counter))
        time_remaining = timedelta(seconds=seconds_remaining)

        print(f'Time elapsed: {timedelta(seconds=seconds_elapsed)}')
        print(f'Estimated time remaining: {time_remaining}')

    counter += 1
    all_pairs_exit_positions = []
    for pair_name in pair_list:
        pair_positions = run_algo(pair_name, all_pairs_data[pair_name], params)[0]
        all_pairs_exit_positions.extend(pair_positions)

    all_positions_df = pd.DataFrame(all_pairs_exit_positions)

    fitness_dict = calc_fitness_parameters(all_positions_df)
    # Combine input parameters and fitness parameters into a single dictionary
    result_row = {**permutation_params_dict, **fitness_dict}
    results.append(result_row)

    print(result_row)
    print()

# Convert the list of dictionaries to a DataFrame and write to CSV
results_df = pd.DataFrame(results)
if not os.path.exists(f'./reports/param_opt/{constants.output_filename}'):
    os.mkdir(f'./reports/param_opt/{constants.output_filename}')
results_df.to_csv(f'./reports/param_opt/{constants.output_filename}/results.csv', index=False)
