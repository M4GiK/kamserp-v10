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

from osv import fields,osv
import tools

class crm_phonecall_report(osv.osv):
    """ Phone calls by user and section """

    _name = "crm.phonecall.report"
    _description = "Phone calls by user and section"
    _auto = False
    _inherit = "crm.case.report"

    _columns = {
        'delay_close': fields.char('Delay to close', size=20, readonly=True),
        'categ_id': fields.many2one('crm.case.categ', 'Category', \
                        domain="[('section_id','=',section_id),\
                        ('object_id.model', '=', 'crm.phonecall')]"),
        'partner_id': fields.many2one('res.partner', 'Partner' , readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
    }

    def init(self, cr):

        """ @param cr: the current row, from the database cursor,
            Phone Calls By User And Section """

        tools.drop_view_if_exists(cr, 'crm_phonecall_report')
        cr.execute("""
            create or replace view crm_phonecall_report as (
                select
                    min(c.id) as id,
                    to_char(c.create_date, 'YYYY') as name,
                    to_char(c.create_date, 'MM') as month,
                    c.state,
                    c.user_id,
                    c.section_id,
                    c.categ_id,
                    c.partner_id,
                    c.company_id,
                    count(*) as nbr,
                    0 as avg_answers,
                    0.0 as perc_done,
                    0.0 as perc_cancel,
                    to_char(avg(date_closed-c.create_date), 'DD"d" HH24:MI:SS') as delay_close
                from
                    crm_phonecall c
                group by to_char(c.create_date, 'YYYY'), to_char(c.create_date, 'MM'),\
                     c.state, c.user_id,c.section_id, c.categ_id,c.partner_id,c.company_id
            )""")

crm_phonecall_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
