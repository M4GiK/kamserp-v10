# -*- coding: utf-8 -*-

import datetime
from dateutil.relativedelta import relativedelta

from odoo.addons.event.tests.common import TestEventCommon
from odoo.exceptions import ValidationError, UserError, AccessError
from odoo.tools import mute_logger


class TestEventFlow(TestEventCommon):

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_00_basic_event_auto_confirm(self):
        """ Basic event management with auto confirmation """
        event_config = self.env['event.config.settings'].sudo(self.user_eventmanager).create({
            'auto_confirmation': 1
        })
        event_config.execute()

        # EventUser creates a new event: ok
        test_event = self.Event.sudo(self.user_eventmanager).create({
            'name': 'TestEvent',
            'date_begin': datetime.datetime.now() + relativedelta(days=-1),
            'date_end': datetime.datetime.now() + relativedelta(days=1),
            'seats_max': 2,
            'seats_availability': 'limited',
        })
        self.assertEqual(test_event.state, 'confirm', 'Event: auto_confirmation of event failed')

        # EventUser create registrations for this event
        test_reg1 = self.Registration.sudo(self.user_eventuser).create({
            'name': 'TestReg1',
            'event_id': test_event.id,
        })
        self.assertEqual(test_reg1.state, 'open', 'Event: auto_confirmation of registration failed')
        self.assertEqual(test_event.seats_reserved, 1, 'Event: wrong number of reserved seats after confirmed registration')
        test_reg2 = self.Registration.sudo(self.user_eventuser).create({
            'name': 'TestReg2',
            'event_id': test_event.id,
        })
        self.assertEqual(test_reg2.state, 'open', 'Event: auto_confirmation of registration failed')
        self.assertEqual(test_event.seats_reserved, 2, 'Event: wrong number of reserved seats after confirmed registration')

        # EventUser create registrations for this event: too much registrations
        with self.assertRaises(ValidationError):
            self.Registration.sudo(self.user_eventuser).create({
                'name': 'TestReg3',
                'event_id': test_event.id,
            })

        # EventUser validates registrations
        test_reg1.button_reg_close()
        self.assertEqual(test_reg1.state, 'done', 'Event: wrong state of attended registration')
        self.assertEqual(test_event.seats_used, 1, 'Event: incorrect number of attendees after closing registration')
        test_reg2.button_reg_close()
        self.assertEqual(test_reg1.state, 'done', 'Event: wrong state of attended registration')
        self.assertEqual(test_event.seats_used, 2, 'Event: incorrect number of attendees after closing registration')

        # EventUser closes the event
        test_event.button_done()

        # EventUser cancels -> not possible when having attendees
        with self.assertRaises(UserError):
            test_event.button_cancel()


    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_10_advanced_event_flow(self):
        """ Avanced event flow: no auto confirmation, manage minimum / maximum
        seats, ... """
        self.env['ir.values'].set_default('event.config.settings', 'auto_confirmation', False)

        # EventUser creates a new event: ok
        test_event = self.Event.sudo(self.user_eventmanager).create({
            'name': 'TestEvent',
            'date_begin': datetime.datetime.now() + relativedelta(days=-1),
            'date_end': datetime.datetime.now() + relativedelta(days=1),
            'seats_max': 10,
        })
        self.assertEqual(
            test_event.state, 'draft',
            'Event: new event should be in draft state, no auto confirmation')

        # EventUser create registrations for this event -> no auto confirmation
        test_reg1 = self.Registration.sudo(self.user_eventuser).create({
            'name': 'TestReg1',
            'event_id': test_event.id,
        })
        self.assertEqual(
            test_reg1.state, 'draft',
            'Event: new registration should not be confirmed with auto_confirmation parameter being False')

    def test_event_access_rights(self):
        # EventManager required to create or update events
        with self.assertRaises(AccessError):
            self.Event.sudo(self.user_eventuser).create({
                'name': 'TestEvent',
                'date_begin': datetime.datetime.now() + relativedelta(days=-1),
                'date_end': datetime.datetime.now() + relativedelta(days=1),
                'seats_max': 10,
            })
        with self.assertRaises(AccessError):
            self.event_0.sudo(self.user_eventuser).write({
                'name': 'TestEvent Modified',
            })

        # Settings access rights required to enable some features
        self.user_eventmanager.write({'groups_id': [
            (3, self.env.ref('base.group_system').id),
            (4, self.env.ref('base.group_erp_manager').id)
        ]})
        with self.assertRaises(AccessError):
            event_config = self.env['event.config.settings'].sudo(self.user_eventmanager).create({
                'auto_confirmation': 1
            })
            event_config.execute()

    def test_event_data(self):
        self.assertEqual(self.event_0.registration_ids.get_date_range_str(), u'Tomorrow')
