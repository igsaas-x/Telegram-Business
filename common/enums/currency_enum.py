from enum import Enum


class CurrencyEnum(Enum):
    KHR = "៛"
    USD = "$"

    @classmethod
    def from_symbol(cls, symbol: str) -> str | None:
        for member in cls:
            if member.value == symbol:
                return member.name
        return None
