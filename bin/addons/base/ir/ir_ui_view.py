# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2008 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id$
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields,osv
from lxml import etree
import tools
import netsvc
import os

def _check_xml(self, cr, uid, ids, context={}):
    for view in self.browse(cr, uid, ids, context):
        eview = etree.fromstring(view.arch)
        frng = tools.file_open(os.path.join('base','rng',view.type+'.rng'))
        relaxng = etree.RelaxNG(file=frng)
        if not relaxng.validate(eview):
            logger = netsvc.Logger()
            logger.notifyChannel('init', netsvc.LOG_ERROR, 'The view do not fit the required schema !')
            logger.notifyChannel('init', netsvc.LOG_ERROR, relaxng.error_log.last_error)
            print view.arch
            return False
    return True

class CustomView(osv.osv):
    _name = 'ir.ui.view.custom'
    _columns = {
        'name': fields.char('View Name',size=64,  required=True),
        'model': fields.char('Model', size=64, required=True),
        'priority': fields.integer('Priority', required=True),
        'type': fields.selection((
            ('tree','Tree'),
            ('form','Form'),
            ('graph', 'Graph'),
            ('calendar', 'Calendar')), 'View Type', required=True),
        'arch': fields.text('View Architecture', required=True),
        'inherit_id': fields.many2one('ir.ui.view', 'Inherited View'),
        'field_parent': fields.char('Childs Field',size=64),
        'user_id': fields.many2one('res.users', 'User'),
        'ref_id': fields.many2one('ir.ui.view', 'Orignal View'),
    }
    _defaults = {
        'arch': lambda *a: '<?xml version="1.0"?>\n<tree title="Unknwown">\n\t<field name="name"/>\n</tree>',
        'priority': lambda *a: 16
    }
    _order = "priority"
    _constraints = [
        (_check_xml, 'Invalid XML for View Architecture!', ['arch'])
    ]
CustomView()

class view(osv.osv):
    _name = 'ir.ui.view'
    _columns = {
        'name': fields.char('View Name',size=64,  required=True),
        'model': fields.char('Model', size=64, required=True),
        'priority': fields.integer('Priority', required=True),
        'type': fields.selection((
            ('tree','Tree'),
            ('form','Form'),
            ('graph', 'Graph'),
            ('calendar', 'Calendar')), 'View Type', required=True),
        'arch': fields.text('View Architecture', required=True),
        'inherit_id': fields.many2one('ir.ui.view', 'Inherited View'),
        'field_parent': fields.char('Childs Field',size=64),
    }
    _defaults = {
        'arch': lambda *a: '<?xml version="1.0"?>\n<tree title="Unknwown">\n\t<field name="name"/>\n</tree>',
        'priority': lambda *a: 16
    }
    _order = "priority"
    _constraints = [
        (_check_xml, 'Invalid XML for View Architecture!', ['arch'])
    ]
    
    def read(self,cr, uid, ids, fields=None, context={}, load='_classic_read'):

        if type(ids) != type([]):
            ids = [ids]
            
        result = super(view, self).read(cr, uid, ids, fields, context, load)
        
        if context.get('read', False) != 'custom':
            for rs in result:
                if rs.get('model',False) == 'board.board':
                    cr.execute("select id,arch,ref_id from ir_ui_view_custom where user_id=%d and ref_id=%d", (uid, rs['id']))
                    oview = cr.dictfetchall()
                    if oview:
                        rs['arch'] = oview[0]['arch']
                
        return result
    
    def write(self, cr, uid, ids, vals, context={}):
        exist = self.pool.get('ir.ui.view').browse(cr, uid, ids[0])
        if exist.model == 'board.board':
            vids = self.pool.get('ir.ui.view.custom').search(cr, uid, [('user_id','=',uid), ('ref_id','=',ids[0])])
            if not vids:
#                if context.get('write') == 'custom':
                
                old = self.pool.get('ir.ui.view').read(cr, uid, ids)[0]

                del old['id']
                old['user_id'] = uid
                old['ref_id'] = ids[0]
                nid = self.pool.get('ir.ui.view.custom').create(cr, uid, old)
                result = self.pool.get('ir.ui.view.custom').write(cr, uid, [nid], vals)
                return result
            else:
                result = super(view, self).write(cr, uid, vids, vals, context)
                return result
        
    	result = super(view, self).write(cr, uid, ids, vals, context)
        cr.commit()
    	return result
view()

class view_sc(osv.osv):
    _name = 'ir.ui.view_sc'
    _columns = {
        'name': fields.char('Shortcut Name', size=64, required=True),
        'res_id': fields.many2one('ir.values','Resource Ref.', ondelete='cascade'),
        'sequence': fields.integer('Sequence'),
        'user_id': fields.many2one('res.users', 'User Ref.', required=True, ondelete='cascade'),
        'resource': fields.char('Resource Name', size=64, required=True)
    }

    def get_sc(self, cr, uid, user_id, model='ir.ui.menu', context={}):
        ids = self.search(cr, uid, [('user_id','=',user_id),('resource','=',model)], context=context)
        return self.read(cr, uid, ids, ['res_id','name'], context=context)

    _order = 'sequence'
    _defaults = {
        'resource': lambda *a: 'ir.ui.menu',
        'user_id': lambda obj, cr, uid, context: uid,
    }
view_sc()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

