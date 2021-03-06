#!/usr/bin/env python3

import calendar
import click
import dateparser
from datetime import date
from datetime import datetime
from datetime import timedelta
import holidays
import udi_interface
from udi_interface import LOGGER
from udi_interface import Custom
import time


class Rule(object):

    START_TOKEN = 'every'
    FROM_TOKEN = 'from'
    TO_TOKEN = 'to'
    MONTHLY_TOKEN = 'of the month'

    def __init__(self, rule='', desc=''):
        self.date = None
        self.base = datetime.today()
        self.rule = rule
        self.desc = desc

    def parse(self):
        self.parseRule(self.rule)

    def parseRule(self, ruleStr):
        self.date = None
        '''
            Parses rule string:
            every <day of the week> | <date> | <nth> of the month [ from <date> [ to <date> ]]
            <absolute date>
        '''
        if not ruleStr.startswith(Rule.START_TOKEN):
            self.date = dateparser.parse(ruleStr,
                                         settings={
                                             'RELATIVE_BASE': self.base,
                                             'STRICT_PARSING': True
                                         })
            if self.date is not None:
                self.date = self.date.date()
            return

        ruleStr = ruleStr[len(Rule.START_TOKEN):]

        toPos = ruleStr.find(Rule.TO_TOKEN)
        if toPos > 0:
            toDate = dateparser.parse(ruleStr[toPos + len(Rule.TO_TOKEN):],
                                      settings={
                                          'PREFER_DATES_FROM': 'future',
                                          'RELATIVE_BASE': self.base
                                      }).date()
            if self.base.date() > toDate:
                return

            ruleStr = ruleStr[:toPos]

        fromPos = ruleStr.find(Rule.FROM_TOKEN)
        if fromPos > 0:
            fromDate = dateparser.parse(ruleStr[fromPos +
                                                len(Rule.FROM_TOKEN):],
                                        settings={
                                            'RELATIVE_BASE': self.base
                                        }).date()

            if self.base.date() < fromDate:
                return
            ruleStr = ruleStr[:fromPos]

        dayPos = ruleStr.find(Rule.MONTHLY_TOKEN)
        if dayPos > 0:
            ruleStr = ruleStr[:dayPos]
            self.date = dateparser.parse(str(self.base.month) + '/' + ruleStr,
                                         settings={
                                             'RELATIVE_BASE': self.base
                                         }).date()
            if self.date < self.base.date():
                self.date = dateparser.parse(str(self.base.month + 1) + '/' +
                                             ruleStr,
                                             settings={
                                                 'RELATIVE_BASE': self.base
                                             }).date()
        else:
            future = dateparser.parse(ruleStr,
                                      settings={
                                          'PREFER_DATES_FROM': 'future',
                                          'RELATIVE_BASE': self.base
                                      }).date()
            past = dateparser.parse(ruleStr,
                                    settings={
                                        'RELATIVE_BASE': self.base
                                    }).date()

            # workaround for day of the week parsting, which is never TODAY
            # either last week or next
            diff = (future - past).days
            if diff == 7:
                self.date = future
            elif diff == 14:
                self.date = future - timedelta(7)
            else:
                self.date = past


