# param_opt/param_set_generator.py

import itertools
from utils import constants

param_cases = {
    'zigzag_window_size': [9, 11, 13, 15],
    'stoploss_coeff': [0.8, 1.2, 1.6, 2],
    'target_coeff': [0.5, 1, 1.5, 2],
    'max_bounces': [1, 2, 3],
    'max_concurrent': [1, 2, 3, 4],
    'trailing_sl_target_id': [0, 1, 2]
}


class Params:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __reduce__(self):
        # Return a tuple with the callable and arguments to reconstruct the object
        return self.__class__, (), self.__dict__

    def __setstate__(self, state):
        # Restore the object's state from the given state
        self.__dict__.update(state)


def create_parameter_sets(param_cases):
    keys = param_cases.keys()
    values = param_cases.values()
    permutations = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
    return permutations


def get_params(param_cases):
    permutation_params_dict = create_parameter_sets(param_cases)
    combined_params = []

    # Filter constants to include only int, float, or str values
    filtered_constants = {k: v for k, v in vars(constants).items() if isinstance(v, (int, float, str))}

    for param_set in permutation_params_dict:
        # Filter param_set to include only int, float, or str values
        filtered_param_set = {k: v for k, v in param_set.items() if isinstance(v, (int, float, str))}
        # Combine with filtered constants
        combined = {**filtered_constants, **filtered_param_set}
        combined_params.append((Params(**combined), filtered_param_set))
    return combined_params


parameter_sets = get_params(param_cases)
