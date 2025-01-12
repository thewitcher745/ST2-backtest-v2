import pandas as pd
import numpy as np


def calc_fitness_parameters(positions_df: pd.DataFrame) -> dict:
    # Calculates the fitness function from a list of positions.
    net_profits = positions_df['Net profit'].to_numpy()
    return {
        'net_profit': float(sum(net_profits)),
        'winrate': len(np.where(net_profits > 0)[0]) / len(net_profits) * 100,
    }
