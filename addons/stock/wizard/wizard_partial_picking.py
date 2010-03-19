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

import time
import netsvc
from tools.misc import UpdateableStr, UpdateableDict
import pooler

import wizard
from osv import osv
import tools
from tools.translate import _

_moves_arch = UpdateableStr()
_moves_fields = UpdateableDict()

_moves_arch_end = '''<?xml version="1.0"?>
<form string="Picking result">
    <label string="The picking has been successfully made !" colspan="4"/>
    <field name="back_order_notification" colspan="4" nolabel="1"/>
</form>'''

_moves_fields_end = {
    'back_order_notification': {'string':'Back Order' ,'type':'text', 'readonly':True}
                     }

def make_default(val):
    def fct(uid, data, state):
        return val
    return fct

def _to_xml(s):
    return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def _get_moves(self, cr, uid, data, context):
    pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
    pick = pick_obj.browse(cr, uid, [data['id']], context)[0]
    res = {}

    _moves_fields.clear()
    _moves_arch_lst = ['<?xml version="1.0"?>', '<form string="Make picking">']

    for m in pick.move_lines:
        if m.state in ('done', 'cancel'):
            continue
        quantity = m.product_qty
        if m.state!='assigned':
            quantity = 0
            _moves_fields
            
        _moves_arch_lst.append('<field name="move%s" />' % (m.id,))
        _moves_fields['move%s' % m.id] = {
                'string': _to_xml(m.name),
                'type' : 'float', 'required' : True, 'default' : make_default(quantity)}

        if (pick.type == 'in') and (m.product_id.cost_method == 'average'):
            price=0
            if hasattr(m, 'purchase_line_id') and m.purchase_line_id:
                price=m.purchase_line_id.price_unit

            currency=0
            if hasattr(pick, 'purchase_id') and pick.purchase_id:
                currency=pick.purchase_id.pricelist_id.currency_id.id

            _moves_arch_lst.append('<group col="6"><field name="uom%s" nolabel="1"/>\
                    <field name="price%s"/>' % (m.id,m.id,))

            _moves_fields['price%s' % m.id] = {'string': 'Unit Price',
                    'type': 'float', 'required': True, 'default': make_default(price)}

            _moves_fields['uom%s' % m.id] = {'string': 'UOM', 'type': 'many2one',
                    'relation': 'product.uom', 'required': True,
                    'default': make_default(m.product_uom.id)}

            _moves_arch_lst.append('<field name="currency%d" nolabel="1"/></group>' % (m.id,))
            _moves_fields['currency%s' % m.id] = {'string': 'Currency',
                    'type': 'many2one', 'relation': 'res.currency',
                    'required': True, 'default': make_default(currency)}
        
                    
        _moves_arch_lst.append('<newline/>')

                
        _moves_arch_lst.append('<newline/>')
        res.setdefault('moves', []).append(m.id)
    
    _moves_arch_lst.append('<field name="partner_id%d"/>' % (m.id,))
    _moves_fields['partner_id%s' % m.id] ={'string':'Partner', 
            'type':'many2one', 'relation':'res.partner', 'required' : '1'}
    _moves_arch_lst.append('<newline/>')
    _moves_arch_lst.append('<field name="address_id%d"/>' % (m.id,))
    
    _moves_fields['address_id%s' % m.id] ={'string':'Delivery Address', 
                                                'type':'many2one', 'relation':'res.partner.address', 'required' : '1'}
    _moves_arch_lst.append('</form>')
    _moves_arch.string = '\n'.join(_moves_arch_lst)
    return res

