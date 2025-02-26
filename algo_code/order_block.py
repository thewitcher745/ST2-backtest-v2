from typing import Optional

import pandas as pd

import utils.general_utils as gen_utils
from algo_code.position import Position
import utils.datatypes as dt
from utils import constants


class OrderBlock:
    def __init__(self, base_candle: pd.Series | dt.Candle, ob_type: str, formation_pdi: int, params):
        if isinstance(base_candle, pd.Series):
            self.base_candle_pdi = base_candle.name
        elif isinstance(base_candle, dt.Candle):
            self.base_candle_pdi = base_candle.pdi
        else:
            self.base_candle_pdi = base_candle.Index

        # Identification
        self.base_candle = base_candle
        self.formation_pdi = formation_pdi
        self.end_pdi = -1
        self.type = ob_type
        self.id = f"OB{self.base_candle_pdi}/" + gen_utils.convert_timestamp_to_readable(base_candle.time)
        self.id += "L" if ob_type == "long" else "S"

        # Geometry
        self.top = base_candle.high
        self.bottom = base_candle.low
        self.height = abs(self.top - self.bottom)
        self.height_percentage = gen_utils.calc_candle_percentage(base_candle)

        # Each time an entry is achieved, the number of remaining bounces decreases by 1
        self.remaining_bounces = params.max_bounces

        # The position formed by the OrderBLock
        self.position = Position(self, params)

        # A list of positions that have been exit, this will be compiled into a report as the output.
        self.exit_positions = []

        # The events array is an array of events after the start (formation) of the order block for each candle. 0 means entry, -1 means (unmoved)
        # stoploss, and 1, 2, 3 etc. mean the target hits.
        self.events_array: Optional[list[float]] = None

        # Only useful for plotting
        self.end_time = None

    def __repr__(self):
        return f"OB {self.id} ({self.type})"
