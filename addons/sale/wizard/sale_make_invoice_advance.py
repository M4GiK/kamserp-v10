# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError

class sale_advance_payment_inv(osv.osv_memory):
    _name = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    _columns = {
        'advance_payment_method':fields.selection(
            [('all', 'Invoice the whole sales order'), ('percentage','Percentage'), ('fixed','Fixed price (deposit)'),
                ('lines', 'Some order lines')],
            'What do you want to invoice?', required=True,
            help="""Use Invoice the whole sale order to create the final invoice.\nUse Percentage to invoice a percentage of the total amount.\nUse Fixed Price to invoice a specific amount in advance.\nUse Some Order Lines to invoice a selection of the sales order lines."""),
        'qtty': fields.float('Quantity', digits=(16, 2), required=True),
        'product_id': fields.many2one('product.product', 'Advance Product',
            domain=[('type', '=', 'service')],
            help="Select a product of type service which is called 'Advance Product'.\nYou may have to create it and set it as a default value on this field."),
        'amount': fields.float('Advance Amount', digits=0,
            help="The amount to be invoiced in advance. \nTaxes are not taken into account for advance invoices."),
    }

    def _get_advance_product(self, cr, uid, context=None):
        try:
            product = self.pool.get('ir.model.data').get_object(cr, uid, 'sale', 'advance_product_0')
        except ValueError:
            # a ValueError is returned if the xml id given is not found in the table ir_model_data
            return False
        return product.id

    _defaults = {
        'advance_payment_method': 'all',
        'qtty': 1.0,
        'product_id': _get_advance_product,
    }

    def _translate_advance(self, cr, uid, percentage=False, context=None):
        return _("Advance of %s %%") if percentage else _("Advance of %s %s")

    def onchange_method(self, cr, uid, ids, advance_payment_method, product_id, context=None):
        if advance_payment_method == 'percentage':
            return {'value': {'amount':0, 'product_id':False }}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            return {'value': {'amount': product.list_price}}
        return {'value': {'amount': 0}}

    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        inv_line_obj = self.pool.get('account.invoice.line')
        invoice_obj = self.pool.get('account.invoice')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])

        result = []
        for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
            new_invoice = invoice_obj.new(cr, uid, {
                                'invoice_line_ids':[(0, 0, {'product_id': wizard.product_id.id})],
                                'partner_id': sale.partner_id.id,
                                'fiscal_position_id': sale.fiscal_position_id.id,
                                'type': 'out_invoice',
                            })
            inv_line = new_invoice.invoice_line_ids[0]
            inv_line.invoice_id = new_invoice #Little hack to in order to old <-> new api
            inv_line._onchange_product_id()

            res = inv_line._convert_to_write(inv_line._cache)

            # determine and check income account
            if not wizard.product_id.id :
                prop = ir_property_obj.get(cr, uid,
                            'property_account_income_categ_id', 'product.category', context=context)
                prop_id = prop and prop.id or False
                account_id = fiscal_obj.map_account(cr, uid, sale.fiscal_position_id or False, prop_id)
                if not account_id:
                    raise UserError(
                            _('There is no income account defined as global property.'))
                res['account_id'] = account_id
            if not res.get('account_id'):
                raise UserError(
                        _('There is no income account defined for this product: "%s" (id:%d).') % \
                            (wizard.product_id.name, wizard.product_id.id,))

            # determine invoice amount
            if wizard.amount <= 0.00:
                raise UserError(_('The value of Advance Amount must be positive.'))
            if wizard.advance_payment_method == 'percentage':
                inv_amount = sale.amount_untaxed * wizard.amount / 100
                if not res.get('name'):
                    res['name'] = self._translate_advance(cr, uid, percentage=True, context=dict(context, lang=sale.partner_id.lang)) % (wizard.amount)
            else:
                inv_amount = wizard.amount
                if not res.get('name'):
                    #TODO: should find a way to call formatLang() from rml_parse
                    symbol = sale.pricelist_id.currency_id.symbol
                    if sale.pricelist_id.currency_id.position == 'after':
                        symbol_order = (inv_amount, symbol)
                    else:
                        symbol_order = (symbol, inv_amount)
                    res['name'] = self._translate_advance(cr, uid, context=dict(context, lang=sale.partner_id.lang)) % symbol_order

            # create the invoice
            inv_line_values = {
                'name': res.get('name'),
                'origin': sale.name,
                'account_id': res['account_id'],
                'price_unit': inv_amount,
                'quantity': wizard.qtty or 1.0,
                'discount': False,
                'uos_id': res.get('uos_id', False),
                'product_id': wizard.product_id.id,
                'invoice_line_tax_ids': res.get('invoice_line_tax_ids'),
                'account_analytic_id': sale.project_id.id or False,
            }
            inv_values = {
                'name': sale.client_order_ref or sale.name,
                'origin': sale.name,
                'type': 'out_invoice',
                'reference': False,
                'account_id': sale.partner_id.property_account_receivable_id.id,
                'partner_id': sale.partner_invoice_id.id,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'currency_id': sale.pricelist_id.currency_id.id,
                'comment': '',
                'payment_term_id': sale.payment_term_id.id,
                'fiscal_position_id': sale.fiscal_position_id.id or sale.partner_id.property_account_position_id.id,
                'team_id': sale.team_id.id,
            }
            result.append((sale.id, inv_values))
        return result

    def _create_invoices(self, cr, uid, inv_values, sale_id, context=None):
        inv_obj = self.pool.get('account.invoice')
        sale_obj = self.pool.get('sale.order')
        inv_id = inv_obj.create(cr, uid, inv_values, context=context)
        inv_obj.compute_taxes(cr, uid, [inv_id], context=context)
        # add the invoice to the sales order's invoices
        sale_obj.write(cr, uid, sale_id, {'invoice_ids': [(4, inv_id)]}, context=context)
        return inv_id

    def create_invoices(self, cr, uid, ids, context=None):
        """ create invoices for the active sales orders """
        sale_obj = self.pool.get('sale.order')
        act_window = self.pool.get('ir.actions.act_window')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
        if wizard.advance_payment_method == 'all':
            # create the final invoices of the active sales orders
            res = sale_obj.manual_invoice(cr, uid, sale_ids, context)
            if context.get('open_invoices', False):
                return res
            return {'type': 'ir.actions.act_window_close'}

        if wizard.advance_payment_method == 'lines':
            # open the list view of sales order lines to invoice
            res = act_window.for_xml_id(cr, uid, 'sale', 'action_order_line_tree2', context)
            res['context'] = {
                'search_default_uninvoiced': 1
            }
            res['domain'] = [('order_id','=', sale_ids and sale_ids[0] or False)]
            return res
        assert wizard.advance_payment_method in ('fixed', 'percentage')

        inv_ids = []
        for sale_id, inv_values in self._prepare_advance_invoice_vals(cr, uid, ids, context=context):
            inv_ids.append(self._create_invoices(cr, uid, inv_values, sale_id, context=context))

        if context.get('open_invoices', False):
            return self.open_invoices( cr, uid, ids, inv_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def open_invoices(self, cr, uid, ids, invoice_ids, context=None):
        """ open a view on one of the given invoice_ids """
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
        tree_id = tree_res and tree_res[1] or False

        return {
            'name': _('Advance Invoice'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'account.invoice',
            'res_id': invoice_ids[0],
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'context': "{'type': 'out_invoice'}",
            'type': 'ir.actions.act_window',
        }
