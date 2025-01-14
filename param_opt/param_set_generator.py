# param_opt/param_set_generator.py

import itertools
from utils import constants

param_cases = {
    'zigzag_window_size': [9, 10, 11, 12, 13, 14, 15],
    'stoploss_coeff': [1, 1.2, 1.4, 1.6, 1.8, 2],
    'target_coeff': [0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2],
    'max_bounces': [1, 2, 3],
    'max_concurrent': [1, 2, 3, 4, 5]
}


class Params:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def create_parameter_sets(param_cases):
    keys = param_cases.keys()
    values = param_cases.values()
    permutations = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
    return permutations


def get_params(param_cases):
    permutation_params_dict = create_parameter_sets(param_cases)
    combined_params = []
    for param_set in permutation_params_dict:
        combined = {**vars(constants), **param_set}
        combined_params.append((Params(**combined), param_set))
    return combined_params


parameter_sets = get_params(param_cases)
