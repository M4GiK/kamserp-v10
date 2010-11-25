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

class action_traceability(osv.osv_memory):
    """
    This class defines a function action_traceability for wizard

    """
    _name = "action.traceability"
    _description = "Action traceability "

    def action_traceability(self, cr, uid, ids, context={}):
        """ It traces the information of a product
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        @return: A dictionary of values
        """
        lot_id = ids
        type1 = context['type'] or 'move_history_ids2'
        field = context['field'] or 'tracking_id'
        obj = self.pool.get('stock.move')
        ids = obj.search(cr, uid, [(field, 'in',lot_id)])
        if type1 == 'move_history_ids2':
            new_id = ids[1]
        else:
            new_id = ids[0]
        cr.execute('select id from ir_ui_view where model=%s and field_parent=%s and type=%s', ('stock.move', type1, 'tree'))
        view_id = cr.fetchone()[0]
        value = {
            'domain': "[('id','in',["+','.join(map(str, [new_id]))+"])]",
            'name': ((type1=='move_history_ids2') and 'Upstream Traceability') or 'Downstream Traceability',
            'view_type': 'tree',
            'res_model': 'stock.move',
            'field_parent': type1,
            'view_id': (view_id,'View'),
            'type': 'ir.actions.act_window',
            'nodestroy':True,
        }
        return value

action_traceability()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