def _do_split(self, cr, uid, data, context):
    move_obj = pooler.get_pool(cr.dbname).get('stock.move')
    pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
    delivery_obj = pooler.get_pool(cr.dbname).get('stock.delivery')
    pick = pick_obj.browse(cr, uid, [data['id']])[0]
    new_picking = None
    new_moves = []

    complete, too_many, too_few = [], [], []
    pool = pooler.get_pool(cr.dbname)
    for move in move_obj.browse(cr, uid, data['form'].get('moves',[])):
        if move.product_qty == data['form']['move%s' % move.id]:
            complete.append(move)
        elif move.product_qty > data['form']['move%s' % move.id]:
            too_few.append(move)
        else:
            too_many.append(move)

        # Average price computation
        if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
            product_obj = pool.get('product.product')
            currency_obj = pool.get('res.currency')
            users_obj = pool.get('res.users')
            uom_obj = pool.get('product.uom')

            product = product_obj.browse(cr, uid, [move.product_id.id])[0]
            user = users_obj.browse(cr, uid, [uid])[0]

            qty = data['form']['move%s' % move.id]
            uom = data['form']['uom%s' % move.id]
            price = data['form']['price%s' % move.id]
            currency = data['form']['currency%s' % move.id]

            qty = uom_obj._compute_qty(cr, uid, uom, qty, product.uom_id.id)
            pricetype=pool.get('product.price.type').browse(cr,uid,user.company_id.property_valuation_price_type.id)
            if (qty > 0):
                new_price = currency_obj.compute(cr, uid, currency,
                        user.company_id.currency_id.id, price)
                new_price = uom_obj._compute_price(cr, uid, uom, new_price,
                        product.uom_id.id)
                if product.qty_available<=0:
                    new_std_price = new_price
                else:
                    # Get the standard price
                    amount_unit=product.price_get(pricetype.field, context)[product.id]
                    new_std_price = ((amount_unit * product.qty_available)\
                        + (new_price * qty))/(product.qty_available + qty)
                        
                # Write the field according to price type field
                product_obj.write(cr, uid, [product.id],
                        {pricetype.field: new_std_price})
                move_obj.write(cr, uid, [move.id], {'price_unit': new_price})

    for move in too_few:
        if not new_picking:

            new_picking = pick_obj.copy(cr, uid, pick.id,
                    {
                        'name': pool.get('ir.sequence').get(cr, uid, 'stock.picking'),
                        'move_lines' : [],
                        'state':'draft',
                    })
        if data['form']['move%s' % move.id] != 0:

            new_obj = move_obj.copy(cr, uid, move.id,
                {
                    'product_qty' : data['form']['move%s' % move.id],
                    'product_uos_qty':data['form']['move%s' % move.id],
                    'picking_id' : new_picking,
                    'state': 'assigned',
                    'move_dest_id': False,
                    'partner_id': data['form']['partner_id%s' % move.id],
                    'address_id': data['form']['address_id%s' % move.id],
                    'price_unit': move.price_unit,
                })
            partner_id = False
            if move.picking_id:
                    partner_id = move.picking_id.address_id and (move.picking_id.address_id.partner_id and move.picking_id.address_id.partner_id.id or False) or False
            delivery_id = delivery_obj.search(cr,uid, [('name','=',pick.name)]) 
            if  not  delivery_id :
                delivery_id = delivery_obj.create(cr, uid, {
                        'name':  pick.name,                                 
                        'partner_id': partner_id,
                        'date': move.date,
                        'product_delivered':[(6,0, [new_obj])]
                    }, context=context)   
            if not isinstance(delivery_id, (int, long)): 
               delivery_id=delivery_id[0]
               delivery_obj.write(cr, uid, [delivery_id], {'product_delivered': [(4, new_obj)]})
                        
        move_obj.write(cr, uid, [move.id],
                {
                    'product_qty' : move.product_qty - data['form']['move%s' % move.id],
                    'product_uos_qty':move.product_qty - data['form']['move%s' % move.id],
                  #  'delivered_id':delivery_id
                })

    if new_picking:
        move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
        for move in too_many:
            move_obj.write(cr, uid, [move.id],
                    {
                        'product_qty' : data['form']['move%s' % move.id],
                        'product_uos_qty': data['form']['move%s' % move.id],
                        'picking_id': new_picking,
                    })
    else:
        for move in too_many:
            move_obj.write(cr, uid, [move.id],
                    {
                        'product_qty': data['form']['move%s' % move.id],
                        'product_uos_qty': data['form']['move%s' % move.id]
                    })

    # At first we confirm the new picking (if necessary)
    wf_service = netsvc.LocalService("workflow")
    if new_picking:
        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
    # Then we finish the good picking
    if new_picking:
        pick_obj.write(cr, uid, [pick.id], {'backorder_id': new_picking})
        pick_obj.action_move(cr, uid, [new_picking])
        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
        wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
    else:
        pick_obj.action_move(cr, uid, [pick.id])
        wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
    bo_name = ''
    if new_picking:
        bo_name = pick_obj.read(cr, uid, [new_picking], ['name'])[0]['name']
    return {'new_picking':new_picking or False, 'back_order':bo_name}

def _get_default(self, cr, uid, data, context):
    if data['form']['back_order']:
        data['form']['back_order_notification'] = _('Back Order %s Assigned to this Picking.') % (tools.ustr(data['form']['back_order']),)
    return data['form']

class partial_picking(wizard.interface):

    states = {
        'init': {
            'actions': [ _get_moves ],
            'result': {'type': 'form', 'arch': _moves_arch, 'fields': _moves_fields,
                'state' : (
                    ('end', 'Cancel', 'gtk-cancel'),
                    ('split', 'Make Picking', 'gtk-apply', True)
                )
            },
        },
        'split': {
            'actions': [ _do_split ],
            'result': {'type': 'state', 'state': 'end2'},
        },
        'end2': {
            'actions': [ _get_default ],
            'result': {'type': 'form', 'arch': _moves_arch_end,
                'fields': _moves_fields_end,
                'state': (
                    ('end', 'Close'),
                )
            },
        },
    }

partial_picking('stock.partial_picking')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

