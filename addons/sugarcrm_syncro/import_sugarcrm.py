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
import sugar
import sugarcrm_fields_mapping

def import_users(self, cr, uid, context=None):
    if not context:
        context = {}
    map_user = {'Users': 
           {'name': ['first_name', 'last_name'], 
           'login': 'user_name',
           'new_password' : 'pwd_last_changed',
           } ,
       }
    user_obj = self.pool.get('res.users')
    PortType,sessionid = sugar.login(context.get('username',''), context.get('password',''))
    sugar_data = sugar.search(PortType,sessionid, 'Users')
    for val in sugar_data:
        user_ids = user_obj.search(cr, uid, [('login', '=', val.get('user_name'))])
        if user_ids:
            return user_ids[0]
        fields, datas = sugarcrm_fields_mapping.sugarcrm_fields_mapp(val, 'Users', map_user)
        openerp_val = dict(zip(fields,datas))
        openerp_val['context_lang'] = context.get('lang','en_US')
        new_user_id = user_obj.create(cr, uid, openerp_val, context)
    return new_user_id    
  
def get_lead_status(self, cr, uid, sugar_val,context=None):
    if not context:
       context = {}  
    stage_id = ''          
    stage_dict = {'status': #field in the sugarcrm database
             { #Mapping of sugarcrm stage : openerp opportunity stage 
                'New' : 'New',
                'Assigned':'Qualification',
               'In Progress': 'Proposition',
               'Recycled': 'Negotiation',
               'Dead': 'Lost'
            },}  
    stage = stage_dict['status'].get(sugar_val['status'], '')
    stage_pool = self.pool.get('crm.case.stage')
    stage_ids = stage_pool.search(cr, uid, [("type", '=', 'lead'), ('name', '=', stage)])
    for stage in stage_pool.browse(cr, uid, stage_ids, context):
        stage_id = stage.id         
    return stage_id

def get_opportunity_status(self, cr, uid, sugar_val,context=None):
    if not context:
       context = {} 
    stage_id = ''           
    stage_dict = {'sales_stage': #field in the sugarcrm database
             { #Mapping of sugarcrm stage : openerp opportunity stage Mapping
                'Need Analysis': 'New',
                'Closed Lost': 'Lost',
               'Closed Won': 'Won',
               'Value Proposition': 'Proposition',
               'Negotiation/Review': 'Negotiation'
            },}  
    stage = stage_dict['sales_stage'].get(sugar_val['sales_stage'], '')
    stage_pool = self.pool.get('crm.case.stage')
    stage_ids = stage_pool.search(cr, uid, [("type", '=', 'opportunity'), ('name', '=', stage)])
    for stage in stage_pool.browse(cr, uid, stage_ids, context):
        stage_id = stage.id         
    return stage_id
  
def import_leads(self, cr, uid, context=None):
   if not context:
       context = {} 
   user_id = import_users(self, cr, uid, context) 
   map_lead = {               
            'Leads':{'name': ['first_name','last_name'],
                   'contact_name': ['first_name','last_name'],
                   'description': 'description',
                   'partner_name': ['first_name','last_name'],
                   'email_from': 'email1',
                   'phone': 'phone_work',
                   'mobile': 'phone_mobile',
                   'write_date':'date_modified',
                   'function':'title',
                   'street': 'primary_address_street',
                   'zip': 'primary_address_postalcode',
                   'city':'primary_address_city',
                  },
               }
      
   lead_pool = self.pool.get('crm.lead')
   PortType,sessionid = sugar.login(context.get('username',''), context.get('password',''))
   sugar_data = sugar.search(PortType,sessionid, 'Leads')
   for val in sugar_data:
       fields, datas = sugarcrm_fields_mapping.sugarcrm_fields_mapp(val, 'Leads', map_lead)
       stage_id = get_lead_status(self, cr, uid, val, context)
       openerp_val = dict(zip(fields,datas))
       openerp_val['type'] = 'lead'
       openerp_val['user_id'] = user_id
       openerp_val['stage_id'] = stage_id
       new_lead_id = lead_pool.create(cr, uid, openerp_val, context)
   return new_lead_id    
        
def import_opportunities(self, cr, uid, context=None):
   if not context:
       context = {} 
   user_id = import_users(self, cr, uid, context) 
   map_opportunity = {'Opportunities':  {'name': 'name',
          'probability': 'probability',
          'planned_revenue': 'amount_usdollar',
          'date_deadline':'date_closed'
          },
      }
   lead_pool = self.pool.get('crm.lead')
   PortType,sessionid = sugar.login(context.get('username',''), context.get('password',''))
   sugar_data = sugar.search(PortType,sessionid, 'Opportunities')
   for val in sugar_data:
       fields, datas = sugarcrm_fields_mapping.sugarcrm_fields_mapp(val, 'Opportunities', map_opportunity)
       stage_id = get_opportunity_status(self, cr, uid, val, context)
       openerp_val = dict(zip(fields,datas))
       openerp_val['type'] = 'opportunity'
       openerp_val['user_id'] = user_id
       openerp_val['stage_id'] = stage_id
       new_opportunity_id = lead_pool.create(cr, uid, openerp_val, context)
   return new_opportunity_id           
        
def resolve_dependencies(self, cr, uid, dict, dep, context=None):
     if not context:
         context = {}
     for dependency in dep:
       resolve_dependencies(self, cr, uid, dict, dict[dependency]['dependencies'], context)
       dict[dependency]['process'](self, cr, uid, context)
     return True 

MAP_FIELDS = {'Opportunities':  #Object Mapping name
                     { 'dependencies' : ['Users'],  #Object to import before this table
                       'process' : import_opportunities,
                     },
                'Users' : {'dependencies' : [],
                          'process' : import_users,
                         },
              'Leads':
              { 'dependencies' : ['Users'],  #Object to import before this table
                       'process' : import_leads,
                     },  
          } 

class import_sugarcrm(osv.osv):
     """Import SugarCRM DATA"""

     _name = "import.sugarcrm"
     _description = __doc__
     _columns = {
        'lead': fields.boolean('Leads', help="If Leads is checked, SugarCRM Leads data imported in openerp crm-Lead form"),
        'opportunity': fields.boolean('Opportunities', help="If Leads is checked, SugarCRM Leads data imported in openerp crm-Opportunity form"),
         'username': fields.char('User Name', size=64),
         'password': fields.char('Password', size=24),
     }
     _defaults = {
        'lead': lambda *a: True,
        'opportunity': lambda *a: True,
     }        
     def get_key(self, cr, uid, ids, context=None):
         """Select Key as For which Module data we want import data."""
         if not context:
             context = {}
         key_list = []
         for current in self.browse(cr, uid, ids, context):
             if current.lead:
                   key_list.append('Leads')
             if current.opportunity:
                   key_list.append('Opportunities')
                
         return key_list     
              
     def import_all(self, cr, uid, ids, context=None):
           """Import all sugarcrm data into openerp module"""
           if not context:
               context = {}
           keys = self.get_key(cr, uid, ids, context)
           for key in keys:
               resolve_dependencies(self, cr, uid, MAP_FIELDS, MAP_FIELDS[key]['dependencies'], context=context)
               if MAP_FIELDS[key]['dependencies']:
                       MAP_FIELDS[key]['process'](self, cr, uid, context)
                                                                 
           obj_model = self.pool.get('ir.model.data')
           model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','import.message.form')])
           resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])
           return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'import.message',
                'views': [(resource_id,'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
            }                 

import_sugarcrm()
