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

from osv import fields, osv, orm
from datetime import datetime, timedelta
import crm
import math
import time
import mx.DateTime
from tools.translate import _

class crm_lead(osv.osv):
    """ CRM Lead Case """

    _name = "crm.lead"
    _description = "Leads Cases"
    _order = "priority, id desc"
    _inherit = ['res.partner.address', 'crm.case']

    def case_open(self, cr, uid, ids, *args):
        """
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of case's Ids
        @param *args: Give Tuple Value
        """

        res = super(crm_lead, self).case_open(cr, uid, ids, *args)
        self.write(cr, uid, ids, {'date_open': time.strftime('%Y-%m-%d %H:%M:%S')})
        return res

    def _compute_day(self, cr, uid, ids, fields, args, context={}):
        """
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Openday’s IDs
        @return: difference between current date and log date
        @param context: A standard dictionary for contextual values
        """        
        cal_obj = self.pool.get('resource.calendar') 
        res_obj = self.pool.get('resource.resource')   
          
        res = {}
        for lead in self.browse(cr, uid, ids , context):
            for field in fields:
                res[lead.id] = {}
                duration = 0
                ans = False
                if field == 'day_open':
                    if lead.date_open:
                        date_create = datetime.strptime(lead.create_date, "%Y-%m-%d %H:%M:%S")
                        date_open = datetime.strptime(lead.date_open, "%Y-%m-%d %H:%M:%S")
                        ans = date_open - date_create
                        date_until = lead.date_open
                elif field == 'day_close':
                    if lead.date_closed:
                        date_create = datetime.strptime(lead.create_date, "%Y-%m-%d %H:%M:%S")
                        date_close = datetime.strptime(lead.date_closed, "%Y-%m-%d %H:%M:%S")
                        date_until = lead.date_closed
                        ans = date_close - date_create
                if ans:
                    resource_id = False
                    if lead.user_id:
                        resource_ids = res_obj.search(cr, uid, [('user_id','=',lead.user_id.id)])
                        if resource_ids:
                            resource_id = len(resource_ids) or resource_ids[0]

                    duration = float(ans.days)
                    if lead.section_id.resource_calendar_id:
                        duration =  float(ans.days) * 24                        
                        new_dates = cal_obj.interval_get(cr,
                            uid,
                            lead.section_id.resource_calendar_id and lead.section_id.resource_calendar_id.id or False,
                            mx.DateTime.strptime(lead.create_date, '%Y-%m-%d %H:%M:%S'),
                            duration,
                            resource=resource_id
                        )
                        no_days = []
                        date_until = mx.DateTime.strptime(date_until, '%Y-%m-%d %H:%M:%S')
                        for in_time, out_time in new_dates:
                            if in_time.date not in no_days:
                                no_days.append(in_time.date)                            
                            if out_time > date_until:
                                break                            
                        duration =  len(no_days)
                res[lead.id][field] = abs(int(duration))
        return res

    _columns = {

        'categ_id': fields.many2one('crm.case.categ', 'Lead Source', \
                        domain="[('section_id','=',section_id),\
                        ('object_id.model', '=', 'crm.opportunity')]"),
        'type_id': fields.many2one('crm.case.resource.type', 'Lead Type', \
                         domain="[('section_id','=',section_id),\
                        ('object_id.model', '=', 'crm.lead')]"),
        'partner_name': fields.char("Contact Name", size=64),

        'priority': fields.selection(crm.AVAILABLE_PRIORITIES, 'Priority'),
        'date_closed': fields.datetime('Closed', readonly=True),
        'stage_id': fields.many2one('crm.case.stage', 'Stage', \
                            domain="[('section_id','=',section_id),\
                            ('object_id.model', '=', 'crm.lead')]"),
        'opportunity_id': fields.many2one('crm.opportunity', 'Opportunity'),

        'user_id': fields.many2one('res.users', 'Salesman'),
        'referred': fields.char('Referred By', size=32),
        'date_open': fields.datetime('Opened', readonly=True),
        'day_open': fields.function(_compute_day, string='Days to Open', \
                                method=True, multi='day_open', type="integer", store=True),
        'day_close': fields.function(_compute_day, string='Days to Close', \
                                method=True, multi='day_close', type="integer", store=True),
        'function_name': fields.char('Function', size=64),
        }

    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'crm.lead', context=c),
        'priority': lambda *a: crm.AVAILABLE_PRIORITIES[2][0],
    }


    def convert_opportunity(self, cr, uid, ids, context=None):
        """ Precomputation for converting lead to opportunity
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of closeday’s IDs
        @param context: A standard dictionary for contextual values
        @return: Value of action in dict
        """
        if not context:
            context = {}
        context.update({'active_ids': ids})

        data_obj = self.pool.get('ir.model.data')
        data_id = data_obj._get_id(cr, uid, 'crm', 'view_crm_lead2opportunity_create')
        value = {}

        view_id = False
        if data_id:
            view_id = data_obj.browse(cr, uid, data_id, context=context).res_id
        for case in self.browse(cr, uid, ids):
            context.update({'opportunity_id': case.id})
            context.update({'active_id': case.id})
            if not case.partner_id:
                data_id = data_obj._get_id(cr, uid, 'crm', 'view_crm_lead2opportunity_partner')
                view_id1 = False
                if data_id:
                    view_id1 = data_obj.browse(cr, uid, data_id, context=context).res_id
                value = {
                        'name': _('Create Partner'),
                        'view_type': 'form',
                        'view_mode': 'form,tree',
                        'res_model': 'crm.lead2opportunity.partner',
                        'view_id': False,
                        'context': context,
                        'views': [(view_id1, 'form')],
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'nodestroy': True
                        }
                break
            else:
                value = {
                        'name': _('Create Opportunity'),
                        'view_type': 'form',
                        'view_mode': 'form,tree',
                        'res_model': 'crm.lead2opportunity',
                        'view_id': False,
                        'context': context,
                        'views': [(view_id, 'form')],
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'nodestroy': True
                        }
        return value

crm_lead()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
