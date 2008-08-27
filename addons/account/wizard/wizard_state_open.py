##############################################################################
#
# Copyright (c) 2004-2008 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# #
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import wizard
import pooler
import netsvc

form = '''<?xml version="1.0"?>
<form string="Open Invoice">
    <label string="Are you sure you want to open this invoice ?"/>
    <newline/>
    <label string="(Invoice should be unreconciled if you want to open it)"/>
</form>'''

fields = {
}

def _change_inv_state(self, cr, uid, data, context):
    pool_obj = pooler.get_pool(cr.dbname)
    data_inv = pool_obj.get('account.invoice').browse(cr, uid, data['ids'][0])
    if data_inv.reconciled:
        raise wizard.except_wizard('Warning', 'Invoice is already reconciled')
    wf_service = netsvc.LocalService("workflow")
    res = wf_service.trg_validate(uid, 'account.invoice', data['ids'][0], 'open_test', cr)
    return {}

class wiz_state_open(wizard.interface):
    states = {
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch':form, 'fields':fields, 'state':[('yes','Yes'),('end','No')]}
        },
        'yes': {
            'actions': [_change_inv_state],
            'result': {'type':'state', 'state':'end'}
        }
    }
wiz_state_open('account.wizard_paid_open')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
