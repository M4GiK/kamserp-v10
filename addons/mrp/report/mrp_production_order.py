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
from osv import fields,osv
import tools


class mrp_production_order(osv.osv):
    _name = "mrp.production.order"
    _description = "Production Order Report"
    _auto = False
    _columns = {
        'name': fields.char('Year',size=64,required=False, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'), ('05','May'), ('06','June'),
                                  ('07','July'), ('08','August'), ('09','September'), ('10','October'), ('11','November'), ('12','December')],'Month',readonly=True),
        'origin': fields.char('Source Document', size=64),
        'nbr': fields.integer('# of Orders', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True, domain=[('type','<>','service')]),
        'product_qty': fields.float('Product Qty', readonly=True),
        'state': fields.selection([('draft','Draft'),
                                   ('picking_except', 'Picking Exception'),
                                   ('confirmed','Waiting Goods'),
                                   ('ready','Ready to Produce'),
                                   ('in_production','In Production'),
                                   ('cancel','Cancelled'),
                                   ('done','Done')],
                                    'State', readonly=True),
        'date_planned':fields.date('Scheduled Date'),
        'location_src_id': fields.many2one('stock.location', 'Raw Materials Location', required=True),
        'date_start': fields.datetime('Start Date',readonly=True),
        'date_finnished': fields.datetime('End Date',readonly=True),
        'location_dest_id': fields.many2one('stock.location', 'Finished Products Location', required=True),
        'company_id': fields.many2one('res.company','Company',readonly=True),
        'bom_id': fields.many2one('mrp.bom', 'Bill of Material', domain=[('bom_id','=',False)],readonly=True),
        'routing_id': fields.many2one('mrp.routing', string='Routing', on_delete='set null',readonly=True),
        'picking_id': fields.many2one('stock.picking', 'Picking list', readonly=True),
        'priority': fields.selection([('0','Not urgent'),
                                      ('1','Normal'),
                                      ('2','Urgent'),
                                      ('3','Very Urgent')],
                                       'Priority',readonly=True),


    }
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'mrp_production_order')
        cr.execute("""
            create or replace view mrp_production_order as (
                select
                     min(l.id) as id,
                     to_char(s.create_date, 'YYYY') as name,
                     to_char(s.create_date, 'MM') as month,
                     l.product_id as product_id,
                     sum(l.product_qty * u.factor) as product_qty,
                     s.company_id as company_id,
                     count(*) as nbr,
                     s.location_src_id,
                     s.location_dest_id,
                     s.bom_id,
                     s.routing_id,
                     s.picking_id,
                     s.date_start,
                     s.date_finnished,
                     s.date_planned,
                     s.origin,
                     s.priority,
                     s.state
                     from
                 mrp_production_product_line l
                 left join
                     mrp_production s on (s.id=l.production_id)
                     left join product_uom u on (u.id=l.product_uom)
                 group by
                     to_char(s.create_date, 'YYYY'),
                     to_char(s.create_date, 'MM'),
                     l.product_id,
                     l.product_uom,
                     s.bom_id,
                     s.routing_id,
                     s.picking_id,
                     s.priority,
                     s.location_src_id,
                     s.location_dest_id,
                     s.state,
                     s.date_planned,
                     s.origin,
                     s.date_start,
                     s.date_finnished,
                     s.company_id
            )""")
mrp_production_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

