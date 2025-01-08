import pandas as pd
import os

import utils.datatypes as dt


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

    # Add the candle color to the return value
    pair_df['candle_color'] = pair_df.apply(lambda row: 'green' if row.close > row.open else 'red', axis=1)

    return dt.PairDf(pair_df)


def get_pair_list(timeframe: str = '15m'):
    # Get the pairs in cached_data/<timeframe> folder
    pair_list = []
    for file in os.listdir(f'./cached_data/{timeframe}'):
        if file.endswith(".hdf5"):
            pair_list.append(file.replace('.hdf5', ''))

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
