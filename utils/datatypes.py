from typing import NamedTuple

import pandas as pd


class TypedDataFrame(pd.DataFrame):
    @property
    def _constructor(self):
        return TypedDataFrame

    @property
    def _constructor_sliced(self):
        return pd.Series


class PairDf(TypedDataFrame):
    @property
    def time(self) -> pd.Series:
        return self['time']

    @property
    def high(self) -> pd.Series:
        return self['high']

    @property
    def low(self) -> pd.Series:
        return self['low']

    @property
    def close(self) -> pd.Series:
        return self['close']

    @property
    def open(self) -> pd.Series:
        return self['open']

    @property
    def candle_color(self) -> pd.Series:
        return self['candle_color']


class ZigZagDf(TypedDataFrame):
    @property
    def time(self) -> pd.Series:
        return self['time']

    @property
    def pivot_value(self) -> pd.Series:
        return self['pivot_value']

    @property
    def pivot_type(self) -> pd.Series:
        return self['pivot_type']

    @property
    def pdi(self):
        return self['pdi']


class Candle(NamedTuple):
    pdi: int
    time: pd.Timestamp
    high: float
    low: float
    close: float = None
    open: float = None
    candle_color: str = 'green'


# Define the named tuple
class MSBPoint(NamedTuple):
    pdi: int
    msb_value: float
    type: str
    formation_pdi: int


class MSBPointsDf(TypedDataFrame):
    @property
    def pdi(self) -> pd.Series | int:
        return self['pdi']

    @property
    def msb_value(self) -> pd.Series | float:
        return self['msb_value']

    @property
    def type(self) -> pd.Series | str:
        return self['type']

    @property
    def formation_pdi(self) -> pd.Series | int:
        return self['formation_pdi']
