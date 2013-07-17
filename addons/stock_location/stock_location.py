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
    _name = 'stock.location.route'
    _description = "Inventory Routes"
    _order = 'sequence'
    _columns = {
        'name': fields.char('Route Name', required=True),
        'sequence': fields.integer('Sequence'),
        'pull_ids': fields.one2many('procurement.rule', 'route_id', 'Pull Rules'),
        'push_ids': fields.one2many('stock.location.path', 'route_id', 'Push Rules'),
    }
    _defaults = {
        'sequence': lambda self,cr,uid,ctx: 0,
    }

class stock_warehouse(osv.osv):
    _inherit = 'stock.warehouse'
    _columns = {
        'route_id': fields.many2one('stock.location.route', help='Default route through the warehouse'), 
    }


class stock_location_path(osv.osv):
    _name = "stock.location.path"
    _description = "Pushed Flows"
    _columns = {
        'name': fields.char('Operation', size=64),
        'company_id': fields.many2one('res.company', 'Company'),
        'route_id': fields.many2one('stock.location.route', 'Route'),

        'product_id' : fields.many2one('product.product', 'Products', ondelete='cascade', select=1),

        'location_from_id' : fields.many2one('stock.location', 'Source Location', ondelete='cascade', select=1, required=True),
        'location_dest_id' : fields.many2one('stock.location', 'Destination Location', ondelete='cascade', select=1, required=True),
        'delay': fields.integer('Delay (days)', help="Number of days to do this transition"),
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")], "Invoice Status",
            required=True,),
        'picking_type': fields.selection([('out','Sending Goods'),('in','Getting Goods'),('internal','Internal')], 'Shipping Type', required=True, select=True, help="Depending on the company, choose whatever you want to receive or send products"),
        'auto': fields.selection(
            [('auto','Automatic Move'), ('manual','Manual Operation'),('transparent','Automatic No Step Added')],
            'Automatic Move',
            required=True, select=1,
            help="This is used to define paths the product has to follow within the location tree.\n" \
                "The 'Automatic Move' value will create a stock move after the current one that will be "\
                "validated automatically. With 'Manual Operation', the stock move has to be validated "\
                "by a worker. With 'Automatic No Step Added', the location is replaced in the original move."
        ),
    }
    _defaults = {
        'auto': 'auto',
        'delay': 1,
        'invoice_state': 'none',
        'picking_type': 'internal',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'procurement.order', context=c)
    }
    def _apply(self, cr, uid, rule, move, context=None):
        move_obj = self.pool.get('stock.move')
        newdate = (datetime.strptime(move.date, '%Y-%m-%d %H:%M:%S') + relativedelta(days=rule.delay or 0)).strftime('%Y-%m-%d')
        if rule.auto=='transparent':
            move_obj.write(cr, uid, [move.id], {
                'date': newdate,
                'location_dest_id': rule.location_dest_id.id
            })
            vals = {}
# TODO journal_id was to be removed?
#             if route.journal_id:
#                 vals['stock_journal_id'] = route.journal_id.id
            vals['type'] = rule.picking_type
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
                'type': move_obj.get_type_from_usage(cr, uid, move.location_id, move.location_dest_id, context=context)
            })
            move_obj.write(cr, uid, [move.id], {
                'move_dest_id': move_id,
            })
            move_obj.action_confirm(cr, uid, [move_id], context=None)
            return move_id


class procurement_rule(osv.osv):
    _inherit = 'procurement.rule'
    _columns = {
        'route_id': fields.many2one('stock.location.route', 'Route',
            help="If route_id is False, the rule is global"),
        'delay': fields.integer('Number of Hours'),
        'procure_method': fields.selection([('make_to_stock','Make to Stock'),('make_to_order','Make to Order')], 'Procure Method', required=True, help="'Make to Stock': When needed, take from the stock or wait until re-supplying. 'Make to Order': When needed, purchase or produce for the procurement request."),
        #'type_proc': fields.selection([('produce','Produce'),('buy','Buy'),('move','Move')], 'Type of Procurement', required=True),
        'partner_address_id': fields.many2one('res.partner', 'Partner Address'),
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")], "Invoice Status",
            required=True,),
    }
    _defaults = {
        'procure_method': 'make_to_stock',
        'invoice_state': 'none',
    }




