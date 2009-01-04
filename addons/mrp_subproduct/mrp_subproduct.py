# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields
from osv import osv

class mrp_subproduct(osv.osv):
    _name = 'mrp.subproduct'
    _description = 'Mrp Sub Product'
    _columns={
              'product_id': fields.many2one('product.product', 'Product', required=True),
              'product_qty': fields.float('Product Qty', required=True),
              'product_uom': fields.many2one('product.uom', 'Product UOM', required=True),
              'bom_id': fields.many2one('mrp.bom', 'BoM'),
              }
    def onchange_product_id(self, cr, uid, ids, product_id,context={}):
         if product_id:
            prod=self.pool.get('product.product').browse(cr,uid,product_id)
            v = {'product_uom':prod.uom_id.id}
            return {'value': v}
         return {}

mrp_subproduct()

class mrp_bom(osv.osv):
    _name = 'mrp.bom'
    _description = 'Bill of Material'
    _inherit='mrp.bom'
    _columns={
              'sub_products':fields.one2many('mrp.subproduct', 'bom_id', 'sub_products'),
              }


mrp_bom()

class mrp_production(osv.osv):
    _name = 'mrp.production'
    _description = 'Production'
    _inherit= 'mrp.production'   

    def action_confirm(self, cr, uid, ids):
         picking_id=super(mrp_production,self).action_confirm(cr, uid, ids)
         for production in self.browse(cr, uid, ids):
             source = production.product_id.product_tmpl_id.property_stock_production.id
             for sub_product in production.bom_id.sub_products:               

                 data = {
                    'name':'PROD:'+production.name,
                    'date_planned': production.date_planned,
                    'product_id': sub_product.product_id.id,
                    'product_qty': sub_product.product_qty,
                    'product_uom': sub_product.product_uom.id,
                    'product_uos_qty': production.product_uos and production.product_uos_qty or False,
                    'product_uos': production.product_uos and production.product_uos.id or False,
                    'location_id': source,
                    'location_dest_id': production.location_dest_id.id,
                    'move_dest_id': production.move_prod_id.id,
                    'state': 'waiting',
                    'production_id':production.id
                 }
                 sub_prod_ids=self.pool.get('stock.move').create(cr, uid,data)
         return picking_id

mrp_production()
