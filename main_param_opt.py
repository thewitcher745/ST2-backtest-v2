import os
import time
import pandas as pd
from multiprocessing import Pool

from algo_code.run_algo import run_algo
from param_opt.fitness_function import calc_fitness_parameters
from param_opt.param_set_generator import parameter_sets
from utils import constants
from utils.general_utils import get_pair_list, load_local_data, format_time


def process_pair(pair_name, params, pair_data):
    """
    Helper function to process a single pair with the given parameters.
    """
    pair_positions = run_algo(pair_name, pair_data, params)[0]
    return pair_positions


def single_threaded_version(pair_list, all_pairs_data):
    """
    Single-threaded version of the parameter optimization code.
    """
    start_time = time.time()
    results = []

    print("Running single-threaded version...")
    for params, permutation_params_dict in parameter_sets:
        all_pairs_exit_positions = []
        for pair_name in pair_list:
            pair_positions = process_pair(pair_name, params, all_pairs_data[pair_name])
            all_pairs_exit_positions.extend(pair_positions)

        all_positions_df = pd.DataFrame(all_pairs_exit_positions)
        fitness_dict = calc_fitness_parameters(all_positions_df)
        result_row = {**permutation_params_dict, **fitness_dict}

        print(result_row)
        print()

        results.append(result_row)

    # Convert the list of dictionaries to a DataFrame and write to CSV
    results_df = pd.DataFrame(results)
    if not os.path.exists(f'./reports/param_opt/{constants.output_filename}'):
        os.mkdir(f'./reports/param_opt/{constants.output_filename}')
    results_df.to_csv(f'./reports/param_opt/{constants.output_filename}/results_single_threaded.csv', index=False)

    elapsed_time = time.time() - start_time
    print(f"Single-threaded execution time: {format_time(elapsed_time)}")


def multiprocessing_version(pair_list, all_pairs_data):
    """
    Multiprocessing version of the parameter optimization code.
    """
    start_time = time.time()
    results = []

    print("Running multiprocessing version...")
    total_parameter_sets = len(parameter_sets)  # Total number of parameter sets to process
    print(f'Parameter space size: {total_parameter_sets}')

    for i, (params, permutation_params_dict) in enumerate(parameter_sets, 1):
        all_pairs_exit_positions = []
        with Pool(processes=constants.max_processes) as pool:
            backtest_results = pool.starmap(process_pair, [(pair_name, params, all_pairs_data[pair_name]) for pair_name in pair_list])
            for result in backtest_results:
                all_pairs_exit_positions.extend(result)

        all_positions_df = pd.DataFrame.from_dict(all_pairs_exit_positions)
        fitness_dict = calc_fitness_parameters(all_positions_df)
        result_row = {**permutation_params_dict, **fitness_dict}

        print(result_row)
        print()

        results.append(result_row)

        # Display progress every 10 parameter sets
        if i % 10 == 0 or i == total_parameter_sets:
            elapsed_time = time.time() - start_time
            time_per_set = elapsed_time / i
            remaining_sets = total_parameter_sets - i
            estimated_time_remaining = time_per_set * remaining_sets

            print(f"Processed {i}/{total_parameter_sets} parameter sets.")
            print(f"Elapsed time: {format_time(elapsed_time)}.")
            print(f"Estimated time remaining: {format_time(estimated_time_remaining)}.")
            print()

    # Convert the list of dictionaries to a DataFrame and write to CSV

    results_df = pd.DataFrame(results)
    if not os.path.exists(f'./reports/param_opt/{constants.output_filename}'):
        os.mkdir(f'./reports/param_opt/{constants.output_filename}')
    results_df.to_csv(f'./reports/param_opt/{constants.output_filename}/results_multiprocessing.csv', index=False)

    elapsed_time = time.time() - start_time
    print(f"Multiprocessing execution time: {format_time(elapsed_time)}")


# Run both versions and compare their execution times
if __name__ == "__main__":
    pair_list = get_pair_list(constants.timeframe)
    all_pairs_data = {pair: load_local_data(pair, constants.timeframe) for pair in pair_list}

    # single_threaded_version(pair_list, all_pairs_data)
    multiprocessing_version(pair_list, all_pairs_data)
