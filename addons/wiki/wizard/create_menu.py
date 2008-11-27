# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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


import time
import wizard
import osv
import pooler

section_form = '''<?xml version="1.0"?>
<form string="Create Menu">
    <separator string="Menu Information" colspan="4"/>
    <field name="menu_name"/>
    <field name="menu_parent_id"/>
</form>'''

section_fields = {
    'menu_name': {'string':'Menu Name', 'type':'char', 'required':True, 'size':64},
    'menu_parent_id': {'string':'Parent Menu', 'type':'many2one', 'relation':'ir.ui.menu', 'required':True},
}

def wiki_menu_create(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    group = pool.get('wiki.groups').browse(cr, uid, data['id'])

    action_id = pool.get('ir.actions.act_window').create(cr, uid, {
        'name': group.name,
        'view_type':'form',
        'view_mode':"tree,form",
        'context': "{'group_id':%d, 'section':%d}" % (group.id, group.section),
        'domain': "[('group_id','child_of',[%d])]" % (group.id,),
        'res_model': 'wiki.wiki'
    })
    pool.get('ir.ui.menu').create(cr, uid, {
        'name': data['form']['menu_name'],
        'parent_id': data['form']['menu_parent_id'],
        'icon': 'STOCK_JUSTIFY_FILL',
        'action': 'ir.actions.act_window,'+str(action_id)
    }, context)
    return {}

class wizard_create_menu(wizard.interface):
    states = {
        'init': {
            'actions': [], 
            'result': {'type':'form', 'arch':section_form, 'fields':section_fields, 'state':[('end','Cancel'),('create_menu','Create Menu')]}
        },
        'create_menu': {
            'actions': [wiki_menu_create], 
            'result': {
                'type':'state', 
                'state':'end'
            }
        }
    }
wizard_create_menu('wiki.create.menu')

