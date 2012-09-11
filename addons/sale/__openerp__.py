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

{
    'name': 'Sales Management',
    'version': '1.0',
    'category': 'Sales Management',
    'sequence': 14,
    'summary': 'Quotations, Sale Orders, Invoicing',
    'description': """
Manage sales quotations and orders
==================================
This application allows you to manage your sales goals in an effective and efficient manner by keeping track of all sales orders and history.

It handles full sales workflow:

* **Quotation** -> **Sales order** -> **Invoice**

Preferences
-----------
* Shipping: Choice of delivery at once or partial delivery
* Invoicing: Choice of how invoice will be paid
* Incoterm: International Commercial terms

You can choose flexible invoicing method:

* *On Demand*: Invoice is created manually from Sale Order when needed
* *On Delivery Order*: Invoice is generated from picking(delivery)
* *Before Delivery*: Draft invoice is created, and it must be paid before delivery


Dashboard for Sales Manager will include
----------------------------------------
* My Quotations
* Monthly Turnover (Graph)
    """,
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': ['images/deliveries_to_invoice.jpeg','images/sale_dashboard.jpeg','images/Sale_order_line_to_invoice.jpeg','images/sale_order.jpeg','images/sales_analysis.jpeg'],
    'depends': ['stock', 'procurement', 'board', 'account_voucher'],
    'data': [
        'wizard/sale_make_invoice_advance.xml',
        'wizard/sale_line_invoice.xml',
        'wizard/sale_make_invoice.xml',
        'security/sale_security.xml',
        'security/ir.model.access.csv',
        'company_view.xml',
        'sale_workflow.xml',
        'sale_sequence.xml',
        'sale_report.xml',
        'sale_data.xml',
        'sale_view.xml',
        'res_partner_view.xml',
        'report/sale_report_view.xml',
        'stock_view.xml',
        'process/sale_process.xml',
        'board_sale_view.xml',
        'edi/sale_order_action_data.xml',
        'res_config_view.xml',
    ],
    'demo': ['sale_demo.xml'],
    'test': [
        'test/sale_order_demo.yml',
        'test/picking_order_policy.yml',
        'test/manual_order_policy.yml',
        'test/prepaid_order_policy.yml',
        'test/cancel_order.yml',
        'test/delete_order.yml',
        'test/edi_sale_order.yml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'certificate': '0058103601429',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
