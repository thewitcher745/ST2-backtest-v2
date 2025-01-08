import pandas as pd

import utils.general_utils as gen_utils
from algo_code.position import Position


class OrderBlock:
    def __init__(self, base_candle: pd.Series, ob_type: str, formation_pdi: int):
        if isinstance(base_candle, pd.Series):
            self.base_candle_pdi = base_candle.name
        else:
            self.base_candle_pdi = base_candle.Index

        # Identification
        self.base_candle = base_candle
        self.formation_pdi = formation_pdi
        self.type = ob_type
        self.id = f"OB{self.base_candle_pdi}/" + gen_utils.convert_timestamp_to_readable(base_candle.time)
        self.id += "L" if ob_type == "long" else "S"

        # Geometry
        self.top = base_candle.high
        self.bottom = base_candle.low
        self.height = self.top - self.bottom

        self.bounces = 0

        # The position formed by the OrderBLock
        self.position = Position(self)

        # Only useful for plotting
        self.end_time = None

    def __repr__(self):
        return f"OB {self.id} ({self.type})"