class DateProvider(object):

    TODAY = 'today'
    TOMORROW = 'tomorrow'

    def __init__(self,
                 country='US',
                 weekend=['Saturday', 'Sunday'],
                 include_holidays='',
                 exclude_holidays=''):
        self.dates = {}
        self.country = country
        self.holidays = holidays.CountryHoliday(country)
        self.set_weekend(weekend)
        self.set_include(include_holidays)
        self.set_exclude(exclude_holidays)

        self.custom_rules = []
        self.refresh()

    def get_holiday_list(self):
        self.holidays.get(date.today())
        return list(self.holidays.values())

    def add_custom_rule(self, rule, desc):
        self.custom_rules.append(Rule(rule, desc))

    def get_now(self):
        return date.today()

    def set_weekend(self, weekend):
        self.weekend = {}
        for day in weekend:
            self.weekend[day] = 'weekend'

    def set_include(self, list):
        self.include = {}
        for day in list:
            if len(day) > 0:
                self.include[day] = True

    def set_exclude(self, list):
        self.exclude = {}
        for day in list:
            if len(day) > 0:
                self.exclude[day] = True

    def refresh(self):
        self.holidays = holidays.CountryHoliday(self.country)
        now = self.get_now()
        self.dates[DateProvider.TODAY] = now
        self.dates[DateProvider.TOMORROW] = now + timedelta(1)

        for i in range(0, 7):
            dt = now + timedelta(i)
            self.dates[calendar.day_name[dt.weekday()]] = dt

        for rule in self.custom_rules:
            rule.parse()
            if rule.date is not None:
                self.holidays.append({rule.date: rule.desc})

    def is_holiday(self, key):
        result = self.holidays.get(self.dates[key])
        if (result is not None
                and (len(self.include) == 0 or result in self.include)
                and result not in self.exclude):
            LOGGER.debug('Holiday found for Key %s, Date %s', key,
                         self.dates[key])
            return True

        return False

    def is_weekend(self, key):
        result = self.weekend.get(calendar.day_name[self.dates[key].weekday()])
        if result is not None:
            LOGGER.debug('Weekend found for Key %s, Date %s', key,
                         self.dates[key])
            return True
        return False

    def is_day_off(self, key):
        return self.is_weekend(key) or self.is_holiday(key)


class Controller(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(Controller, self).__init__(polyglot, primary, address, name)
        self.dateProvider = DateProvider('US')
        self.currentDate = None
        self.poly = polyglot
        self.TypedParameters = Custom(polyglot, "customtypedparams")
        self.customData = Custom(polyglot, "customdata")

        polyglot.subscribe(polyglot.START, self.start, address)
        polyglot.subscribe(polyglot.CUSTOMTYPEDPARAMS, self.typeParamsHandler)
        polyglot.subscribe(polyglot.CUSTOMTYPEDDATA, self.parameterHandler)
        polyglot.subscribe(polyglot.POLL, self.poll)

        LOGGER.error('Loading typed parameters now....')
        self.TypedParameters.load([
            {
                'name': 'country',
                'title': 'Country',
                'desc': 'Country to get holidays for',
                'defaultValue': 'US',
                'isRequired': True
            }, {
                'name': 'includeHolidays',
                'title': 'Include Holidays',
                'desc': 'List of holidays to include (leave empty to include all)',
                'isList': True,
                'isRequired': True
            }, {
                'name': 'excludeHolidays',
                'title': 'Exclude Holidays',
                'desc': 'List of holidays to exclude',
                'isList': True,
                'isRequired': True
            }, {
                'name': 'weekend',
                'title': 'Weekend',
                'desc': 'Normal weekend (days off) days',
                'defaultValue': ['Saturday', 'Sunday'],
                'isList': True,
                'isRequired': True
            }, {
                'name': 'rules',
                'title': 'Rules',
                'desc': 'Rules defining days off',
                'isList': True,
                'params': [
                    {
                    'name': 'description',
                    'title': 'Description',
                    'isRequired': True
                    },
                    {
                    'name': 'dateStr',
                    'title': 'Date String',
                    'isRequired': True
                    },
                ]
            }
        ], True)
        LOGGER.error('typed parameters = {}'.format(self.TypedParameters))

        polyglot.ready()
        polyglot.addNode(self, conn_status="ST")

    def start(self):
        #self.poly.save_typed_params(params)
        self.poly.updateProfile()

        self.addHolidaysList()

        LOGGER.info('Started HolidayServer')
        self.discover()
        self.setDriver('ST', 1)

    def typeParamsHandler(self, params):
        LOGGER.error(params)

    def addHolidaysList(self):
        cfgdata = self.poly.getMarkDownData('POLYGLOT_CONFIG.md')
        data = '<h3>Known Holidays</h3><ul>'
        for holiday in self.dateProvider.get_holiday_list():
            data += '<li>' + holiday + '</li>'
        data += '</ul>'
        cfgdata += data
        self.poly.setCustomParamsDoc(cfgdata)

    def poll(self, pollflag):
        if 'longPoll' in pollflag:
            if self.currentDate != date.today():
                LOGGER.debug('New date detected. Recalculating nodes')
                self.refresh()
                self.currentDate = date.today()

    def refresh(self):
        self.setDriver('ST', 1)
        self.dateProvider.refresh()
        for node in self.poly.nodes():
            if node != self:
                node.refresh()

    def parameterHandler(self, params):
        if not params:
            return

        if self.dateProvider.country != params['country']:
            self.dateProvider = DateProvider(params['country'])
            self.addHolidaysList()

        self.dateProvider.set_include(params['includeHolidays'])
        self.dateProvider.set_exclude(params['excludeHolidays'])
        self.dateProvider.set_weekend(params['weekend'])
        self.dateProvider.custom_rules = []
        rules = params.get('rules')
        if rules:
            for rule in rules:
                self.dateProvider.add_custom_rule(rule['dateStr'],
                                                  rule['description'])
        self.refresh()

    def discover(self, *args, **kwargs):
        # get key 'customDates' from custom data?
        #self.customDates = self.polyConfig.get('customData', {}).get('customDates', {})
        self.customDates = self.customData.customDates
        self.currentDate = date.today()
        self.dateProvider.refresh()

        time.sleep(1)
        for key in self.dateProvider.dates.keys():
            if self.customDates is not None:
                customDate = self.customDates.get(str(
                    self.dateProvider.dates[key]))
            else:
                customDate = None

            self.poly.addNode(
                DayNode(self.poly, self.address, key.lower(), key + ' Day Node',
                        key, self.dateProvider, self, customDate is True,
                        customDate is False))

    def set_on(self, date):
        self.customDates[str(date)] = True
        #self.saveCustomData({'customDates': self.customDates})
        self.customData['customDates'] = self.customDates

    def set_off(self, date):
        if str(date) in self.customDates:
            self.customDates.pop(str(date))

        #self.saveCustomData({'customDates': self.customDates})
        self.customData['customDates'] = self.customDates

    def set_force_off(self, date):
        self.customDates[str(date)] = False
        #self.saveCustomData({'customDates': self.customDates})
        self.customData['customDates'] = self.customDates

    id = 'controller'
    commands = {'DISCOVER': discover}
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]


