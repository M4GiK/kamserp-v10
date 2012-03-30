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
import pooler
from tools.translate import _

class sale_configuration(osv.osv_memory):
    _inherit = 'sale.config.settings'

    _columns = {
        'group_invoice_so_lines': fields.boolean('Based on Sales Orders',
            implied_group='sale.group_invoice_so_lines',
            help="To allow your salesman to make invoices for sale order lines using the menu 'Lines to Invoice'."),
        'group_invoice_deli_orders': fields.boolean('Based on Delivery Orders',
            implied_group='sale.group_invoice_deli_orders',
            help="To allow your salesman to make invoices for Delivery Orders using the menu 'Deliveries to Invoice'."),
        'task_work': fields.boolean('Based on Tasks\' Work',
            help="""Lets you transfer the entries under tasks defined for Project Management to
                the Timesheet line entries for particular date and particular user  with the effect of creating, editing and deleting either ways
                and to automatically creates project tasks from procurement lines.
                This installs the modules project_timesheet and project_mrp."""),
        'module_account_analytic_analysis': fields.boolean('Based on Timesheet',
            help = """For modifying account analytic view to show important data to project manager of services companies.
                You can also view the report of account analytic summary user-wise as well as month wise.
                This installs the module account_analytic_analysis."""),
        'default_order_policy': fields.selection(
            [('manual', 'Invoice Based on Sales Orders'), ('picking', 'Invoice Based on Deliveries')],
            'Main Method Based On', required=True, default_model='sale.order',
            help="You can generate invoices based on sales orders or based on shippings."),
        'module_delivery': fields.boolean('Charge Delivery Costs',
            help ="""Allows you to add delivery methods in sale orders and delivery orders.
                You can define your own carrier and delivery grids for prices.
                This installs the module delivery."""),
        'time_unit': fields.many2one('product.uom', 'Working Time Unit'),
        'default_picking_policy' : fields.boolean("Deliver all Products at Once",
            help = "You can set picking policy on sale order that will allow you to deliver all products at once."),
        'group_sale_pricelist':fields.boolean("Pricelist per Customer",
            implied_group='product.group_sale_pricelist',
            help="""Allows to manage different prices based on rules per category of customers. 
                Example: 10% for retailers, promotion of 5 EUR on this product, etc."""),
        'group_uom':fields.boolean("Allow Different Units of Measure per Product",
            implied_group='product.group_uom',
            help="""Allows you to select and maintain different units of measure per product."""),
        'group_sale_delivery_address': fields.boolean("Allow Different Addresses for Delivery and Invoice",
            implied_group='sale.group_delivery_invoice_address',
            help="Allows you to specify different delivery and invoice addresses on a sale order."),
        'group_discount_per_so_line': fields.boolean("Discount per Line",
            implied_group='sale.group_discount_per_so_line',
            help="Allows you to apply some discount per sale order line."),
        'module_sale_layout': fields.boolean("Notes & Subtotals per Line",
            help="""Allows to format sale order lines using notes, separators, titles and subtotals.
                This installs the module sale_layout."""),
        'module_warning': fields.boolean("Alerts by Products or Customers",
            help="""To raise user specific warning messages on different products used in Sales Orders, Purchase Orders, Invoices and Deliveries.
                This installs the module warning."""),
        'module_sale_margin': fields.boolean("Display Margins for Users",
            help="""This adds the 'Margin' on sales order.
                This gives the profitability by calculating the difference between the Unit Price and Cost Price.
                This installs the module sale_margin."""),
        'module_sale_journal': fields.boolean("Allow Batch Invoicing through Journals",
            help="""Allows you to categorize your sales and deliveries (picking lists) between different journals,
                and perform batch operations on journals.
                This installs the module sale_journal."""),
        'module_analytic_user_function': fields.boolean("User Function by Contract",
            help="""Allows you to define what is the default function of a specific user on a given account.
                This is mostly used when a user encodes his timesheet. The values are retrieved and the fields are auto-filled.
                But the possibility to change these values is still available.
                This installs the module analytic_user_function."""),
        'module_analytic_journal_billing_rate': fields.boolean("Billing Rates by Contract",
            help="""Allows you to define the default invoicing rate for a specific journal on a given account.
                This installs the module analytic_journal_billing_rate."""),
        'module_project_timesheet': fields.boolean("Project Timesheet"),
        'module_project_mrp': fields.boolean("Project MRP"),
    }

    def default_get(self, cr, uid, fields, context=None):
        ir_model_data = self.pool.get('ir.model.data')
        res = super(sale_configuration, self).default_get(cr, uid, fields, context)
        # task_work, time_unit depend on other fields
        res['task_work'] = res.get('module_project_mrp') and res.get('module_project_timesheet')
        if res.get('module_account_analytic_analysis'):
            product = ir_model_data.get_object(cr, uid, 'product', 'product_consultant')
            res['time_unit'] = product.uom_id.id
        return res

    def get_default_sale_config(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        default_picking_policy = ir_values.get_default(cr, uid, 'sale.order', 'picking_policy')
        return {
            'default_picking_policy': default_picking_policy == 'one',
        }

    def _get_default_time_unit(self, cr, uid, context=None):
        ids = self.pool.get('product.uom').search(cr, uid, [('name', '=', _('Hour'))], context=context)
        return ids and ids[0] or False

    _defaults = {
        'default_order_policy': 'manual',
        'time_unit': _get_default_time_unit,
    }

    def set_sale_defaults(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        ir_model_data = self.pool.get('ir.model.data')
        wizard = self.browse(cr, uid, ids)[0]

        default_picking_policy = 'one' if wizard.default_picking_policy else 'direct'
        ir_values.set_default(cr, uid, 'sale.order', 'picking_policy', default_picking_policy)

        if wizard.time_unit:
            product = ir_model_data.get_object(cr, uid, 'product', 'product_consultant')
            product.write({'uom_id': wizard.time_unit.id, 'uom_po_id': wizard.time_unit.id})

        if wizard.task_work and wizard.time_unit:
            user = self.pool.get('res.users').browse(cr, uid, uid, context)
            user.company_id.write({'project_time_mode_id': wizard.time_unit.id})

        return {}

    def onchange_task_work(self, cr, uid, ids, task_work, context=None):
        return {'value': {
            'module_project_timesheet': task_work,
            'module_project_mrp': task_work,
        }}



class account_config_settings(osv.osv_memory):
    _inherit = 'account.config.settings'
    _columns = {
        'group_analytic_account_for_sales': fields.boolean('Analytic Accounting for Sales',
            implied_group='sale.group_analytic_accounting',
            help="Allows you to specify an analytic account on sale orders."),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
