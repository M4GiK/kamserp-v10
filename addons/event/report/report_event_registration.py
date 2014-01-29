# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp import tools

class report_event_registration(osv.osv):
    _name = "report.event.registration"
    _description = "Events Analysis"
    _auto = False
    _columns = {
        'event_date': fields.datetime('Event Date', readonly=True),
        'event_id': fields.many2one('event.event', 'Event', required=True),
        'draft_state': fields.integer(' # No of Draft Registrations', size=20),
        'confirm_state': fields.integer(' # No of Confirmed Registrations', size=20),
        'seats_max': fields.integer('Max Seats'),
        'nbevent': fields.integer('Number Of Events'),
        'event_type': fields.many2one('event.type', 'Event Type'),
        'registration_state': fields.selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('done', 'Attended'), ('cancel', 'Cancelled')], 'Registration State', readonly=True, required=True),
        'event_state': fields.selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Event State', readonly=True, required=True),
        'user_id': fields.many2one('res.users', 'Event Responsible', readonly=True),
        'user_id_registration': fields.many2one('res.users', 'Register', readonly=True),
        'name_registration': fields.char('Participant / Contact Name',size=45, readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
    }
    _order = 'event_date desc'

    def init(self, cr):
        """
        Initialize the sql view for the event registration
        """
        tools.drop_view_if_exists(cr, 'report_event_registration')

        # TOFIX this request won't select events that have no registration
        cr.execute(""" CREATE VIEW report_event_registration AS (
            SELECT
                e.id::char || '/' || coalesce(r.id::char,'') AS id,
                e.id AS event_id,
                e.user_id AS user_id,
                r.user_id AS user_id_registration,
                r.name AS name_registration,
                e.company_id AS company_id,
                e.date_begin AS event_date,
                count(e.id) AS nbevent,
                CASE WHEN r.state IN ('draft') THEN r.nb_register ELSE 0 END AS draft_state,
                CASE WHEN r.state IN ('open','done') THEN r.nb_register ELSE 0 END AS confirm_state,
                e.type AS event_type,
                e.seats_max AS seats_max,
                e.state AS event_state,
                r.state AS registration_state
            FROM
                event_event e
                LEFT JOIN event_registration r ON (e.id=r.event_id)

            GROUP BY
                event_id,
                user_id_registration,
                r.id,
                registration_state,
                r.nb_register,
                event_type,
                e.id,
                e.date_begin,
                e.user_id,
                event_state,
                e.company_id,
                e.seats_max,
                name_registration
        )
        """)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
