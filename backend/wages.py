"""Integer-paise calculation rules for the upcoming persistent wage ledger.

This module does not write attendance or transfer money. Financial API integration
must preserve these rules and enforce uniqueness/ownership in PostgreSQL.
"""
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Literal

BIGINT_MAX = 2**63 - 1


def integer_paise(value: int, *, positive: bool = False) -> int:
    if type(value) is not int:
        raise ValueError('Money must be integer paise')
    if abs(value) > BIGINT_MAX or (positive and value <= 0):
        raise ValueError('Money is outside the supported range')
    return value


def earnings_paise(daily_rate_paise: int, half_day_units: int) -> int:
    """0/1/2 units mean absent/half-day/full-day. Round half a paise up."""
    rate = integer_paise(daily_rate_paise, positive=True)
    if type(half_day_units) is not int or half_day_units not in (0,1,2):
        raise ValueError('Attendance must be 0, 1 or 2 half-day units')
    return integer_paise((rate * half_day_units + 1) // 2)


def disbursement_paise(amount_paise: int) -> int:
    """An advance or a wage payment reduces the outstanding balance once."""
    return -integer_paise(amount_paise, positive=True)


@dataclass(frozen=True)
class LedgerAmount:
    effective_date: date
    amount_paise: int
    kind: Literal['earning','advance','payment','adjustment','reversal']

    def __post_init__(self):
        integer_paise(self.amount_paise)
        if type(self.effective_date) is not date:
            raise ValueError('Ledger date must be a work date, not a timestamp')
        if self.kind not in ('earning','advance','payment','adjustment','reversal'):
            raise ValueError('Unknown ledger entry kind')
        if self.kind == 'earning' and self.amount_paise < 0:
            raise ValueError('Earnings cannot be negative')
        if self.kind in ('advance','payment') and self.amount_paise >= 0:
            raise ValueError('Disbursements must reduce the balance')


def statement_totals(entries: Iterable[LedgerAmount], start: date, end: date) -> dict[str,int]:
    """Inclusive period totals. Earlier postings form the opening balance."""
    if type(start) is not date or type(end) is not date or start > end:
        raise ValueError('Invalid statement date range')
    opening = period = earnings = disbursements = adjustments = 0
    for entry in entries:
        if entry.effective_date < start:
            opening += entry.amount_paise
        elif entry.effective_date <= end:
            period += entry.amount_paise
            if entry.kind == 'earning':
                earnings += entry.amount_paise
            elif entry.kind in ('advance','payment'):
                disbursements -= entry.amount_paise
            else:
                adjustments += entry.amount_paise
    return { 'opening_paise':integer_paise(opening), 'earnings_paise':integer_paise(earnings),
             'disbursements_paise':integer_paise(disbursements), 'adjustments_paise':integer_paise(adjustments),
             'closing_paise':integer_paise(opening + period) }
