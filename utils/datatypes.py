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
