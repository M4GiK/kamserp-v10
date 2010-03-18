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

import tools
from osv import fields,osv


class hr_expense_report(osv.osv):
    _name = "hr.expense.report"
    _description = "Expenses Statistics"
    _auto = False
    _rec_name = 'date'
    _columns = {
        'date': fields.date('Date', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        'product_id':fields.many2one('product.product', 'Product', readonly=True),
        'product_qty':fields.float('Qty', readonly=True),
        'employee_id': fields.many2one('hr.employee', "Employee's Name", readonly=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice',readonly=True),
        'department_id':fields.many2one('hr.department','Department',readonly=True),
        'company_id':fields.many2one('res.company', 'Company', readonly=True),
        'user_id':fields.many2one('res.users', 'User', readonly=True),
        'price_total':fields.float('Total Price', readonly=True),
        'price_average':fields.float('Average Price', readonly=True),
        'nbr':fields.integer('# of Lines', readonly=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Waiting confirmation'),
            ('accepted', 'Accepted'),
            ('invoiced', 'Invoiced'),
            ('paid', 'Reimbursed'),
            ('cancelled', 'Cancelled')],
            'State', readonly=True),
    }
    _order = 'date desc'
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_expense_report')
        cr.execute("""
            create or replace view hr_expense_report as (
                 select
                     min(l.id) as id,
                     s.date as date,
                     s.employee_id,
                     s.invoice_id,
                     s.department_id,
                     to_char(s.date, 'YYYY') as year,
                     to_char(s.date, 'MM') as month,
                     l.product_id as product_id,
                     sum(l.unit_quantity * u.factor) as product_qty,
                     s.user_id as user_id,
                     s.company_id as company_id,
                     sum(l.unit_quantity*l.unit_amount) as price_total,
                     (sum(l.unit_quantity*l.unit_amount)/sum(l.unit_quantity * u.factor))::decimal(16,2) as price_average,
                     count(*) as nbr,
                     s.state
                     from
                 hr_expense_line l
                 left join
                     hr_expense_expense s on (s.id=l.expense_id)
                     left join product_uom u on (u.id=l.uom_id)
                 group by
                     s.date, l.product_id,s.invoice_id,
                     s.department_id,
                     l.uom_id, s.user_id, s.state,
                     s.company_id,s.employee_id
            )
        """)
hr_expense_report()

