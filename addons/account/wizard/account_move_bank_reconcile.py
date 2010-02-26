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
import wizard
import netsvc
import pooler
import time
from tools.translate import _
import tools
from osv import fields, osv


class account_move_bank_reconcile(osv.osv_memory):
    
    _name = "account.move.bank.reconcile"
    _description = "Move bank reconcile"
    _columns = {
                'journal_id':fields.many2one('account.journal',  'Journal', required=True),
                
              }
    def _action_open_window(self, cr, uid, ids, context):
             """
            cr is the current row, from the database cursor,
            uid is the current user’s ID for security checks,
            ID is the account move bank reconcile’s ID or list of IDs if we want more than one
            This function Open  account move line   on given journal_id.
            """
             for form in  self.read(cr, uid, ids):
                 cr.execute('select default_credit_account_id from account_journal where id=%s', (form['journal_id'],))
                 account_id = cr.fetchone()[0]
                 if not account_id:
                     raise osv.except_osv(_('Error'), _('You have to define the bank account\nin the journal definition for reconciliation.'))
                 return {
                    'domain': "[('journal_id','=',%d), ('account_id','=',%d), ('state','<>','draft')]" % (form['journal_id'],account_id),
                    'name': _('Standard Encoding'),
                    
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.move.line',
                    'view_id': False,
                    'context': "{'journal_id':%d}" % (form['journal_id'],),
                    'type': 'ir.actions.act_window'
                     }

account_move_bank_reconcile()