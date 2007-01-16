##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
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
import re

def _check(self, cr, uid, data, context):
	for invoice in pooler.get_pool(cr.dbname).get('account.invoice').browse(cr, uid, data['ids'], context):
		if not invoice.bank_id:
			raise wizard.except_wizard('UserError','The invoice "%s" has no bank associated !' % (invoice.number,))
		if not re.compile('[0-9][0-9]?\-[0-9]+-[0-9]+').match(invoice.bank_id.bvr_number or ''):
			raise wizard.except_wizard('UserError','Your bank BVR number should be of the form 0X-XXX-X !\nSee invoice "%s".' % (invoice.number,))

	return {}

class wizard_report(wizard.interface):
	states = {
		'init': {
			'actions': [_check], 
			'result': {'type':'print', 'report':'l10n_ch.bvr', 'state':'end'}
		}
	}
wizard_report('l10n_ch.bvr.check')


