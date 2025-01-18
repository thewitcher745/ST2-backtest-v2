import numpy as np


def default_1234(position, params):
    if position.type == "long":
        position.stoploss = position.entry_price - params.stoploss_coeff * position.parent_ob.height
        position.target_list = np.array([
            position.entry_price + (i + 1) * params.target_coeff * position.parent_ob.height
            for i in range(params.n_targets)
        ])
    else:
        position.stoploss = position.entry_price + params.stoploss_coeff * position.parent_ob.height
        position.target_list = np.array([
            position.entry_price - (i + 1) * params.target_coeff * position.parent_ob.height
            for i in range(params.n_targets)
        ])
