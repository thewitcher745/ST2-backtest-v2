# A config Singleton containing the pair_name that is being processed. This is used to update the logger and to keep track of the current pair being
# processed.

class Config:
    _pair_name = None

    @classmethod
    def set_pair_name(cls, pair_name: str):
        cls._pair_name = pair_name

    @classmethod
    def get_pair_name(cls) -> str:
        return cls._pair_name
