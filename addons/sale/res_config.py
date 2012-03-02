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

MODULE_LIST = [
               'analytic_user_function', 'analytic_journal_billing_rate', 'import_sugarcrm',
               'import_google', 'crm_caldav', 'wiki_sale_faq', 'base_contact','sale_layout','warning',
               'google_map', 'fetchmail_crm', 'plugin_thunderbird', 'plugin_outlook','account_analytic_analysis',
               'project_timesheet', 'account_analytic_analysis', 'project_mrp', 'delivery',
               'sale_margin', 'sale_journal'
]

class sale_configuration(osv.osv_memory):
    _inherit = 'res.config'

    _columns = {
        'sale_orders': fields.boolean('Based on Sales Orders',),
        'deli_orders': fields.boolean('Based on Delivery Orders'),
        'task_work': fields.boolean('Based on Tasks\' Work',
                                    help="""
                                    This allows to you transfer the entries under tasks defined for Project Management to
                                    the Timesheet line entries for particular date and particular user  with the effect of creating, editing and deleting either ways.
                                    Automatically creates project tasks from procurement lines.
                                    It installs the project_timesheet and project_mrp module.
                                    """),
        'timesheet': fields.boolean('Based on Timesheet',
                                    help = """For modifying account analytic view to show important data to project manager of services companies,
                                    You can also view the report of account analytic summary user-wise as well as month wise
                                    ,It installs the account_analytic_analysis module."""),
        'order_policy': fields.selection([
            ('manual', 'Invoice Based on Sales Orders'),
            ('picking', 'Invoice Based on Deliveries'),
        ], 'Main Method Based On', required=True, help="You can generate invoices based on sales orders or based on shippings."),
        'module_delivery': fields.boolean('Do you charge the delivery?',
                                   help ="""
                                   Allows you to add delivery methods in sale orders and picking,
                                   You can define your own carrier and delivery grids for prices.
                                   It installs the delivery module.
                                   """),
        'time_unit': fields.many2one('product.uom','Working Time Unit'),
        'picking_policy' : fields.boolean("Deliver all products at once?", help = "You can set picking policy from sale order that will allow you to deliver all products at one."),
        'group_sale_delivery_address':fields.boolean("Multiple Address",help="This allows you to set different delivery address and picking address.It assigns Multiple Address group to employee."),
        'group_sale_disc_per_sale_order_line':fields.boolean("Discounts per sale order lines ",help="This allows you to apply discounts per sale order lines. It assigns Discounts per sale order lines group to employee."),
        'module_sale_layout':fields.boolean("Notes & subtotals per line",help="Allows to format sale order lines using notes, separators, titles and subtotals. It installs the sale_layout module."),
        'module_warning': fields.boolean("Alerts by products or customers",
                                  help="""To trigger warnings in OpenERP objects.
                                  Warning messages can be displayed for objects like sale order, purchase order, picking and invoice. The message is triggered by the form's onchange event.
                                  It installs the warning module."""),
        'module_sale_margin': fields.boolean("Display Margin For Users",
                        help="""This adds the 'Margin' on sales order,
                        This gives the profitability by calculating the difference between the Unit Price and Cost Price.
                        .It installs the sale_margin module."""),
        'module_sale_journal': fields.boolean("Invoice journal?",
                        help="""This allows you to categorise your sales and deliveries (picking lists) between different journals.
                        It installs the sale_journal module."""),
        'module_analytic_user_function' : fields.boolean("User function by contracts",
                                    help="""This allows you to define what is the default function of a specific user on a given account
                                    This is mostly used when a user encodes his timesheet: the values are retrieved and the fields are auto-filled. But the possibility to change these values is still available.
                                    It Installs analytic_user_function module."""),
        'module_analytic_journal_billing_rate' : fields.boolean("Billing rates by contracts",
                                    help=""" This allows you to define what is the default invoicing rate for a specific journal on a given account.
                                    It installs analytic_journal_billing_rate module.
                                    """),
        'module_account_analytic_analysis': fields.boolean('Contracts',
                                    help = """
                                    For modifying account analytic view to show important data to project manager of services companies,
                                    You can also view the report of account analytic summary user-wise as well as month wise.
                                    It installs the account_analytic_analysis module."""),
    }

    def get_default_applied_groups(self, cr, uid, ids, context=None):
        applied_groups = {}
        user_obj = self.pool.get('res.users')
        dataobj = self.pool.get('ir.model.data')

        groups = []
        user_group_ids = user_obj.browse(cr, uid, uid, context=context).groups_id

        for group_id in user_group_ids:
            groups.append(group_id.id)

        for id in groups:
            key_id = dataobj.search(cr, uid,[('res_id','=',id),('model','=','res.groups')],context=context)
            key = dataobj.browse(cr, uid, key_id[0], context=context).name
            applied_groups[key] = True

        return applied_groups

    def get_default_installed_modules(self, cr, uid, ids, context=None):
        module_obj = self.pool.get('ir.module.module')
        data_obj = self.pool.get('ir.model.data')
        module_ids = module_obj.search(cr, uid,
                           [('name','in',MODULE_LIST),
                            ('state','in',['to install', 'installed', 'to upgrade'])],
                           context=context)
        installed_modules = dict([(mod.name,True) for mod in module_obj.browse(cr, uid, module_ids, context=context)])
        if installed_modules.get('project_mrp') and installed_modules.get('project_timesheet'):
            installed_modules['task_work'] = True
            prod_id = data_obj.get_object(cr, uid, 'product', 'product_consultant').id
            uom_id = self.pool.get('product.product').browse(cr, uid, prod_id).uom_id.id
            defaults.update({'time_unit': uom_id})
        if installed_modules.get('account_analytic_analysis'):
            installed_modules['timesheet'] = True
            prod_id = data_obj.get_object(cr, uid, 'product', 'product_consultant').id
            uom_id = self.pool.get('product.product').browse(cr, uid, prod_id).uom_id.id
            defaults.update({'time_unit': uom_id})
        return installed_modules

    def get_default_sale_configs(self, cr, uid, ids, context=None):
        ir_values_obj = self.pool.get('ir.values')
        data_obj = self.pool.get('ir.model.data')
        menu_obj = self.pool.get('ir.ui.menu')
        result = {}
        invoicing_groups_id = [gid.id for gid in data_obj.get_object(cr, uid, 'sale', 'menu_invoicing_sales_order_lines').groups_id]
        picking_groups_id = [gid.id for gid in data_obj.get_object(cr, uid, 'sale', 'menu_action_picking_list_to_invoice').groups_id]
        group_id = data_obj.get_object(cr, uid, 'base', 'group_sale_salesman').id
        for menu in ir_values_obj.get(cr, uid, 'default', False, ['ir.ui.menu']):
            if menu[1] == 'groups_id' and group_id in menu[2][0]:
                if group_id in invoicing_groups_id:
                    result['sale_orders'] = True
                if group_id in picking_groups_id:
                    result['deli_orders'] = True
        for res in ir_values_obj.get(cr, uid, 'default', False, ['sale.order']):
            result[res[1]] = res[2]
        return result
    
    def get_default_groups(self, cr, uid, ids, context=None):
        ir_values_obj = self.pool.get('ir.values')
        result = {}
        for res in ir_values_obj.get(cr, uid, 'default', False, ['res.users']):
            result[res[1]] = res[2]
        return result
    
    def default_get(self, cr, uid, fields_list, context=None):
        result = super(sale_configuration, self).default_get(
            cr, uid, fields_list, context=context)
        for method in dir(self):
            if method.startswith('get_default_'):
                result.update(getattr(self, method)(cr, uid, [], context))
        return result
    
    _defaults = {
        'order_policy': 'manual',
        'time_unit': lambda self, cr, uid, c: self.pool.get('product.uom').search(cr, uid, [('name', '=', _('Hour'))], context=c) and self.pool.get('product.uom').search(cr, uid, [('name', '=', _('Hour'))], context=c)[0] or False,
    }

    def create(self, cr, uid, vals, context=None):
        ids = super(sale_configuration, self).create(cr, uid, vals, context=context)
        self.execute(cr, uid, [ids], vals, context=context)
        return ids

    def write(self, cr, uid, ids, vals, context=None):
        self.execute(cr, uid, ids, vals, context=context)
        return super(sale_configuration, self).write(cr, uid, ids, vals, context=context)

    def execute(self, cr, uid, ids, vals, context=None):
        #TODO: TO BE IMPLEMENTED
        for method in dir(self):
            if method.startswith('set_'):
                vals['modules'] = MODULE_LIST
                getattr(self, method)(cr, uid, ids, vals, context)
        return True

    def set_modules(self, cr, uid, ids, vals, context=None):
        module_obj = self.pool.get('ir.module.module')
        MODULE_LIST = vals.get('modules')
        if vals.get('task_work'):
            vals.update({'project_timesheet': True,'project_mrp': True})
        if vals.get('timesheet'):
            vals.update({'account_analytic_analysis': True})
        for k, v in vals.items():
            if k in MODULE_LIST:
                installed = self.get_default_installed_modules(cr, uid, [k], context)
                if v == True and not installed.get(k):
                    module_id = module_obj.search(cr, uid, [('name','=',k)])
                    module_obj.button_immediate_install(cr, uid, module_id, context)
                elif v == False and installed.get(k):
                    module_id = module_obj.search(cr, uid, [('name','=',k)])
                    module_obj.button_uninstall(self, cr, uid, module_id, context=None)
                    module_obj.button_upgrade(self, cr, uid, module_id, context=None)

    def set_sale_defaults(self, cr, uid, ids, vals, context=None):
        ir_values_obj = self.pool.get('ir.values')
        data_obj = self.pool.get('ir.model.data')
        menu_obj = self.pool.get('ir.ui.menu')
        res = {}
        wizard = self.browse(cr, uid, ids)[0]
        group_id = data_obj.get_object(cr, uid, 'base', 'group_sale_salesman').id

        if wizard.sale_orders:
            menu_id = data_obj.get_object(cr, uid, 'sale', 'menu_invoicing_sales_order_lines').id
            menu_obj.write(cr, uid, menu_id, {'groups_id':[(4,group_id)]})
            ir_values_obj.set(cr, uid, 'default', False, 'groups_id', ['ir.ui.menu'], [(4,group_id)])

        if wizard.deli_orders:
            menu_id = data_obj.get_object(cr, uid, 'sale', 'menu_action_picking_list_to_invoice').id
            menu_obj.write(cr, uid, menu_id, {'groups_id':[(4,group_id)]})
            ir_values_obj.set(cr, uid, 'default', False, 'groups_id', ['ir.ui.menu'], [(4,group_id)])
            
        if wizard.picking_policy:
            ir_values_obj.set(cr, uid, 'default', False, 'picking_policy', ['sale.order'], 'one')

        if wizard.time_unit:
            prod_id = data_obj.get_object(cr, uid, 'product', 'product_consultant').id
            product_obj = self.pool.get('product.product')
            product_obj.write(cr, uid, prod_id, {'uom_id': wizard.time_unit.id, 'uom_po_id': wizard.time_unit.id})

        ir_values_obj.set(cr, uid, 'default', False, 'order_policy', ['sale.order'], wizard.order_policy)
        if wizard.task_work and wizard.time_unit:
            company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
            self.pool.get('res.company').write(cr, uid, [company_id], {
                'project_time_mode_id': wizard.time_unit.id
            }, context=context)
            
        return res

    def set_groups(self, cr, uid, ids, vals, context=None):
        data_obj = self.pool.get('ir.model.data')
        users_obj = self.pool.get('res.users')
        groups_obj = self.pool.get('res.groups')
        ir_values_obj = self.pool.get('ir.values')
        dummy,user_group_id = data_obj.get_object_reference(cr, uid, 'base', 'group_user')
        for group in vals.keys():
            if group.startswith('group_'):
                dummy,group_id = data_obj.get_object_reference(cr, uid, 'base', group)
                if vals[group]:
                    groups_obj.write(cr, uid, [user_group_id], {'implied_ids': [(4,group_id)]})
                    users_obj.write(cr, uid, [uid], {'groups_id': [(4,group_id)]})
                    ir_values_obj.set(cr, uid, 'default', False, 'groups_id', ['res.users'], [(4,group_id)])
                else:
                    groups_obj.write(cr, uid, [user_group_id], {'implied_ids': [(3,group_id)]})
                    users_obj.write(cr, uid, [uid], {'groups_id': [(3,group_id)]})
                    ir_values_obj.set(cr, uid, 'default', False, 'groups_id', ['res.users'], [(3,group_id)])

    def onchange_tax_policy(self, cr, uid, ids, tax_policy, tax_value, context=None):
        res = {'value': {}}
        if isinstance(tax_value, (int)):
            self.set_default_taxes(cr, uid, ids, {'tax_value': [tax_value]}, context=context)
        self.set_tax_policy(cr, uid, ids, {'tax_policy': tax_policy}, context=context)
        return res
    
    def set_default_taxes(self, cr, uid, ids, vals, context=None):
        ir_values_obj = self.pool.get('ir.values')
        taxes = self._check_default_tax(cr, uid, context=context)
        if isinstance(vals.get('tax_value'), list):
            taxes = vals.get('tax_value')
        if taxes:
            ir_values_obj.set(cr, uid, 'default', False, 'tax_id', ['sale.order'], taxes[0])
            ir_values_obj.set(cr, uid, 'default', False, 'tax_id', ['sale.order.line'], taxes)
            ir_values_obj.set(cr, uid, 'default', False, 'taxes_id', ['product.product'], taxes)

sale_configuration()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: