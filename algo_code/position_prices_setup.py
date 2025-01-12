import numpy as np

import utils.constants as constants


def default_1234(position):
    if position.type == "long":
        position.stoploss = position.entry_price - constants.stoploss_coeff * position.parent_ob.height
        position.target_list = np.array([
            position.entry_price + 1 * constants.target_coeff * position.parent_ob.height,
            position.entry_price + 2 * constants.target_coeff * position.parent_ob.height,
            position.entry_price + 3 * constants.target_coeff * position.parent_ob.height,
            position.entry_price + 4 * constants.target_coeff * position.parent_ob.height,
        ])
    else:
        position.stoploss = position.entry_price + constants.stoploss_coeff * position.parent_ob.height
        position.target_list = np.array([
            position.entry_price - 1 * constants.target_coeff * position.parent_ob.height,
            position.entry_price - 2 * constants.target_coeff * position.parent_ob.height,
            position.entry_price - 3 * constants.target_coeff * position.parent_ob.height,
            position.entry_price - 4 * constants.target_coeff * position.parent_ob.height,
        ])

