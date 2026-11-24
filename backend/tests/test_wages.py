import unittest
from datetime import date
from backend.wages import LedgerAmount, earnings_paise, disbursement_paise, statement_totals


class WageRules(unittest.TestCase):
    def test_spec_example_and_advance_counted_once(self):
        workday = date(2026,11,20)
        entries = [LedgerAmount(workday,earnings_paise(60000,u),'earning') for u in [2,2,2,1]]
        entries += [LedgerAmount(workday,disbursement_paise(50000),'advance'),
                    LedgerAmount(workday,disbursement_paise(100000),'payment')]
        totals = statement_totals(entries,workday,workday)
        self.assertEqual(totals,{'opening_paise':0,'earnings_paise':210000,
                                'disbursements_paise':150000,'adjustments_paise':0,'closing_paise':60000})

    def test_half_paise_rounds_up(self):
        self.assertEqual(earnings_paise(60101,1),30051)
        self.assertEqual(earnings_paise(60101,2),60101)
        self.assertEqual(earnings_paise(60101,0),0)

    def test_float_boolean_negative_and_unknown_units_rejected(self):
        for rate,units in [(600.0,2),(True,2),(-1,2),(0,1),(60000,0.5),(60000,True),(60000,3)]:
            with self.subTest(rate=rate,units=units), self.assertRaises(ValueError):
                earnings_paise(rate,units)

    def test_statement_cutoffs_and_negative_opening(self):
        entries=[LedgerAmount(date(2026,10,31),-10000,'advance'),
                 LedgerAmount(date(2026,11,1),60000,'earning'),
                 LedgerAmount(date(2026,11,30),-20000,'payment'),
                 LedgerAmount(date(2026,12,1),90000,'earning')]
        self.assertEqual(statement_totals(entries,date(2026,11,1),date(2026,11,30)),
            {'opening_paise':-10000,'earnings_paise':60000,'disbursements_paise':20000,'adjustments_paise':0,'closing_paise':30000})

    def test_reversal_and_replacement_reconcile(self):
        day=date(2026,11,20)
        entries=[LedgerAmount(day,60000,'earning'),LedgerAmount(day,-60000,'reversal'),LedgerAmount(day,30000,'earning')]
        self.assertEqual(statement_totals(entries,day,day)['closing_paise'],30000)

    def test_earlier_rate_snapshot_is_independent_of_later_rate(self):
        earlier=LedgerAmount(date(2026,11,20),earnings_paise(60000,2),'earning')
        later=LedgerAmount(date(2026,11,21),earnings_paise(70000,2),'earning')
        self.assertEqual(earlier.amount_paise,60000)
        self.assertEqual(statement_totals([earlier,later],date(2026,11,20),date(2026,11,20))['closing_paise'],60000)

    def test_zero_payments_and_oversized_money_rejected(self):
        for amount in [0,-10,100.0,2**63]:
            with self.subTest(amount=amount),self.assertRaises(ValueError):
                disbursement_paise(amount)

    def test_invalid_date_range_rejected(self):
        with self.assertRaises(ValueError):
            statement_totals([],date(2026,11,30),date(2026,11,1))
