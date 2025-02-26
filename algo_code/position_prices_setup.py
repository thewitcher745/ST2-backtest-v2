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


def small_box_1234(position, params):
    # For very small boxes, calculate targets and stoplosses based on a box height of 1% of the price.
    if position.parent_ob.height_percentage > 1:
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

    # If the box is smaller than 1%
    elif position.parent_ob.height_percentage < 1:
        one_percent_box_height = 0.01 * position.parent_ob.height
        if position.type == "long":
            position.stoploss = position.entry_price - params.stoploss_coeff * one_percent_box_height
            position.target_list = np.array([
                position.entry_price + (i + 1) * params.target_coeff * one_percent_box_height
                for i in range(params.n_targets)
            ])
        else:
            position.stoploss = position.entry_price + params.stoploss_coeff * one_percent_box_height
            position.target_list = np.array([
                position.entry_price - (i + 1) * params.target_coeff * one_percent_box_height
                for i in range(params.n_targets)
            ])

