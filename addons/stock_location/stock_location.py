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
from datetime import *
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _

class stock_location_route(osv.osv):
    _inherit = 'stock.location.route'
    _description = "Inventory Routes"

    _columns = {
        'push_ids': fields.one2many('stock.location.path', 'route_id', 'Push Rules'),
        'product_selectable': fields.boolean('Selectable on Product'),
        'product_categ_selectable': fields.boolean('Selectable on Product Category'),
        'warehouse_selectable': fields.boolean('Selectable on Warehouse'),
    }
    _defaults = {
        'product_selectable': True
    }

class stock_warehouse(osv.osv):
    _inherit = 'stock.warehouse'
    _columns = {
        'route_id': fields.many2one('stock.location.route', 'Default Delivery Route', domain="[('warehouse_selectable', '=', True)]", help='Default route through the warehouse'),
    }


class stock_location_path(osv.osv):
    _name = "stock.location.path"
    _description = "Pushed Flows"
    _order = "name"
    _columns = {
        'name': fields.char('Operation Name', size=64, required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'route_id': fields.many2one('stock.location.route', 'Route'),
        'location_from_id': fields.many2one('stock.location', 'Source Location', ondelete='cascade', select=1, required=True),
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', ondelete='cascade', select=1, required=True),
        'delay': fields.integer('Delay (days)', help="Number of days to do this transition"),
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")], "Invoice Status",
            required=True,), 
        'picking_type_id': fields.many2one('stock.picking.type', 'Type of the new Operation', required=True, help="This is the picking type associated with the different pickings"), 
        'auto': fields.selection(
            [('auto','Automatic Move'), ('manual','Manual Operation'),('transparent','Automatic No Step Added')],
            'Automatic Move',
            required=True, select=1,
            help="This is used to define paths the product has to follow within the location tree.\n" \
                "The 'Automatic Move' value will create a stock move after the current one that will be "\
                "validated automatically. With 'Manual Operation', the stock move has to be validated "\
                "by a worker. With 'Automatic No Step Added', the location is replaced in the original move."
            ),
        'propagate': fields.boolean('Propagate cancel and split', help='If checked, when the previous move is cancelled or split, the move generated by this move will too'),
    }
    _defaults = {
        'auto': 'auto',
        'delay': 1,
        'invoice_state': 'none',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'procurement.order', context=c),
        'propagate': True,
    }
    def _apply(self, cr, uid, rule, move, context=None):
        move_obj = self.pool.get('stock.move')
        newdate = (datetime.strptime(move.date, '%Y-%m-%d %H:%M:%S') + relativedelta(days=rule.delay or 0)).strftime('%Y-%m-%d')
        if rule.auto=='transparent':
            move_obj.write(cr, uid, [move.id], {
                'date': newdate,
                'location_dest_id': rule.location_dest_id.id
            })
            if rule.location_dest_id.id<>move.location_dest_id.id:
                move_obj._push_apply(self, cr, uid, move.id, context)
            return move.id
        else:
            move_id = move_obj.copy(cr, uid, move.id, {
                'location_id': move.location_dest_id.id,
                'location_dest_id': rule.location_dest_id.id,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'company_id': rule.company_id and rule.company_id.id or False,
                'date_expected': newdate,
                'picking_id': False,
                'picking_type_id': rule.picking_type_id and rule.picking_type_id.id or False,
                'rule_id': rule.id,
                'propagate': rule.propagate, 
            })
            move_obj.write(cr, uid, [move.id], {
                'move_dest_id': move_id,
            })
            move_obj.action_confirm(cr, uid, [move_id], context=None)
            return move_id


class procurement_rule(osv.osv):
    _inherit = 'procurement.rule'

    _columns = {
        'delay': fields.integer('Number of Days'),
        'partner_address_id': fields.many2one('res.partner', 'Partner Address'),
        'propagate': fields.boolean('Propagate cancel and split', help='If checked, when the previous move of the move (which was generated by a next procurement) is cancelled or split, the move generated by this move will too'),
    }
    _defaults = {
        'propagate': True, 
        'delay': 0, 
    }


