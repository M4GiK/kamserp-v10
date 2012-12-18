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

from openerp.osv import fields, osv

class stock_move(osv.osv):
    _inherit = 'stock.move'
    _columns = {
        'purchase_line_id': fields.many2one('purchase.order.line',
            'Purchase Order Line', ondelete='set null', select=True,
            readonly=True),
    }

stock_move()

#
# Inherit of picking to add the link to the PO
#
class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order',
            ondelete='set null', select=True),
    }

    _defaults = {
        'purchase_id': False,
    }

    def _get_partner_to_invoice(self, cr, uid, picking, context=None):
        """ Inherit the original function of the 'stock' module
            We select the partner of the sale order as the partner of the customer invoice
        """
        if picking.purchase_id:
            return picking.purchase_id.partner_id
        return super(stock_picking, self)._get_partner_to_invoice(cr, uid, picking, context=context)

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        """ Inherit the original function of the 'stock' module in order to override some
            values if the picking has been generated by a purchase order
        """
        invoice_vals = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        if picking.purchase_id:
            invoice_vals['fiscal_position'] = picking.purchase_id.fiscal_position.id
            invoice_vals['payment_term'] = picking.purchase_id.payment_term_id.id
            # Fill the date_due on the invoice, for usability purposes.
            # Note that when an invoice with a payment term is validated, the
            # date_due is always recomputed from the invoice date and the payment
            # term.
            if picking.purchase_id.payment_term_id and context.get('date_inv'):
                invoice_vals['date_due'] = self.pool.get('account.invoice').onchange_payment_term_date_invoice(cr, uid, [], picking.purchase_id.payment_term_id.id, context.get('date_inv'))['value'].get('date_due')
        return invoice_vals

    def get_currency_id(self, cursor, user, picking):
        if picking.purchase_id:
            return picking.purchase_id.pricelist_id.currency_id.id
        else:
            return super(stock_picking, self).get_currency_id(cursor, user, picking)

    def _get_comment_invoice(self, cursor, user, picking):
        if picking.purchase_id and picking.purchase_id.notes:
            if picking.note:
                return picking.note + '\n' + picking.purchase_id.notes
            else:
                return picking.purchase_id.notes
        return super(stock_picking, self)._get_comment_invoice(cursor, user, picking)

    def _get_price_unit_invoice(self, cursor, user, move_line, type):
        if move_line.purchase_line_id:
            if move_line.purchase_line_id.order_id.invoice_method == 'picking':
                return move_line.price_unit
            else:
                return move_line.purchase_line_id.price_unit
        return super(stock_picking, self)._get_price_unit_invoice(cursor, user, move_line, type)

    def _get_discount_invoice(self, cursor, user, move_line):
        if move_line.purchase_line_id:
            return 0.0
        return super(stock_picking, self)._get_discount_invoice(cursor, user, move_line)

    def _get_taxes_invoice(self, cursor, user, move_line, type):
        if move_line.purchase_line_id:
            return [x.id for x in move_line.purchase_line_id.taxes_id]
        return super(stock_picking, self)._get_taxes_invoice(cursor, user, move_line, type)

    def _get_account_analytic_invoice(self, cursor, user, picking, move_line):
        if picking.purchase_id and move_line.purchase_line_id:
            return move_line.purchase_line_id.account_analytic_id.id
        return super(stock_picking, self)._get_account_analytic_invoice(cursor, user, picking, move_line)

    def _invoice_line_hook(self, cursor, user, move_line, invoice_line_id):
        if move_line.purchase_line_id:
            invoice_line_obj = self.pool.get('account.invoice.line')
            purchase_line_obj = self.pool.get('purchase.order.line') 
            purchase_line_obj.write(cursor, user, [move_line.purchase_line_id.id], {
                'invoiced': True,
                'invoice_lines': [(4, invoice_line_id)],
            })
        return super(stock_picking, self)._invoice_line_hook(cursor, user, move_line, invoice_line_id)

    def _invoice_hook(self, cursor, user, picking, invoice_id):
        purchase_obj = self.pool.get('purchase.order')
        if picking.purchase_id:
            purchase_obj.write(cursor, user, [picking.purchase_id.id], {'invoice_ids': [(4, invoice_id)]})
        return super(stock_picking, self)._invoice_hook(cursor, user, picking, invoice_id)

class stock_partial_picking(osv.osv_memory):
    _inherit = 'stock.partial.picking'

    # Overridden to inject the purchase price as true 'cost price' when processing
    # incoming pickings.
    def _product_cost_for_average_update(self, cr, uid, move):
        if move.picking_id.purchase_id:
            return {'cost': move.purchase_line_id.price_unit,
                    'currency': move.picking_id.purchase_id.pricelist_id.currency_id.id}
        return super(stock_partial_picking, self)._product_cost_for_average_update(cr, uid, move)

# Redefinition of the new field in order to update the model stock.picking.in in the orm
# FIXME: this is a temporary workaround because of a framework bug (ref: lp996816). It should be removed as soon as
#        the bug is fixed
class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    _columns = {
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order',
            ondelete='set null', select=True),
        'warehouse_id': fields.related('purchase_id', 'warehouse_id', type='many2one', relation='stock.warehouse', string='Destination Warehouse'),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
