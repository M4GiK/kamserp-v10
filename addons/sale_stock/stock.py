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
from openerp.tools.translate import _

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
        'sale_id': fields.many2one('sale.order', 'Sales Order', ondelete='set null', select=True),
    }
    _defaults = {
        'sale_id': False
    }

    def get_currency_id(self, cursor, user, picking):
        if picking.sale_id:
            return picking.sale_id.pricelist_id.currency_id.id
        else:
            return super(stock_picking, self).get_currency_id(cursor, user, picking)

    def _get_partner_to_invoice(self, cr, uid, picking, context=None):
        """ Inherit the original function of the 'stock' module
            We select the partner of the sales order as the partner of the customer invoice
        """
        if picking.sale_id:
            return picking.sale_id.partner_invoice_id
        return super(stock_picking, self)._get_partner_to_invoice(cr, uid, picking, context=context)

    def _get_comment_invoice(self, cursor, user, picking):
        if picking.note or (picking.sale_id and picking.sale_id.note):
            return picking.note or picking.sale_id.note
        return super(stock_picking, self)._get_comment_invoice(cursor, user, picking)

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        """ Inherit the original function of the 'stock' module in order to override some
            values if the picking has been generated by a sales order
        """
        invoice_vals = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        if picking.sale_id:
            invoice_vals['fiscal_position'] = picking.sale_id.fiscal_position.id
            invoice_vals['payment_term'] = picking.sale_id.payment_term.id
            invoice_vals['user_id'] = picking.sale_id.user_id.id
            invoice_vals['name'] = picking.sale_id.client_order_ref or ''
        return invoice_vals

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=None):
        invoice_vals = super(stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=context)
        if picking.sale_id:
            if move_line.sale_line_id:
                invoice_vals['account_analytic_id'] = self._get_account_analytic_invoice(cr, uid, picking, move_line)
        return invoice_vals

    def _get_price_unit_invoice(self, cursor, user, move_line, type):
        if move_line.sale_line_id and move_line.sale_line_id.product_id.id == move_line.product_id.id:
            uom_id = move_line.product_id.uom_id.id
            uos_id = move_line.product_id.uos_id and move_line.product_id.uos_id.id or False
            price = move_line.sale_line_id.price_unit
            coeff = move_line.product_id.uos_coeff
            if uom_id != uos_id  and coeff != 0:
                price_unit = price / coeff
                return price_unit
            return move_line.sale_line_id.price_unit
        return super(stock_picking, self)._get_price_unit_invoice(cursor, user, move_line, type)

    def _get_discount_invoice(self, cursor, user, move_line):
        if move_line.sale_line_id:
            return move_line.sale_line_id.discount
        return super(stock_picking, self)._get_discount_invoice(cursor, user, move_line)

    def _get_taxes_invoice(self, cursor, user, move_line, type):
        if move_line.sale_line_id and move_line.sale_line_id.product_id.id == move_line.product_id.id:
            return [x.id for x in move_line.sale_line_id.tax_id]
        return super(stock_picking, self)._get_taxes_invoice(cursor, user, move_line, type)

    def _get_account_analytic_invoice(self, cursor, user, picking, move_line):
        if picking.sale_id:
            return picking.sale_id.project_id.id
        return super(stock_picking, self)._get_account_analytic_invoice(cursor, user, picking, move_line)

    def _invoice_line_hook(self, cursor, user, move_line, invoice_line_id):
        if move_line.sale_line_id:
            move_line.sale_line_id.write({'invoice_lines': [(4, invoice_line_id)]})
        return super(stock_picking, self)._invoice_line_hook(cursor, user, move_line, invoice_line_id)

    def _invoice_hook(self, cursor, user, picking, invoice_id):
        sale_obj = self.pool.get('sale.order')
        if picking.sale_id:
            sale_obj.write(cursor, user, [picking.sale_id.id], {
                'invoice_ids': [(4, invoice_id)],
                })
        return super(stock_picking, self)._invoice_hook(cursor, user, picking, invoice_id)
    
    def action_done(self, cr, uid, ids, context=None):
        """ Changes picking state to done. This method is called at the end of
            the workflow by the activity "done".
        """
        for record in self.browse(cr, uid, ids, context):
            if record.type == "out" and record.sale_id:
                self.pool.get('sale.order').message_post(cr, uid, [record.sale_id.id], body=_("Products delivered"), context=context)
        return super(stock_picking, self).action_done(cr, uid, ids, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