class procurement_order(osv.osv):
    _inherit = 'procurement.order'
    _columns = {
        'route_ids': fields.many2many('stock.location.route', 'stock_location_route_procurement', 'procurement_id', 'route_id', 'Followed Route', help="Preferred route to be followed by the procurement order"),
        }
    
    def _run_move_create(self, cr, uid, procurement, context=None):
        d = super(procurement_order, self)._run_move_create(cr, uid, procurement, context=context)
        d.update({
            'route_ids': [(4,x.id) for x in procurement.route_ids],  
        })
        if procurement.rule_id:
            newdate = (datetime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S') - relativedelta(days=procurement.rule_id.delay or 0)).strftime('%Y-%m-%d %H:%M:%S')
            d.update({
                'date': newdate,
                'propagate': procurement.rule_id.propagate, 
            })
        return d

    def _find_suitable_rule(self, cr, uid, procurement, context=None):
        rule_id = super(procurement_order, self)._find_suitable_rule(cr, uid, procurement, context=context)
        if not rule_id:
            rule_id = self._search_suitable_rule(cr, uid, procurement, [('location_id', '=', procurement.location_id.id)], context=context) #action=move
            rule_id = rule_id and rule_id[0] or False
        return rule_id

    def _search_suitable_rule(self, cr, uid, procurement, domain, context=None):
        '''we try to first find a rule among the ones defined on the procurement order group and if none is found, we try on the routes defined for the product, and finally we fallback on the default behavior'''
        categ_obj = self.pool.get("product.category")
        categ_id = procurement.product_id.categ_id.id
        route_ids = [x.id for x in procurement.route_ids + procurement.product_id.route_ids + procurement.product_id.categ_id.total_route_ids]
        res = self.pool.get('procurement.rule').search(cr, uid, domain + [('route_id', 'in', route_ids)], order = 'route_sequence, sequence', context=context)
        if not res:
            res = self.pool.get('procurement.rule').search(cr, uid, domain + [('route_id', '=', False)], order='sequence', context=context)
        return res


class product_putaway_strategy(osv.osv):
    _name = 'product.putaway'
    _description = 'Put Away Strategy'
    _columns = {
        'product_categ_id':fields.many2one('product.category', 'Product Category', required=True),
        'location_id': fields.many2one('stock.location','Parent Location', help="Parent Destination Location from which a child bin location needs to be chosen", required=True), #domain=[('type', '=', 'parent')], 
        'method': fields.selection([('fixed', 'Fixed Location')], "Method", required = True),
        'location_spec_id': fields.many2one('stock.location','Specific Location', help="When the location is specific, it will be put over there"), #domain=[('type', '=', 'parent')],
    }

# TODO: move this on stock module

class product_removal_strategy(osv.osv):
    _name = 'product.removal'
    _description = 'Removal Strategy'
    _order = 'sequence'
    _columns = {
        'product_categ_id': fields.many2one('product.category', 'Category', required=True), 
        'sequence': fields.integer('Sequence'),
        'method': fields.selection([('fifo', 'FIFO'), ('lifo', 'LIFO')], "Method", required = True),
        'location_id': fields.many2one('stock.location', 'Locations', required=True),
    }

class product_product(osv.osv):
    _inherit = 'product.product'
    _columns = {
        'route_ids': fields.many2many('stock.location.route', 'stock_route_product', 'product_id', 'route_id', 'Routes', domain="[('product_selectable', '=', True)]"), #Adds domain
    }

class product_category(osv.osv):
    _inherit = 'product.category'
    
    
    def calculate_total_routes(self, cr, uid, ids, name, args, context=None):
        res = {}
        route_obj = self.pool.get("stock.location.route")
        for categ in self.browse(cr, uid, ids, context=context):
            categ2 = categ
            routes = [x.id for x in categ.route_ids]
            while categ2.parent_id:
                categ2 = categ2.parent_id
                routes += [x.id for x in categ2.route_ids]
            res[categ.id] = routes
        return res
        
    _columns = {
        'route_ids': fields.many2many('stock.location.route', 'stock_location_route_categ', 'categ_id', 'route_id', 'Routes', domain="[('product_categ_selectable', '=', True)]"),
        'removal_strategy_ids': fields.one2many('product.removal', 'product_categ_id', 'Removal Strategies'),
        'putaway_strategy_ids': fields.one2many('product.putaway', 'product_categ_id', 'Put Away Strategies'),
        'total_route_ids': fields.function(calculate_total_routes, relation='stock.location.route', type='many2many', string='Total routes', readonly=True),
    }

    

class stock_move_putaway(osv.osv):
    _name = 'stock.move.putaway'
    _description = 'Proposed Destination'
    _columns = {
        'move_id': fields.many2one('stock.move', required=True),
        'location_id': fields.many2one('stock.location', 'Location', required=True),
        'lot_id': fields.many2one('stock.production.lot', 'Lot'),
        'quantity': fields.float('Quantity', required=True),
    }


class stock_quant(osv.osv):
    _inherit = "stock.quant"
    def check_preferred_location(self, cr, uid, move, context=None):
        # moveputaway_obj = self.pool.get('stock.move.putaway')
        if move.putaway_ids and move.putaway_ids[0]:
            #Take only first suggestion for the moment
            return move.putaway_ids[0].location_id
        else:
            return super(stock_quant, self).check_preferred_location(cr, uid, move, context=context)


class stock_move(osv.osv):
    _inherit = 'stock.move'
    _columns = {
        'putaway_ids': fields.one2many('stock.move.putaway', 'move_id', 'Put Away Suggestions'), 
        'route_ids': fields.many2many('stock.location.route', 'stock_location_route_move', 'move_id', 'route_id', 'Destination route', help="Preferred route to be followed by the procurement order"),
    }

    def _push_apply(self, cr, uid, moves, context):
        categ_obj = self.pool.get("product.category")
        push_obj = self.pool.get("stock.location.path")
        for move in moves:
            if not move.move_dest_id:
                categ_id = move.product_id.categ_id.id
                routes = [x.id for x in move.product_id.route_ids + move.product_id.categ_id.total_route_ids]
                rules = push_obj.search(cr, uid, [('route_id', 'in', routes), ('location_from_id', '=', move.location_dest_id.id)], context=context)
                if rules: 
                    rule = push_obj.browse(cr, uid, rules[0], context=context)
                    push_obj._apply(cr, uid, rule, move, context=context)
        return True

    # Create the stock.move.putaway records
    def _putaway_apply(self,cr, uid, ids, context=None):
        moveputaway_obj = self.pool.get('stock.move.putaway')
        for move in self.browse(cr, uid, ids, context=context):
            putaway = self.pool.get('stock.location').get_putaway_strategy(cr, uid, move.location_dest_id, move.product_id, context=context)
            if putaway:
                # Should call different methods here in later versions
                # TODO: take care of lots
                if putaway.method == 'fixed' and putaway.location_spec_id:
                    moveputaway_obj.create(cr, uid, {'move_id': move.id,
                                                     'location_id': putaway.location_spec_id.id,
                                                     'quantity': move.product_uom_qty}, context=context)
        return True

    def action_assign(self, cr, uid, ids, context=None):
        result = super(stock_move, self).action_assign(cr, uid, ids, context=context)
        self._putaway_apply(cr, uid, ids, context=context)
        return result

    def action_confirm(self, cr, uid, ids, context=None):
        result = super(stock_move, self).action_confirm(cr, uid, ids, context)
        moves = self.browse(cr, uid, ids, context=context)
        self._push_apply(cr, uid, moves, context=context)
        return result

    def _prepare_procurement_from_move(self, cr, uid, move, context=None):
        """
            Next to creating the procurement order, it will propagate the routes
        """
        vals = super(stock_move, self)._prepare_procurement_from_move(cr, uid, move, context=context)
        vals['route_ids'] = [(4, x.id) for x in move.route_ids]
        return vals


class stock_location(osv.osv):
    _inherit = 'stock.location'
    _columns = {
        'removal_strategy_ids': fields.one2many('product.removal', 'location_id', 'Removal Strategies'),
        'putaway_strategy_ids': fields.one2many('product.putaway', 'location_id', 'Put Away Strategies'),
    }

    def get_putaway_strategy(self, cr, uid, location, product, context=None):
        pa = self.pool.get('product.putaway')
        categ = product.categ_id
        categs = [categ.id, False]
        while categ.parent_id:
            categ = categ.parent_id
            categs.append(categ.id)

        result = pa.search(cr,uid, [
            ('location_id', '=', location.id),
            ('product_categ_id', 'in', categs)
        ], context=context)
        if result:
            return pa.browse(cr, uid, result[0], context=context)
        #return super(stock_location, self).get_putaway_strategy(cr, uid, location, product, context=context)

    def get_removal_strategy(self, cr, uid, location, product, context=None):
        pr = self.pool.get('product.removal')
        categ = product.categ_id
        categs = [categ.id, False]
        while categ.parent_id:
            categ = categ.parent_id
            categs.append(categ.id)

        result = pr.search(cr,uid, [
            ('location_id', '=', location.id),
            ('product_categ_id', 'in', categs)
        ], context=context)
        if result:
            return pr.browse(cr, uid, result[0], context=context).method
        return super(stock_location, self).get_removal_strategy(cr, uid, location, product, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
