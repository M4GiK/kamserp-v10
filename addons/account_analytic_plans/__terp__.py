# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Multiple-plans management in Analytic Accounting',
    'version': '1.0',
    'category': 'Generic Modules/Accounting',
    'description': """This module allows to use several analytic plans, according to the general journal,
so that multiple analytic lines are created when the invoice or the entries
are confirmed.

For example, you can define the following analytic structure:
  Projects
      Project 1
          SubProj 1.1
          SubProj 1.2
      Project 2
  Salesman
      Eric
      Fabien

Here, we have two plans: Projects and Salesman. An invoice line must
be able to write analytic entries in the 2 plans: SubProj 1.1 and
Fabien. The amount can also be split. The following example is for
an invoice that touches the two subproject and assigned to one salesman:

Plan1:
    SubProject 1.1 : 50%
    SubProject 1.2 : 50%
Plan2:
    Eric: 100%

So when this line of invoice will be confirmed, it will generate 3 analytic lines,
for one account entry.
        """,
    'author': 'Tiny',
    'website': 'http://www.openerp.com',
    'depends': ['account', 'account_analytic_default'],
    'init_xml': [],
    'update_xml': [   'security/ir.model.access.csv',
    'model_wizard.xml',
    'account_analytic_plans_view.xml',
    'account_analytic_plans_report.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '0018550331377437',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
