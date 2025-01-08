import pandas as pd

import utils.general_utils as gen_utils
from algo_code.position import Position
import utils.datatypes as dt
from utils import constants


class OrderBlock:
    def __init__(self, base_candle: pd.Series | dt.Candle, ob_type: str, formation_pdi: int):
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
        self.height = self.top - self.bottom

        # Each time an entry is achieved, the number of remaining bounces decreases by 1
        self.remaining_bounces = constants.max_bounces

        # The position formed by the OrderBLock
        self.position = Position(self)

        # Only useful for plotting
        self.end_time = None

    def __repr__(self):
        return f"OB {self.id} ({self.type})"
