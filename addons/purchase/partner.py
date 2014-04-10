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

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _purchase_order_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,{'purchase_order_count': 0, 'supplier_invoice_count': 0}), ids))
        invoice_ids = self.pool.get('account.invoice').search(cr,uid, [('type', '=', 'in_invoice'), ('partner_id', '=', ids[0])])
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = {
                    'purchase_order_count': len(partner.purchase_order_ids),
                    'supplier_invoice_count': len(invoice_ids),
                }
        return res
    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}

        default.update({'purchase_order_ids': []})

        return super(res_partner, self).copy(cr, uid, id, default=default, context=context)

    def _commercial_fields(self, cr, uid, context=None):
        return super(res_partner, self)._commercial_fields(cr, uid, context=context) + ['property_product_pricelist_purchase']

    _columns = {
        'property_product_pricelist_purchase': fields.property(
          type='many2one', 
          relation='product.pricelist', 
          domain=[('type','=','purchase')],
          string="Purchase Pricelist", 
          help="This pricelist will be used, instead of the default one, for purchases from the current partner"),
        'purchase_order_count': fields.function(_purchase_order_count, string='# of Purchase Order', type='integer', multi="count"),
        'purchase_order_ids': fields.one2many('purchase.order','partner_id','Purchase Order'),
        'invoice_ids': fields.one2many('account.invoice','partner_id','Supplier Invoices'),
        'supplier_invoice_count': fields.function(_purchase_order_count, string='# Supplier Invoices', type='integer', multi="count"),
    }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

