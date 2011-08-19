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

from osv import fields, osv

class accounting_report(osv.osv_memory):
    _name = "accounting.report"
    _inherit = "account.common.report"
    _description = "Account Report"

    _columns = {
        'comparison': fields.boolean('Enable Comparison'),
        'account_details': fields.boolean('Details by Account'),
        'account_report_id':  fields.many2one('account.report', 'Account Reports', required=True),
    }

    _defaults={
        'enable_comparison': False,
        'display_details_per_account': False,
    }
    def _print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data['form'].update(self.read(cr, uid, ids, ['account_report_id', 'comparison', 'account_details'], context=context)[0])
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.common',
            'datas': data,
        }

accounting_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
