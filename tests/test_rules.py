from datetime import date
from datetime import datetime
import udi_interface
import sys
import unittest

from holidays_server import Rule

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
udi_interface.LOGGER.handlers = []


class RuleTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rule = Rule()
        cls.rule.base = datetime(2018, 5, 25)

    def test_simple(self):
        RuleTester.rule.parseRule("5th of november 2018")
        expected = date(RuleTester.rule.base.year, 11, 5)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_fail(self):
        RuleTester.rule.parseRule("5th of november")
        self.assertIsNone(RuleTester.rule.date)

    def test_on_date(self):
        RuleTester.rule.parseRule("every 5th of november")
        expected = date(RuleTester.rule.base.year, 11, 5)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_on_date_to_date(self):
        RuleTester.rule.parseRule("every 5th of november to December 31st")
        expected = date(RuleTester.rule.base.year, 11, 5)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_on_date_to_date_next_year(self):
        RuleTester.rule.parseRule('every 5th of november to January 31st')
        expected = date(RuleTester.rule.base.year, 11, 5)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_on_date_to_date_past(self):
        RuleTester.rule.parseRule('every 5th of november to January 31st ' + str(RuleTester.rule.base.year - 1))

        self.assertIsNone(RuleTester.rule.date)

    def test_on_date_from_date(self):
        RuleTester.rule.parseRule("every 5th of november from Jan 31st")
        expected = date(RuleTester.rule.base.year, 11, 5)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_on_date_from_date_future(self):
        RuleTester.rule.parseRule("every 5th of november from Dec 31st")

        self.assertIsNone(RuleTester.rule.date)

    def test_on_date_from_date_past(self):
        RuleTester.rule.parseRule('every 5th of november from Dec 31st ' + str(RuleTester.rule.base.year - 1))
        expected = date(RuleTester.rule.base.year, 11, 5)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_on_date_from_to_date(self):
        RuleTester.rule.parseRule("every 5th of november from Jan 31st to Dec 19th")
        expected = date(RuleTester.rule.base.year, 11, 5)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_weekday(self):
        RuleTester.rule.parseRule("every wednesday")
        expected = date(RuleTester.rule.base.year, 5, 30)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_weekday_today(self):
        RuleTester.rule.parseRule("every friday")
        expected = date(RuleTester.rule.base.year, 5, 25)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_on_date_today(self):
        RuleTester.rule.parseRule("every 5/25")
        expected = date(RuleTester.rule.base.year, 5, 25)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_day_of_month_past(self):
        RuleTester.rule.parseRule("every 5th of the month")
        expected = date(RuleTester.rule.base.year, 6, 5)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_day_of_month_today(self):
        RuleTester.rule.parseRule("every 25th of the month")
        expected = date(RuleTester.rule.base.year, 5, 25)

        self.assertEqual(RuleTester.rule.date, expected)

    def test_day_of_month_future(self):
        RuleTester.rule.parseRule("every 30th of the month")
        expected = date(RuleTester.rule.base.year, 5, 30)

        self.assertEqual(RuleTester.rule.date, expected)

if __name__ == '__main__':
    unittest.main()
