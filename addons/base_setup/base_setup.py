# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

import simplejson
import cgi
import pooler
import tools
from osv import fields, osv
from tools.translate import _
from lxml import etree

# Specify Your Terminology will move to 'partner' module
class specify_partner_terminology(osv.osv_memory):
    _name = 'base.setup.terminology'
    _inherit = 'res.config'
    _columns = {
        'partner': fields.selection([
            ('Customer','Customer'),
            ('Client','Client'),
            ('Member','Member'),
            ('Patient','Patient'),
            ('Partner','Partner'),
            ('Donor','Donor'),
            ('Guest','Guest'),
            ('Tenant','Tenant')
        ], 'How do you call a Customer', required=True ),
    }
    _defaults={
        'partner' :'Customer',
    }

    def make_translations(self, cr, uid, ids, name, type, src, value, res_id=0, context=None):
        trans_obj = self.pool.get('ir.translation')
        user_obj = self.pool.get('res.users')
        context_lang = user_obj.browse(cr, uid, uid, context=context).context_lang
        existing_trans_ids = trans_obj.search(cr, uid, [('name','=',name), ('lang','=',context_lang), ('type','=',type), ('src','=',src), ('res_id','=',res_id)])
        if existing_trans_ids:
            trans_obj.write(cr, uid, existing_trans_ids, {'value': value}, context=context)
        else:
            create_id = trans_obj.create(cr, uid, {'name': name,'lang': context_lang, 'type': type, 'src': src, 'value': value , 'res_id': res_id}, context=context)
        return {}

    def execute(self, cr, uid, ids, context=None):
        def _case_insensitive_replace(ref_string, src, value):
            import re
            pattern = re.compile(src, re.IGNORECASE)
            return pattern.sub(_(value), _(ref_string))
        trans_obj = self.pool.get('ir.translation')
        fields_obj = self.pool.get('ir.model.fields')
        menu_obj = self.pool.get('ir.ui.menu')
        act_window_obj = self.pool.get('ir.actions.act_window')
        for o in self.browse(cr, uid, ids, context=context):
            #translate label of field
            field_ids = fields_obj.search(cr, uid, [('field_description','ilike','Customer')])
            for f_id in fields_obj.browse(cr ,uid, field_ids, context=context):
                field_ref = f_id.model_id.model + ',' + f_id.name
                self.make_translations(cr, uid, ids, field_ref, 'field', f_id.field_description, _case_insensitive_replace(f_id.field_description,'Customer',o.partner), context=context)
            #translate help tooltip of field
            for obj in self.pool.models.values():
                for field_name, field_rec in obj._columns.items():
                    if field_rec.help.lower().count('customer'):
                        field_ref = obj._name + ',' + field_name
                        self.make_translations(cr, uid, ids, field_ref, 'help', field_rec.help, _case_insensitive_replace(field_rec.help,'Customer',o.partner), context=context)
            #translate menuitems
            menu_ids = menu_obj.search(cr,uid, [('name','ilike','Customer')])
            for m_id in menu_obj.browse(cr, uid, menu_ids, context=context):
                menu_name = m_id.name
                menu_ref = 'ir.ui.menu' + ',' + 'name'
                self.make_translations(cr, uid, ids, menu_ref, 'model', menu_name, _case_insensitive_replace(menu_name,'Customer',o.partner), res_id=m_id.id, context=context)
            #translate act window name
            act_window_ids = act_window_obj.search(cr, uid, [('name','ilike','Customer')])
            for act_id in act_window_obj.browse(cr ,uid, act_window_ids, context=context):
                act_ref = 'ir.actions.act_window' + ',' + 'name'
                self.make_translations(cr, uid, ids, act_ref, 'model', act_id.name, _case_insensitive_replace(act_id.name,'Customer',o.partner), res_id=act_id.id, context=context)
            #translate act window tooltips
            act_window_ids = act_window_obj.search(cr, uid, [('help','ilike','Customer')])
            for act_id in act_window_obj.browse(cr ,uid, act_window_ids, context=context):
                act_ref = 'ir.actions.act_window' + ',' + 'help'
                self.make_translations(cr, uid, ids, act_ref, 'model', act_id.help, _case_insensitive_replace(act_id.help,'Customer',o.partner), res_id=act_id.id, context=context)
        return {}

# Preferences wizard for Sales & CRM.
# It is defined here because it is inherited independently in modules sale, crm,
# plugin_outlook and plugin_thunderbird.
class sale_config_settings(osv.osv_memory):
    _name = 'sale.config.settings'
    _inherit = 'res.config.settings'
    _columns = {
        'module_crm': fields.boolean('CRM'),
        'module_plugin_thunderbird': fields.boolean('Thunderbird Plugin', readonly= False,
            help="""The plugin allows you archive email and its attachments to the selected
                OpenERP objects. You can select a partner, or a lead and 
                attach the selected mail as a .eml file in
                the attachment of a selected record. You can create documents for CRM Lead,
                Partner from the selected emails.
                This installs the module plugin_thunderbird."""),
        'module_plugin_outlook': fields.boolean('Outlook Plugin',
            help="""The Outlook plugin allows you to select an object that you would like to add
                to your email and its attachments from MS Outlook. You can select a partner, 
                or a lead object and archive a selected
                email into an OpenERP mail message with attachments.
                This installs the module plugin_outlook."""),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
