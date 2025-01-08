from typing import Union, Literal
import pandas as pd

import algo_code.position_prices_setup as setup
import utils.constants as constants


class Position:
    def __init__(self, parent_ob):
        self.parent_ob = parent_ob
        self.entry_price = parent_ob.top if parent_ob.type == "long" else parent_ob.bottom

        self.type = parent_ob.type

        self.status: str = "ACTIVE"
        self.entry_pdi = None
        self.qty: float = 0
        self.highest_target: int = 0
        self.target_hit_pdis: list[int] = []
        self.exit_pdi = None
        self.portioned_qty = []
        self.net_profit = None

        self.target_list = []
        self.stoploss = None

        # Set up the target list nd stoploss using a function which operates on the "self" object and directly manipulates the instance.
        setup.default_1234(self)