class procurement_order(osv.osv):
    _inherit = 'procurement.order'
    
    _columns = {
        'route_ids': fields.many2many('stock.location.route', 'stock_location_route_procurement', 'procurement_id', 'route_id', 'Destination route', help="Preferred route to be followed by the procurement order"),
        }
    
    def _run_move_create(self, cr, uid, procurement, context=None):
        d = super(procurement_order, self)._run_move_create(cr, uid, procurement, context=context)
        if procurement.move_dest_id:
            date = procurement.move_dest_id.date
        else:
            date = procurement.date_planned
        procure_method = procurement.rule_id and procurement.rule_id.procure_method or 'make_to_stock'
        newdate = (datetime.strptime(date, '%Y-%m-%d %H:%M:%S') - relativedelta(days=procurement.rule_id.delay or 0)).strftime('%Y-%m-%d %H:%M:%S')
        d.update({
            'date': newdate,
            'procure_method': procure_method, 
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
        route_ids = [x.id for x in procurement.route_ids]
        res = self.pool.get('procurement.rule').search(cr, uid, domain + [('route_id', 'in', route_ids)], context=context)
        if not res:
            route_ids = [x.id for x in procurement.product_id.route_ids]
            res = self.pool.get('procurement.rule').search(cr, uid, domain + [('route_id', 'in', route_ids)], context=context)
            if not res:
                res = self.pool.get('procurement.rule').search(cr, uid, domain, context=context)
        return res


class product_putaway_strategy(osv.osv):
    _name = 'product.putaway'
    _description = 'Put Away Strategy'
    _columns = {
        'product_categ_id':fields.many2one('product.category', 'Product Category', required=True),
        'location_id': fields.many2one('stock.location','Parent Location', help="Parent Destination Location from which a child bin location needs to be chosen", required=True), #domain=[('type', '=', 'parent')], 
        'method': fields.selection([('empty', 'Empty'), ('fixed', 'Fixed Location')], "Method", required = True),
    }

# TODO: move this on stock module

class product_removal_strategy(osv.osv):
    _name = 'product.removal'
    _description = 'Removal Strategy'
    _order = 'sequence'
    _columns = {
        'product_categ_id': fields.many2one('product.removal', 'Category', required=True), 
        'sequence': fields.integer('Sequence'),
        'location_id': fields.many2one('stock.location', 'Locations', required=True),
    }

class product_product(osv.osv):
    _inherit = 'product.product'
    _columns = {
        'route_ids': fields.many2many('stock.location.route', 'stock_location_route_product', 'product_id', 'route_id', 'Routes'),
    }

class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
        'route_ids': fields.many2many('stock.location.route', 'stock_location_route_categ', 'categ_id', 'route_id', 'Routes'),
        #'removal_strategy_ids': fields.one2many('product.removal', 'product_categ_id', 'Removal Strategies'),
        #'putaway_strategy_ids': fields.one2many('product.putaway', 'product_categ_id', 'Put Away Strategies'),
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

class stock_move(osv.osv):
    _inherit = 'stock.move'
    _columns = {
        'cancel_cascade': fields.boolean('Cancel Cascade', help='If checked, when this move is cancelled, cancel the linked move too'),
        'putaway_ids': fields.one2many('stock.move.putaway', 'move_id', 'Put Away Suggestions'), 
    }

    def _push_apply(self, cr, uid, moves, context):
        for move in moves:
            for route in move.product_id.route_ids:
                found = False
                for rule in route.push_ids:
                    if rule.location_from_id.id == move.location_dest_id.id:
                        self.pool.get('stock.location.path')._apply(cr, uid, rule, move, context=context)
                        found = True
                        break
                if found: break
        return True

    # Create the stock.move.putaway records
    def _putaway_apply(self,cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            res = self.pool.get('stock.location').get_putaway_strategy(cr, uid, move.location_dest_id, move.product_id, context=context)
            if res:
                raise 'put away strategies not implemented yet!'
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

    def _create_procurement(self, cr, uid, move, context=None):
        """
            Next to creating the procurement order, it will propagate the routes
        """
        proc_id = super(stock_move, self)._create_procurement(cr, uid, move, context=context)
        proc_obj = self.pool.get("procurement.order")
        procs = proc_obj.search(cr, uid, [("move_id", "=", move.id)], context=context)
        routes = []
        for proc in proc_obj.browse(cr, uid, procs, context=context):
            routes += [x.id for x in proc.route_ids]
        if routes:
            proc_obj.write(cr, uid, [proc_id], {'route_ids': [(4,x) for x in routes]}, context=context)
        return proc_id


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
            return pr.browse(cr, uid, result[0], context=context)
        return super(stock_location, self).get_removal_strategy(cr, uid, location, product, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
