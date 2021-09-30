from datetime import date
import udi_interface
import sys
import unittest
from unittest.mock import Mock

from holidays_server import DateProvider
from holidays_server import Rule

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
udi_interface.LOGGER.handlers = []


class DateProviderTester(unittest.TestCase):

    def test_simple(self):
        provider = DateProvider()
        provider.get_now = Mock(return_value=date(2018, 7, 1))
        provider.refresh()

        self.assertTrue(provider.is_holiday('Wednesday'))
        self.assertEqual(provider.dates['today'], provider.dates['Sunday'])

    def test_rule(self):
        provider = DateProvider()
        provider.get_now = Mock(return_value=date(2018, 7, 1))

        rule = Rule('', 'WFH')
        rule.parse = Mock()
        rule.date = date(2018, 7, 2)

        provider.custom_rules.append(rule)
        provider.refresh()

        self.assertTrue(provider.is_holiday('Monday'))

    def test_weekend(self):
        provider = DateProvider()
        provider.get_now = Mock(return_value=date(2018, 7, 1))
        provider.refresh()

        self.assertTrue(provider.is_weekend('today'))

    def test_set_weekend(self):
        provider = DateProvider()
        provider.set_weekend(['Monday', 'Tuesday'])
        provider.get_now = Mock(return_value=date(2018, 7, 2))
        provider.refresh()

        self.assertTrue(provider.is_weekend('today'))

    def test_include(self):
        provider = DateProvider()
        provider.get_now = Mock(return_value=date(2018, 7, 1))
        provider.refresh()
        provider.set_include(['Independence Day'])

        self.assertTrue(provider.is_holiday('Wednesday'))

    def test_include_fail(self):
        provider = DateProvider()
        provider.get_now = Mock(return_value=date(2018, 7, 1))
        provider.refresh()
        provider.set_include(['New Year''s Day'])

        self.assertFalse(provider.is_holiday('Wednesday'))

    def test_include_multi(self):
        provider = DateProvider()
        provider.get_now = Mock(return_value=date(2018, 7, 1))
        provider.refresh()
        provider.set_include(['New Year''s Day', 'Independence Day'])

        self.assertTrue(provider.is_holiday('Wednesday'))

    def test_exclude(self):
        provider = DateProvider()
        provider.get_now = Mock(return_value=date(2018, 7, 1))
        provider.refresh()
        provider.set_exclude(['Independence Day'])

        self.assertFalse(provider.is_holiday('Wednesday'))

    def test_include_exclude(self):
        provider = DateProvider()
        provider.get_now = Mock(return_value=date(2018, 7, 1))
        provider.refresh()
        provider.set_include(['Independence Day'])
        provider.set_exclude(['New Year''s Day', 'Independence Day'])

        self.assertFalse(provider.is_holiday('Wednesday'))

if __name__ == '__main__':
    unittest.main()
