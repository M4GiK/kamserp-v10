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
from tools.translate import _
import time

class stock_change_product_qty(osv.osv_memory):
    _name = "stock.change.product.qty"
    _description = "Change Product Quantity"
    _columns = {
        'new_quantity': fields.float('Quantity', required=True), 
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True, ondelete="cascade"), 
        'location_id': fields.many2one('stock.location', 'Location', required=True, ondelete="cascade", domain="[('usage', '=', 'internal')]"), 
    }

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id, context={}):
        """ Finds location id for changed warehouse.
        @param warehouse_id: Changed id of warehouse.
        @return: Dictionary of values.
        """
        if warehouse_id:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id, context)
            val = {'location_id': warehouse.lot_stock_id.id}
            return {'value': val}
        return {}

    def default_get(self, cr, uid, fields, context):
        """ To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        res = super(stock_change_product_qty, self).default_get(cr, uid, fields, context=context)

        wids = self.pool.get('stock.warehouse').search(cr, uid, [], context=context)
        if 'warehouse_id' in fields:
            res.update({'warehouse_id': wids and wids[0] or False})

        if 'new_quantity' in fields:
            res.update({'new_quantity': 1})
        return res

    def change_product_qty(self, cr, uid, ids, context=None):
        """ Changes the Product Quantity by making a Physical Inventory.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}

        move_ids = []
        rec_id = context and context.get('active_id', False)
        assert rec_id, _('Active ID is not set in Context')

        inventry_obj = self.pool.get('stock.inventory')
        inventry_line_obj = self.pool.get('stock.inventory.line')
        prod_obj_pool = self.pool.get('product.product')

        res_original = prod_obj_pool.browse(cr, uid, rec_id, context=context)
        for data in self.browse(cr, uid, ids, context=context):
            invntry_id = inventry_obj.create(cr , uid, {'name': 'INV:' + str(res_original.name)}, context=context)
            line_data ={
                'inventory_id' : invntry_id, 
                'product_qty' : data.new_quantity, 
                'location_id' : data.location_id.id, 
                'product_id' : rec_id, 
                'product_uom' : res_original.uom_id.id, 
                'company_id' : self.pool.get('res.users').browse(cr, uid, uid).company_id.id or False , 
            }
            line_id = inventry_line_obj.create(cr , uid, line_data, context=context)
    
            inventry_obj.action_confirm(cr, uid, [invntry_id], context=context)
            inventry_obj.action_done(cr, uid, [invntry_id], context=context)
            
        return {}

stock_change_product_qty()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
