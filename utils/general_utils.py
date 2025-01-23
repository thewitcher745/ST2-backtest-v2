import numpy as np
import pandas as pd
import os

import utils.datatypes as dt
from utils import constants


def load_local_data(pair_name: str = "BTCUSDT", timeframe: str = "15m") -> dt.PairDf:
    """
    Imports the .hdf5 files associated with the indicated pair in the give timeframe.

    Args:
        pair_name (str): The symbol of the pair to load
        timeframe (str): Standardized timeframe

    Returns:
        pd.DataFrame: A dataframe containing all the OHLC data of the give pair

    """
    hdf_path: str = f"./cached_data/{timeframe}/{pair_name}.hdf5"

    pair_df = pd.DataFrame(pd.read_hdf(hdf_path))

    return dt.PairDf(pair_df)


def get_pair_list(timeframe: str = '15m'):
    # Get the pairs in cached_data/<timeframe> folder, or, if given, the pair list given through the --pl runtime argument
    if constants.pair_list_filename:
        pair_list = pd.read_csv(f'./{constants.pair_list_filename}', header=None)[0].tolist()
        print(f'Running on {len(pair_list)} pairs')
        return pair_list

    pair_list = []
    for file in os.listdir(f'./cached_data/{timeframe}'):
        if file.endswith(".hdf5"):
            pair_list.append(file.replace('.hdf5', ''))

    print(f'Running on {len(pair_list)} pairs')
    return pair_list


def convert_timestamp_to_readable(timestamp: pd.Timestamp) -> str:
    """
    Converts a pd.Timestamp object to a readable string to be used in ID strings.

    Args:
        timestamp: The timestamp to convert.

    Returns:
        str: A string of the timestamp made readable.
    """
    utc = timestamp.to_pydatetime()

    def two_char_long(num):
        # Make the single-digit hours, minutes and seconds to double digits.
        if num >= 10:
            return str(num)
        else:
            return "0" + str(num)

    readable_format = f"{utc.year}.{utc.month}.{utc.day}/{two_char_long(utc.hour)}:{two_char_long(utc.minute)}:{two_char_long(utc.second)}"

    return readable_format


def calc_candle_percentage(candle: dt.Candle):
    # Calculate the candle height as a percentage of the average of its low and high
    return abs(candle.high - candle.low) / (candle.high + candle.low) * 2 * 100


def format_time(seconds):
    """
    Convert seconds to a readable format (HH:MM:SS).
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