class DayNode(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name, key,
                 dateProvider, controller, is_day_off, is_force_off):
        super(DayNode, self).__init__(polyglot, primary, address, name)
        self.key = key
        self.dateProvider = dateProvider
        self.controller = controller
        self.is_day_off = False if is_day_off is None else is_day_off
        self.is_force_off = False if is_force_off is None else is_force_off

        polyglot.subscribe(polyglot.START, self.start, address)

    def start(self):
        self.refresh()

    def refresh(self):
        date = self.dateProvider.dates[self.key]
        self.setDriver('GV0', date.month)
        self.setDriver('GV1', date.day)
        self.setDriver('GV2', date.year)
        self.setDriver('ST', self.get_state())

    def set_on(self, command):
        self.is_day_off = True
        self.is_force_off = False
        self.setDriver('ST', 1)
        time.sleep(1)
        self.controller.set_on(self.dateProvider.dates[self.key])

    def set_off(self, command):
        self.is_day_off = False
        self.is_force_off = False
        self.setDriver('ST', self.get_state())
        time.sleep(1)
        self.controller.set_off(self.dateProvider.dates[self.key])

    def set_force_off(self, command):
        LOGGER.debug("Setting %s to force off", self.key)
        self.is_day_off = False
        self.is_force_off = True
        self.setDriver('ST', self.get_state())
        time.sleep(1)
        self.controller.set_force_off(self.dateProvider.dates[self.key])

    def query(self):
        self.reportDrivers()

    def get_state(self):
        return 1 if not self.is_force_off and (
            self.is_day_off or self.dateProvider.is_day_off(self.key)) else 0

    drivers = [{
        'driver': 'ST',
        'value': 0,
        'uom': 2
    }, {
        'driver': 'GV0',
        'value': 0,
        'uom': 47
    }, {
        'driver': 'GV1',
        'value': 0,
        'uom': 9
    }, {
        'driver': 'GV2',
        'value': 0,
        'uom': 77
    }]

    id = 'daynode'
    commands = {'DON': set_on, 'DOF': set_off, 'FOFF': set_force_off}


@click.command()
def holidays_server():
    polyglot = udi_interface.Interface([])
    polyglot.start('1.0.0')
    Controller(polyglot, 'controller', 'controller', 'Holiday Controller')
    polyglot.runForever()


if __name__ == '__main__':
    holidays_server()
