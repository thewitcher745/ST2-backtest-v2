import numpy as np

import utils.constants as constants


def default_1234(position, params):
    if position.type == "long":
        position.stoploss = position.entry_price - params.stoploss_coeff * position.parent_ob.height
        position.target_list = np.array([
            position.entry_price + 1 * params.target_coeff * position.parent_ob.height,
            position.entry_price + 2 * params.target_coeff * position.parent_ob.height,
            position.entry_price + 3 * params.target_coeff * position.parent_ob.height,
            position.entry_price + 4 * params.target_coeff * position.parent_ob.height,
        ])
    else:
        position.stoploss = position.entry_price + params.stoploss_coeff * position.parent_ob.height
        position.target_list = np.array([
            position.entry_price - 1 * params.target_coeff * position.parent_ob.height,
            position.entry_price - 2 * params.target_coeff * position.parent_ob.height,
            position.entry_price - 3 * params.target_coeff * position.parent_ob.height,
            position.entry_price - 4 * params.target_coeff * position.parent_ob.height,
        ])

