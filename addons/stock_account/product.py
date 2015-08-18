# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import api
from openerp.exceptions import UserError


class product_template(osv.osv):
    _name = 'product.template'
    _inherit = 'product.template'

    _columns = {
        'valuation': fields.property(type='selection', selection=[('manual_periodic', 'Periodic (manual)'),
                                        ('real_time', 'Perpetual (automated)')], string='Inventory Valuation',
                                        help="If perpetual valuation is enabled for a product, the system will automatically create journal entries corresponding to stock moves, with product price as specified by the 'Costing Method'" \
                                             "The inventory variation account set on the product category will represent the current inventory value, and the stock input and stock output account will hold the counterpart moves for incoming and outgoing products."
                                        , required=True, copy=True),
        'cost_method': fields.property(type='selection', selection=[('standard', 'Standard Price'), ('average', 'Average Price'), ('real', 'Real Price')],
            help="""Standard Price: The cost price is manually updated at the end of a specific period (usually once a year).
                    Average Price: The cost price is recomputed at each incoming shipment and used for the product valuation.
                    Real Price: The cost price displayed is the price of the last outgoing product (will be use in case of inventory loss for example).""",
            string="Costing Method", required=True, copy=True),
        'property_stock_account_input': fields.property(
            type='many2one',
            relation='account.account',
            string='Stock Input Account',
            domain=[('deprecated', '=', False)],
            help="When doing real-time inventory valuation, counterpart journal items for all incoming stock moves will be posted in this account, unless "
                 "there is a specific valuation account set on the source location. When not set on the product, the one from the product category is used."),
        'property_stock_account_output': fields.property(
            type='many2one',
            relation='account.account',
            string='Stock Output Account',
            domain=[('deprecated', '=', False)],
            help="When doing real-time inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account, unless "
                 "there is a specific valuation account set on the destination location. When not set on the product, the one from the product category is used."),
    }

    _defaults = {
        'valuation': 'manual_periodic',
    }

    def onchange_type(self, cr, uid, ids, type):
        res = super(product_template, self).onchange_type(cr, uid, ids, type)
        if type in ('consu', 'service'):
            res = {'value': {'valuation': 'manual_periodic'}}
        return res

    @api.multi
    def _get_product_accounts(self):
        """ Add the stock accounts related to product to the result of super()
        @return: dictionary which contains information regarding stock accounts and super (income+expense accounts)
        """
        accounts = super(product_template, self)._get_product_accounts()
        accounts.update({
            'stock_input': self.property_stock_account_input or self.categ_id.property_stock_account_input_categ_id,
            'stock_output': self.property_stock_account_output or self.categ_id.property_stock_account_output_categ_id,
            'stock_valuation': self.categ_id.property_stock_valuation_account_id or False,
        })
        return accounts

    @api.multi
    def get_product_accounts(self, fiscal_pos=None):
        """ Add the stock journal related to product to the result of super()
        @return: dictionary which contains all needed information regarding stock accounts and journal and super (income+expense accounts)
        """
        accounts = super(product_template, self).get_product_accounts(fiscal_pos=fiscal_pos)
        accounts.update({'stock_journal': self.categ_id.property_stock_journal or False})
        return accounts

    def do_change_standard_price(self, cr, uid, ids, new_price, context=None):
        """ Changes the Standard Price of Product and creates an account move accordingly."""
        location_obj = self.pool.get('stock.location')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        if context is None:
            context = {}
        user_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        loc_ids = location_obj.search(cr, uid, [('usage', '=', 'internal'), ('company_id', '=', user_company_id)])
        for rec_id in ids:
            datas = self.get_product_accounts(cr, uid, rec_id, context=context)
            for location in location_obj.browse(cr, uid, loc_ids, context=context):
                c = context.copy()
                c.update({'location': location.id, 'compute_child': False})
                product = self.browse(cr, uid, rec_id, context=c)

                diff = product.standard_price - new_price
                if not diff:
                    raise UserError(_("No difference between standard price and new price!"))
                for prod_variant in product.product_variant_ids:
                    qty = prod_variant.qty_available
                    if qty:
                        # Accounting Entries
                        move_vals = {
                            'journal_id': datas['stock_journal'],
                            'company_id': location.company_id.id,
                        }
                        move_id = move_obj.create(cr, uid, move_vals, context=context)
    
                        if diff*qty > 0:
                            amount_diff = qty * diff
                            debit_account_id = datas['stock_account_input']
                            credit_account_id = datas['property_stock_valuation_account_id']
                        else:
                            amount_diff = qty * -diff
                            debit_account_id = datas['property_stock_valuation_account_id']
                            credit_account_id = datas['stock_account_output']
    
                        move_line_obj.create(cr, uid, {
                                        'name': _('Standard Price changed'),
                                        'account_id': debit_account_id,
                                        'debit': amount_diff,
                                        'credit': 0,
                                        'move_id': move_id,
                                        }, context=context)
                        move_line_obj.create(cr, uid, {
                                        'name': _('Standard Price changed'),
                                        'account_id': credit_account_id,
                                        'debit': 0,
                                        'credit': amount_diff,
                                        'move_id': move_id
                                        }, context=context)
                        move_obj.post(cr, uid, [move_id], context=context)
            self.write(cr, uid, rec_id, {'standard_price': new_price})
        return True


class product_product(osv.osv):
    _inherit = 'product.product'

    def onchange_type(self, cr, uid, ids, type):
        res = super(product_product, self).onchange_type(cr, uid, ids, type)
        if type not in ['product']:
            res = {'value': {'valuation': 'manual_periodic'}}
        return res
class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
        'property_stock_journal': fields.property(
            relation='account.journal',
            type='many2one',
            string='Stock Journal',
            help="When doing real-time inventory valuation, this is the Accounting Journal in which entries will be automatically posted when stock moves are processed."),
        'property_stock_account_input_categ_id': fields.property(
            type='many2one',
            relation='account.account',
            string='Stock Input Account',
            domain=[('deprecated', '=', False)], oldname="property_stock_account_input_categ",
            help="When doing real-time inventory valuation, counterpart journal items for all incoming stock moves will be posted in this account, unless "
                 "there is a specific valuation account set on the source location. This is the default value for all products in this category. It "
                 "can also directly be set on each product"),
        'property_stock_account_output_categ_id': fields.property(
            type='many2one',
            relation='account.account',
            domain=[('deprecated', '=', False)],
            string='Stock Output Account', oldname="property_stock_account_output_categ",
            help="When doing real-time inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account, unless "
                 "there is a specific valuation account set on the destination location. This is the default value for all products in this category. It "
                 "can also directly be set on each product"),
        'property_stock_valuation_account_id': fields.property(
            type='many2one',
            relation='account.account',
            string="Stock Valuation Account",
            domain=[('deprecated', '=', False)],
            help="When real-time inventory valuation is enabled on a product, this account will hold the current value of the products.",),
    }
