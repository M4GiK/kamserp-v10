# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta, date

import babel.dates
from dateutil.relativedelta import relativedelta

from openerp.addons.resource.tests.common import TestResourceCommon

from openerp.tests import TransactionCase


class TestResource(TestResourceCommon):

    def test_00_intervals(self):
        cr, uid = self.cr, self.uid
        intervals = [
            (
                datetime.strptime('2013-02-04 09:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.strptime('2013-02-04 11:00:00', '%Y-%m-%d %H:%M:%S')
            ), (
                datetime.strptime('2013-02-04 08:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.strptime('2013-02-04 12:00:00', '%Y-%m-%d %H:%M:%S')
            ), (
                datetime.strptime('2013-02-04 11:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.strptime('2013-02-04 14:00:00', '%Y-%m-%d %H:%M:%S')
            ), (
                datetime.strptime('2013-02-04 17:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.strptime('2013-02-04 21:00:00', '%Y-%m-%d %H:%M:%S')
            ), (
                datetime.strptime('2013-02-03 08:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.strptime('2013-02-03 10:00:00', '%Y-%m-%d %H:%M:%S')
            ), (
                datetime.strptime('2013-02-04 18:00:00', '%Y-%m-%d %H:%M:%S'),
                datetime.strptime('2013-02-04 19:00:00', '%Y-%m-%d %H:%M:%S')
            )
        ]

        # Test: interval cleaning
        cleaned_intervals = self.resource_calendar.interval_clean(intervals)
        self.assertEqual(len(cleaned_intervals), 3, 'resource_calendar: wrong interval cleaning')
        # First interval: 03, unchanged
        self.assertEqual(cleaned_intervals[0][0], datetime.strptime('2013-02-03 08:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong interval cleaning')
        self.assertEqual(cleaned_intervals[0][1], datetime.strptime('2013-02-03 10:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong interval cleaning')
        # Second intreval: 04, 08-14, combining 08-12 and 11-14, 09-11 being inside 08-12
        self.assertEqual(cleaned_intervals[1][0], datetime.strptime('2013-02-04 08:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong interval cleaning')
        self.assertEqual(cleaned_intervals[1][1], datetime.strptime('2013-02-04 14:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong interval cleaning')
        # Third interval: 04, 17-21, 18-19 being inside 17-21
        self.assertEqual(cleaned_intervals[2][0], datetime.strptime('2013-02-04 17:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong interval cleaning')
        self.assertEqual(cleaned_intervals[2][1], datetime.strptime('2013-02-04 21:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong interval cleaning')

        # Test: disjoint removal
        working_interval = (datetime.strptime('2013-02-04 08:00:00', '%Y-%m-%d %H:%M:%S'), datetime.strptime('2013-02-04 18:00:00', '%Y-%m-%d %H:%M:%S'))
        result = self.resource_calendar.interval_remove_leaves(cr, uid, working_interval, intervals)
        self.assertEqual(len(result), 1, 'resource_calendar: wrong leave removal from interval')
        # First interval: 04, 14-17
        self.assertEqual(result[0][0], datetime.strptime('2013-02-04 14:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')
        self.assertEqual(result[0][1], datetime.strptime('2013-02-04 17:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')

        # Test: schedule hours on intervals
        result = self.resource_calendar.interval_schedule_hours(cleaned_intervals, 5.5)
        self.assertEqual(len(result), 2, 'resource_calendar: wrong hours scheduling in interval')
        # First interval: 03, 8-10 untouches
        self.assertEqual(result[0][0], datetime.strptime('2013-02-03 08:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')
        self.assertEqual(result[0][1], datetime.strptime('2013-02-03 10:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')
        # First interval: 04, 08-11:30
        self.assertEqual(result[1][0], datetime.strptime('2013-02-04 08:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')
        self.assertEqual(result[1][1], datetime.strptime('2013-02-04 11:30:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')

        # Test: schedule hours on intervals, backwards
        cleaned_intervals.reverse()
        result = self.resource_calendar.interval_schedule_hours(cleaned_intervals, 5.5, remove_at_end=False)
        self.assertEqual(len(result), 2, 'resource_calendar: wrong hours scheduling in interval')
        # First interval: 03, 8-10 untouches
        self.assertEqual(result[0][0], datetime.strptime('2013-02-04 17:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')
        self.assertEqual(result[0][1], datetime.strptime('2013-02-04 21:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')
        # First interval: 04, 08-11:30
        self.assertEqual(result[1][0], datetime.strptime('2013-02-04 12:30:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')
        self.assertEqual(result[1][1], datetime.strptime('2013-02-04 14:00:00', '%Y-%m-%d %H:%M:%S'), 'resource_calendar: wrong leave removal from interval')

    def test_10_calendar_basics(self):
        """ Testing basic method of resource.calendar """
        cr, uid = self.cr, self.uid

        # --------------------------------------------------
        # Test1: get_next_day
        # --------------------------------------------------

        # Test: next day: next day after day1 is day4
        date = self.resource_calendar.get_next_day(cr, uid, self.calendar_id, day_date=self.date1.date())
        self.assertEqual(date, self.date2.date(), 'resource_calendar: wrong next day computing')

        # Test: next day: next day after day4 is (day1+7)
        date = self.resource_calendar.get_next_day(cr, uid, self.calendar_id, day_date=self.date2.date())
        self.assertEqual(date, self.date1.date() + relativedelta(days=7), 'resource_calendar: wrong next day computing')

        # Test: next day: next day after day4+1 is (day1+7)
        date = self.resource_calendar.get_next_day(cr, uid, self.calendar_id, day_date=self.date2.date() + relativedelta(days=1))
        self.assertEqual(date, self.date1.date() + relativedelta(days=7), 'resource_calendar: wrong next day computing')

        # Test: next day: next day after day1-1 is day1
        date = self.resource_calendar.get_next_day(cr, uid, self.calendar_id, day_date=self.date1.date() + relativedelta(days=-1))
        self.assertEqual(date, self.date1.date(), 'resource_calendar: wrong next day computing')

        # --------------------------------------------------
        # Test2: get_previous_day
        # --------------------------------------------------

        # Test: previous day: previous day before day1 is (day4-7)
        date = self.resource_calendar.get_previous_day(cr, uid, self.calendar_id, day_date=self.date1.date())
        self.assertEqual(date, self.date2.date() + relativedelta(days=-7), 'resource_calendar: wrong previous day computing')

        # Test: previous day: previous day before day4 is day1
        date = self.resource_calendar.get_previous_day(cr, uid, self.calendar_id, day_date=self.date2.date())
        self.assertEqual(date, self.date1.date(), 'resource_calendar: wrong previous day computing')

        # Test: previous day: previous day before day4+1 is day4
        date = self.resource_calendar.get_previous_day(cr, uid, self.calendar_id, day_date=self.date2.date() + relativedelta(days=1))
        self.assertEqual(date, self.date2.date(), 'resource_calendar: wrong previous day computing')

        # Test: previous day: previous day before day1-1 is (day4-7)
        date = self.resource_calendar.get_previous_day(cr, uid, self.calendar_id, day_date=self.date1.date() + relativedelta(days=-1))
        self.assertEqual(date, self.date2.date() + relativedelta(days=-7), 'resource_calendar: wrong previous day computing')

        # --------------------------------------------------
        # Test3: misc
        # --------------------------------------------------

        weekdays = self.resource_calendar.get_weekdays(cr, uid, self.calendar_id)
        self.assertEqual(weekdays, [1, 4], 'resource_calendar: wrong weekdays computing')

#        attendances = self.resource_calendar.get_attendances_for_weekdays(cr, uid, self.calendar_id, [2, 3, 4, 5])
#        self.assertEqual(set([att.id for att in attendances]), set([self.att2_id, self.att3_id]),
#                         'resource_calendar: wrong attendances filtering by weekdays computing')

    def test_20_calendar_working_intervals(self):
        """ Testing working intervals computing method of resource.calendar """
        cr, uid = self.cr, self.uid
        context = self.context
        _format = '%Y-%m-%d %H:%M:%S'

        # Test: day0 without leaves: 1 interval
        intervals = self.resource_calendar.get_working_intervals_of_day(cr, uid, self.calendar_id, start_dt=self.date1, context=context)
        self.assertEqual(len(intervals), 1, 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[0][0], datetime.strptime('2013-02-12 09:08:07', _format), 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[0][1], datetime.strptime('2013-02-12 16:00:00', _format), 'resource_calendar: wrong working intervals')

        # Test: day3 without leaves: 2 interval
        intervals = self.resource_calendar.get_working_intervals_of_day(cr, uid, self.calendar_id, start_dt=self.date2, context=context)
        self.assertEqual(len(intervals), 2, 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[0][0], datetime.strptime('2013-02-15 10:11:12', _format), 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[0][1], datetime.strptime('2013-02-15 13:00:00', _format), 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[1][0], datetime.strptime('2013-02-15 16:00:00', _format), 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[1][1], datetime.strptime('2013-02-15 23:00:00', _format), 'resource_calendar: wrong working intervals')

        # Test: day0 with leaves outside range: 1 interval
        intervals = self.resource_calendar.get_working_intervals_of_day(cr, uid, self.calendar_id, start_dt=self.date1.replace(hour=0), compute_leaves=True, context=context)
        self.assertEqual(len(intervals), 1, 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[0][0], datetime.strptime('2013-02-12 08:00:00', _format), 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[0][1], datetime.strptime('2013-02-12 16:00:00', _format), 'resource_calendar: wrong working intervals')

        # Test: day0 with leaves: 2 intervals because of leave between 9 ans 12, ending at 15:45:30
        intervals = self.resource_calendar.get_working_intervals_of_day(cr, uid, self.calendar_id,
                                                                        start_dt=self.date1.replace(hour=8) + relativedelta(days=7),
                                                                        end_dt=self.date1.replace(hour=15, minute=45, second=30) + relativedelta(days=7),
                                                                        compute_leaves=True, context=context)
        self.assertEqual(len(intervals), 2, 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[0][0], datetime.strptime('2013-02-19 08:08:07', _format), 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[0][1], datetime.strptime('2013-02-19 09:00:00', _format), 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[1][0], datetime.strptime('2013-02-19 12:00:00', _format), 'resource_calendar: wrong working intervals')
        self.assertEqual(intervals[1][1], datetime.strptime('2013-02-19 15:45:30', _format), 'resource_calendar: wrong working intervals')

    def test_30_calendar_working_days(self):
        """ Testing calendar hours computation on a working day """
        cr, uid = self.cr, self.uid
        context = self.context
        _format = '%Y-%m-%d %H:%M:%S'

        # Test: day1, beginning at 10:30 -> work from 10:30 (arrival) until 16:00
        intervals = self.resource_calendar.get_working_intervals_of_day(cr, uid, self.calendar_id, start_dt=self.date1.replace(hour=10, minute=30, second=0), context=context)
        self.assertEqual(len(intervals), 1, 'resource_calendar: wrong working interval / day computing')
        self.assertEqual(intervals[0][0], datetime.strptime('2013-02-12 10:30:00', _format), 'resource_calendar: wrong working interval / day computing')
        self.assertEqual(intervals[0][1], datetime.strptime('2013-02-12 16:00:00', _format), 'resource_calendar: wrong working interval / day computing')
        # Test: hour computation for same interval, should give 5.5
        wh = self.resource_calendar.get_working_hours_of_date(cr, uid, self.calendar_id, start_dt=self.date1.replace(hour=10, minute=30, second=0), context=context)
        self.assertEqual(wh, 5.5, 'resource_calendar: wrong working interval / day time computing')

        # Test: day1+7 on leave, without leave computation
        intervals = self.resource_calendar.get_working_intervals_of_day(
            cr, uid, self.calendar_id,
            start_dt=self.date1.replace(hour=7, minute=0, second=0) + relativedelta(days=7), context=context
        )
        # Result: day1 (08->16)
        self.assertEqual(len(intervals), 1, 'resource_calendar: wrong working interval/day computing')
        self.assertEqual(intervals[0][0], datetime.strptime('2013-02-19 08:00:00', _format), 'resource_calendar: wrong working interval / day computing')
        self.assertEqual(intervals[0][1], datetime.strptime('2013-02-19 16:00:00', _format), 'resource_calendar: wrong working interval / day computing')

        # Test: day1+7 on leave, with generic leave computation
        intervals = self.resource_calendar.get_working_intervals_of_day(
            cr, uid, self.calendar_id,
            start_dt=self.date1.replace(hour=7, minute=0, second=0) + relativedelta(days=7),
            compute_leaves=True, context=context
        )
        # Result: day1 (08->09 + 12->16)
        self.assertEqual(len(intervals), 2, 'resource_calendar: wrong working interval/day computing')
        self.assertEqual(intervals[0][0], datetime.strptime('2013-02-19 08:00:00', _format), 'resource_calendar: wrong working interval / day computing')
        self.assertEqual(intervals[0][1], datetime.strptime('2013-02-19 09:00:00', _format), 'resource_calendar: wrong working interval / day computing')
        self.assertEqual(intervals[1][0], datetime.strptime('2013-02-19 12:00:00', _format), 'resource_calendar: wrong working interval / day computing')
        self.assertEqual(intervals[1][1], datetime.strptime('2013-02-19 16:00:00', _format), 'resource_calendar: wrong working interval / day computing')

        # Test: day1+14 on leave, with generic leave computation
        intervals = self.resource_calendar.get_working_intervals_of_day(
            cr, uid, self.calendar_id,
            start_dt=self.date1.replace(hour=7, minute=0, second=0) + relativedelta(days=14),
            compute_leaves=True, context=context
        )
        # Result: day1 (08->16)
        self.assertEqual(len(intervals), 1, 'resource_calendar: wrong working interval/day computing')
        self.assertEqual(intervals[0][0], datetime.strptime('2013-02-26 08:00:00', _format), 'resource_calendar: wrong working interval / day computing')
        self.assertEqual(intervals[0][1], datetime.strptime('2013-02-26 16:00:00', _format), 'resource_calendar: wrong working interval / day computing')

        # Test: day1+14 on leave, with resource leave computation
        intervals = self.resource_calendar.get_working_intervals_of_day(
            cr, uid, self.calendar_id,
            start_dt=self.date1.replace(hour=7, minute=0, second=0) + relativedelta(days=14),
            compute_leaves=True,
            resource_id=self.resource1_id, context=context
        )
        # Result: nothing, because on leave
        self.assertEqual(len(intervals), 0, 'resource_calendar: wrong working interval/day computing')

    def test_40_calendar_hours_scheduling(self):
        """ Testing calendar hours scheduling """
        cr, uid = self.cr, self.uid
        context = self.context
        _format = '%Y-%m-%d %H:%M:%S'

        # --------------------------------------------------
        # Test0: schedule hours backwards (old interval_min_get)
        #   Done without calendar
        # --------------------------------------------------

        # Done without calendar
        # res = self.resource_calendar.interval_min_get(cr, uid, None, self.date1, 40, resource=False)
        # res: (datetime.datetime(2013, 2, 7, 9, 8, 7), datetime.datetime(2013, 2, 12, 9, 8, 7))

        # --------------------------------------------------
        # Test1: schedule hours backwards (old interval_min_get)
        # --------------------------------------------------

        # res = self.resource_calendar.interval_min_get(cr, uid, self.calendar_id, self.date1, 40, resource=False)
        #   (datetime.datetime(2013, 1, 29, 9, 0), datetime.datetime(2013, 1, 29, 16, 0))
        #   (datetime.datetime(2013, 2, 1, 8, 0), datetime.datetime(2013, 2, 1, 13, 0))
        #   (datetime.datetime(2013, 2, 1, 16, 0), datetime.datetime(2013, 2, 1, 23, 0))
        #   (datetime.datetime(2013, 2, 5, 8, 0), datetime.datetime(2013, 2, 5, 16, 0))
        #   (datetime.datetime(2013, 2, 8, 8, 0), datetime.datetime(2013, 2, 8, 13, 0))
        #   (datetime.datetime(2013, 2, 8, 16, 0), datetime.datetime(2013, 2, 8, 23, 0))
        #   (datetime.datetime(2013, 2, 12, 8, 0), datetime.datetime(2013, 2, 12, 9, 0))

        res = self.resource_calendar.schedule_hours(cr, uid, self.calendar_id, -40, day_dt=self.date1.replace(minute=0, second=0), context=context)
        # current day, limited at 09:00 because of day_dt specified -> 1 hour
        self.assertEqual(res[-1][0], datetime.strptime('2013-02-12 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-1][1], datetime.strptime('2013-02-12 09:00:00', _format), 'resource_calendar: wrong hours scheduling')
        # previous days: 5+7 hours / 8 hours / 5+7 hours -> 32 hours
        self.assertEqual(res[-2][0], datetime.strptime('2013-02-08 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-2][1], datetime.strptime('2013-02-08 23:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-3][0], datetime.strptime('2013-02-08 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-3][1], datetime.strptime('2013-02-08 13:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-4][0], datetime.strptime('2013-02-05 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-4][1], datetime.strptime('2013-02-05 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-5][0], datetime.strptime('2013-02-01 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-5][1], datetime.strptime('2013-02-01 23:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-6][0], datetime.strptime('2013-02-01 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-6][1], datetime.strptime('2013-02-01 13:00:00', _format), 'resource_calendar: wrong hours scheduling')
        # 7 hours remaining
        self.assertEqual(res[-7][0], datetime.strptime('2013-01-29 09:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[-7][1], datetime.strptime('2013-01-29 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        # Compute scheduled hours
        td = timedelta()
        for item in res:
            td += item[1] - item[0]
        self.assertEqual(seconds(td) / 3600.0, 40.0, 'resource_calendar: wrong hours scheduling')

        # --------------------------------------------------
        # Test2: schedule hours forward (old interval_get)
        # --------------------------------------------------

        # res = self.resource_calendar.interval_get(cr, uid, self.calendar_id, self.date1, 40, resource=False, byday=True)
        #   (datetime.datetime(2013, 2, 12, 9, 0), datetime.datetime(2013, 2, 12, 16, 0))
        #   (datetime.datetime(2013, 2, 15, 8, 0), datetime.datetime(2013, 2, 15, 13, 0))
        #   (datetime.datetime(2013, 2, 15, 16, 0), datetime.datetime(2013, 2, 15, 23, 0))
        #   (datetime.datetime(2013, 2, 22, 8, 0), datetime.datetime(2013, 2, 22, 13, 0))
        #   (datetime.datetime(2013, 2, 22, 16, 0), datetime.datetime(2013, 2, 22, 23, 0))
        #   (datetime.datetime(2013, 2, 26, 8, 0), datetime.datetime(2013, 2, 26, 16, 0))
        #   (datetime.datetime(2013, 3, 1, 8, 0), datetime.datetime(2013, 3, 1, 9, 0))

        res = self.resource_calendar.schedule_hours(
            cr, uid, self.calendar_id, 40,
            day_dt=self.date1.replace(minute=0, second=0), context=context
        )
        self.assertEqual(res[0][0], datetime.strptime('2013-02-12 09:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[0][1], datetime.strptime('2013-02-12 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[1][0], datetime.strptime('2013-02-15 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[1][1], datetime.strptime('2013-02-15 13:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[2][0], datetime.strptime('2013-02-15 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[2][1], datetime.strptime('2013-02-15 23:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[3][0], datetime.strptime('2013-02-19 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[3][1], datetime.strptime('2013-02-19 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[4][0], datetime.strptime('2013-02-22 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[4][1], datetime.strptime('2013-02-22 13:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[5][0], datetime.strptime('2013-02-22 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[5][1], datetime.strptime('2013-02-22 23:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[6][0], datetime.strptime('2013-02-26 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[6][1], datetime.strptime('2013-02-26 09:00:00', _format), 'resource_calendar: wrong hours scheduling')
        td = timedelta()
        for item in res:
            td += item[1] - item[0]
        self.assertEqual(seconds(td) / 3600.0, 40.0, 'resource_calendar: wrong hours scheduling')

        # res = self.resource_calendar.interval_get(cr, uid, self.calendar_id, self.date1, 40, resource=self.resource1_id, byday=True)
        #   (datetime.datetime(2013, 2, 12, 9, 0), datetime.datetime(2013, 2, 12, 16, 0))
        #   (datetime.datetime(2013, 2, 15, 8, 0), datetime.datetime(2013, 2, 15, 13, 0))
        #   (datetime.datetime(2013, 2, 15, 16, 0), datetime.datetime(2013, 2, 15, 23, 0))
        #   (datetime.datetime(2013, 3, 1, 8, 0), datetime.datetime(2013, 3, 1, 13, 0))
        #   (datetime.datetime(2013, 3, 1, 16, 0), datetime.datetime(2013, 3, 1, 23, 0))
        #   (datetime.datetime(2013, 3, 5, 8, 0), datetime.datetime(2013, 3, 5, 16, 0))
        #   (datetime.datetime(2013, 3, 8, 8, 0), datetime.datetime(2013, 3, 8, 9, 0))

        res = self.resource_calendar.schedule_hours(
            cr, uid, self.calendar_id, 40,
            day_dt=self.date1.replace(minute=0, second=0),
            compute_leaves=True,
            resource_id=self.resource1_id, context=context
        )
        self.assertEqual(res[0][0], datetime.strptime('2013-02-12 09:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[0][1], datetime.strptime('2013-02-12 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[1][0], datetime.strptime('2013-02-15 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[1][1], datetime.strptime('2013-02-15 13:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[2][0], datetime.strptime('2013-02-15 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[2][1], datetime.strptime('2013-02-15 23:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[3][0], datetime.strptime('2013-02-19 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[3][1], datetime.strptime('2013-02-19 09:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[4][0], datetime.strptime('2013-02-19 12:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[4][1], datetime.strptime('2013-02-19 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[5][0], datetime.strptime('2013-02-22 08:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[5][1], datetime.strptime('2013-02-22 09:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[6][0], datetime.strptime('2013-02-22 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[6][1], datetime.strptime('2013-02-22 23:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[7][0], datetime.strptime('2013-03-01 11:30:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[7][1], datetime.strptime('2013-03-01 13:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[8][0], datetime.strptime('2013-03-01 16:00:00', _format), 'resource_calendar: wrong hours scheduling')
        self.assertEqual(res[8][1], datetime.strptime('2013-03-01 22:30:00', _format), 'resource_calendar: wrong hours scheduling')
        td = timedelta()
        for item in res:
            td += item[1] - item[0]
        self.assertEqual(seconds(td) / 3600.0, 40.0, 'resource_calendar: wrong hours scheduling')

        # --------------------------------------------------
        # Test3: working hours (old _interval_hours_get)
        # --------------------------------------------------

        # old API: resource without leaves
        # res: 2 weeks -> 40 hours
        res = self.resource_calendar._interval_hours_get(
            cr, uid, self.calendar_id,
            self.date1.replace(hour=6, minute=0),
            self.date2.replace(hour=23, minute=0) + relativedelta(days=7),
            resource_id=self.resource1_id, exclude_leaves=True, context=context)
        self.assertEqual(res, 40.0, 'resource_calendar: wrong _interval_hours_get compatibility computation')

        # new API: resource without leaves
        # res: 2 weeks -> 40 hours
        res = self.resource_calendar.get_working_hours(
            cr, uid, self.calendar_id,
            self.date1.replace(hour=6, minute=0),
            self.date2.replace(hour=23, minute=0) + relativedelta(days=7),
            compute_leaves=False, resource_id=self.resource1_id, context=context)
        self.assertEqual(res, 40.0, 'resource_calendar: wrong get_working_hours computation')

        # old API: resource and leaves
        # res: 2 weeks -> 40 hours - (3+4) leave hours
        res = self.resource_calendar._interval_hours_get(
            cr, uid, self.calendar_id,
            self.date1.replace(hour=6, minute=0),
            self.date2.replace(hour=23, minute=0) + relativedelta(days=7),
            resource_id=self.resource1_id, exclude_leaves=False, context=context)
        self.assertEqual(res, 33.0, 'resource_calendar: wrong _interval_hours_get compatibility computation')

        # new API: resource and leaves
        # res: 2 weeks -> 40 hours - (3+4) leave hours
        res = self.resource_calendar.get_working_hours(
            cr, uid, self.calendar_id,
            self.date1.replace(hour=6, minute=0),
            self.date2.replace(hour=23, minute=0) + relativedelta(days=7),
            compute_leaves=True, resource_id=self.resource1_id, context=context)
        self.assertEqual(res, 33.0, 'resource_calendar: wrong get_working_hours computation')

        # --------------------------------------------------
        # Test4: misc
        # --------------------------------------------------

        # Test without calendar and default_interval
        res = self.resource_calendar.get_working_hours(
            cr, uid, None,
            self.date1.replace(hour=6, minute=0),
            self.date2.replace(hour=23, minute=0),
            compute_leaves=True, resource_id=self.resource1_id,
            default_interval=(8, 16), context=context)
        self.assertEqual(res, 32.0, 'resource_calendar: wrong get_working_hours computation')

        self.att0_0_id = self.resource_attendance.create(
            cr, uid, {
                'name': 'Att0',
                'dayofweek': '0',
                'hour_from': 7.5,
                'hour_to': 12.5,
                'calendar_id': self.calendar_id,
            }, context=context
        )
        self.att0_1_id = self.resource_attendance.create(
            cr, uid, {
                'name': 'Att0',
                'dayofweek': '0',
                'hour_from': 13,
                'hour_to': 14,
                'calendar_id': self.calendar_id,
            }, context=context
        )
        date1 = datetime.strptime('2013-02-11 07:30:00', '%Y-%m-%d %H:%M:%S')
        date2 = datetime.strptime('2013-02-11 14:00:00', '%Y-%m-%d %H:%M:%S')
        res = self.resource_calendar.get_working_hours(
            cr, uid, self.calendar_id,
            date1,
            date2,
            compute_leaves=False, resource_id=self.resource1_id, context=context)
        # 7h30 -> 12h30 = 5 / 13h -> 14h = 1 / -> 6h
        self.assertEqual(res, 6, 'resource_calendar: wrong get_working_hours computation')


    def test_50_calendar_schedule_days(self):
        """ Testing calendar days scheduling """
        cr, uid = self.cr, self.uid
        _format = '%Y-%m-%d %H:%M:%S'

        # --------------------------------------------------
        # Test1: with calendar
        # --------------------------------------------------

        res = self.resource_calendar.schedule_days_get_date(cr, uid, self.calendar_id, 5, day_date=self.date1, context={'tz': 'UTC'})
        self.assertEqual(res.date(), datetime.strptime('2013-02-26 00:0:00', _format).date(), 'resource_calendar: wrong days scheduling')
        res = self.resource_calendar.schedule_days_get_date(cr, uid, self.calendar_id, -2, day_date=self.date1, context={'tz': 'UTC'})
        self.assertEqual(res.date(), datetime.strptime('2013-02-08 00:00:00', _format).date(), 'resource_calendar: wrong days scheduling')

        res = self.resource_calendar.schedule_days_get_date(
            cr, uid, self.calendar_id, 5, day_date=self.date1,
            compute_leaves=True, resource_id=self.resource1_id, context={'tz': 'UTC'})
        self.assertEqual(res.date(), datetime.strptime('2013-03-01 00:0:00', _format).date(), 'resource_calendar: wrong days scheduling')

        # --------------------------------------------------
        # Test2: misc
        # --------------------------------------------------

        # Without calendar, should only count days -> 12 -> 16, 5 days with default intervals
        res = self.resource_calendar.schedule_days_get_date(cr, uid, None, 5, day_date=self.date1, default_interval=(8, 16), context={'tz': 'UTC'})
        self.assertEqual(res, datetime.strptime('2013-02-16 16:00:00', _format), 'resource_calendar: wrong days scheduling')

WAR_START = date(1932, 11, 2)
WAR_END = date(1932, 12, 10)
class TestWorkDays(TransactionCase):
    def _make_attendance(self, weekday, **kw):
        data = {
            'name': babel.dates.get_day_names()[weekday],
            'dayofweek': str(weekday),
            'hour_from': 9,
            'hour_to': 17,
        }
        data.update(kw)
        return data
    def setUp(self):
        super(TestWorkDays, self).setUp()
        # trivial 5/7 9-17 resource calendar
        self._calendar = self.env['resource.calendar'].create({
            'name': "Trivial Calendar",
            'attendance_ids': [
                (0, 0, self._make_attendance(i))
                for i in range(5)
            ]
        })

        self._days = [
            date.fromordinal(o)
            for o in xrange(
                WAR_START.toordinal(),
                WAR_END.toordinal() + 1
            )
        ]

    def test_no_calendar(self):
        """
        If a resource has no resource calendar, they don't work
        """
        r = self.env['resource.resource'].create({
            'name': "NoCalendar"
        })

        self.assertEqual(
            [],
            list(r._iter_work_days(WAR_START, WAR_END)),
        )

    def test_trivial_calendar_no_leaves(self):
        """ If leaves are not involved, only calendar attendances (basic
        company configuration) are taken in account
        """
        r = self.env['resource.resource'].create({
            'name': "Trivial Calendar",
            'calendar_id': self._calendar.id
        })

        # with the trivial calendar, all days are work days except for
        # saturday and sunday
        self.assertEqual(
            [d for d in self._days if d.weekday() not in (5, 6)],
            list(r._iter_work_days(WAR_START, WAR_END))
        )

    def test_global_leaves(self):
        self.env['resource.calendar.leaves'].create({
            'calendar_id': self._calendar.id,
            'date_from': '1932-11-09 00:00:00',
            'date_to': '1932-11-12 23:59:59',
        })

        r1 = self.env['resource.resource'].create({
            'name': "Resource 1",
            'calendar_id': self._calendar.id
        })
        r2 = self.env['resource.resource'].create({
            'name': "Resource 2",
            'calendar_id': self._calendar.id
        })

        days = [
            d for d in self._days
            if d.weekday() not in (5, 6)
            if d < date(1932, 11, 9) or d > date(1932, 11, 12)
        ]
        self.assertEqual(days, list(r1._iter_work_days(WAR_START, WAR_END)))
        self.assertEqual(days, list(r2._iter_work_days(WAR_START, WAR_END)))

    def test_personal_leaves(self):
        """ Leaves with a resource_id apply only to that resource
        """
        r1 = self.env['resource.resource'].create({
            'name': "Resource 1",
            'calendar_id': self._calendar.id
        })
        r2 = self.env['resource.resource'].create({
            'name': "Resource 2",
            'calendar_id': self._calendar.id
        })
        self.env['resource.calendar.leaves'].create({
            'calendar_id': self._calendar.id,
            'date_from': '1932-11-09 00:00:00',
            'date_to': '1932-11-12 23:59:59',
            'resource_id': r2.id
        })

        weekdays = [d for d in self._days if d.weekday() not in (5, 6)]
        self.assertEqual(weekdays, list(r1._iter_work_days(WAR_START, WAR_END)))
        self.assertEqual(
            [d for d in weekdays
             if d < date(1932, 11, 9) or d > date(1932, 11, 12)
            ],
            list(r2._iter_work_days(WAR_START, WAR_END))
        )

    def test_mixed_leaves(self):
        r = self.env['resource.resource'].create({
            'name': "Resource 1",
            'calendar_id': self._calendar.id
        })
        self.env['resource.calendar.leaves'].create({
            'calendar_id': self._calendar.id,
            'date_from': '1932-11-09 00:00:00',
            'date_to': '1932-11-12 23:59:59',
        })
        self.env['resource.calendar.leaves'].create({
            'calendar_id': self._calendar.id,
            'date_from': '1932-12-02 00:00:00',
            'date_to': '1932-12-31 23:59:59',
            'resource_id': r.id
        })

        self.assertEqual(
            [d for d in self._days
             if d.weekday() not in (5, 6)
             if d < date(1932, 11, 9) or d > date(1932, 11, 12)
             if d < date(1932, 12, 2)
            ],
            list(r._iter_work_days(WAR_START, WAR_END))
        )

        # _is_work_day is built on _iter_work_days, but it's probably a good
        # idea to ensure it does do what it should
        self.assertTrue(r._is_work_day(date(1932, 11, 8)))
        self.assertTrue(r._is_work_day(date(1932, 11, 14)))
        self.assertTrue(r._is_work_day(date(1932, 12, 1)))

        self.assertFalse(r._is_work_day(date(1932, 11, 11))) # global leave
        self.assertFalse(r._is_work_day(date(1932, 11, 13))) # sun
        self.assertFalse(r._is_work_day(date(1932, 11, 19))) # sat
        self.assertFalse(r._is_work_day(date(1932, 11, 20))) # sun
        self.assertFalse(r._is_work_day(date(1932, 12, 6))) # personal leave

def seconds(td):
    assert isinstance(td, timedelta)

    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10.**6
