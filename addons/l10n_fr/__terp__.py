# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 JAILLET Simon - CrysaLEAD - www.crysalead.fr
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


{
    'name': 'France - Plan Comptable G\xc3\xa9n\xc3\xa9ral',
    'version': '1.0',
    'category': 'Localisation/Account Charts',
    'description': """This is the module to manage the accounting chart for France in Open ERP.

Credits: Sistheo Zeekom CrysaLEAD
""",
    'author': 'OpenERP',
    'website': 'http://www.openerp.com',
    'depends': ['base', 'account', 'account_chart', 'account_report', 'base_vat'],
    'init_xml': [],
    'update_xml': [   'report.xml',
    'pcg.xml',
    'l10n_fr_pcg_taxes.xml',
    'tax.xml',
    'fiscal_templates_fr.xml',
    'l10n_fr_pcg_account_report.xml',
    'l10n_fr_pcg_report.xml',
    'l10n_fr_pcg_wizard.xml',
    'l10n_fr_pcg_view.xml',
    'security/ir.model.access.csv'],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '0012865552406941',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
