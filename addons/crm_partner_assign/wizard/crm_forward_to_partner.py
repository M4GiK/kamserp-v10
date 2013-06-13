# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
from openerp.tools.translate import _


class crm_lead_forward_to_partner(osv.TransientModel):
    """ Forward info history to partners. """
    _name = 'crm.lead.forward.to.partner'

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        lead_obj = self.pool.get('crm.lead')
        partner_obj = self.pool.get('res.partner')
        email_template_obj = self.pool.get('email.template')
        base_url = self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url')
        try:
            template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'crm_partner_assign', 'email_template_lead_forward_mail')[1]
        except ValueError:
            template_id = False
        res = super(crm_lead_forward_to_partner, self).default_get(cr, uid, fields, context=context)
        active_ids = context.get('active_ids')
        default_composition_mode = context.get('default_composition_mode')
        res['assignation_lines'] = []
        if template_id:
            res['body'] = email_template_obj.get_email_template(cr, uid, template_id).body_html
        if active_ids:
            for lead in lead_obj.browse(cr, uid, active_ids, context=context):
                lead_location = []
                partner_location = []
                if lead.country_id:
                    lead_location.append(lead.country_id.name)
                if lead.city:
                    lead_location.append(lead.city)
                if (not lead.partner_assigned_id) and default_composition_mode == 'mass_mail':
                    partner_id = lead_obj.search_geo_partner(cr, uid, [lead.id], context)
                    partner = partner_obj.browse(cr, uid, partner_id, context=context)
                    if partner.country_id:
                        partner_location.append(partner.country_id.name)
                    if partner.city:
                        partner_location.append(partner.city)
                    res['assignation_lines'].append({'lead_id': lead.id,
                                                     'lead_location': ", ".join(lead_location),
                                                     'partner_assigned_id': partner_id and partner_id[lead.id] or False,
                                                     'partner_location': ", ".join(partner_location),
                                                     'lead_link': "%s/?db=%s#id=%s&model=crm.lead" % (base_url, cr.dbname, lead.id)
                                                     })
                elif default_composition_mode == 'forward':
                    if lead.partner_assigned_id.country_id:
                        partner_location.append(lead.partner_assigned_id.country_id.name)
                    if lead.partner_assigned_id.city:
                        partner_location.append(lead.partner_assigned_id.city)
                    res['assignation_lines'].append({'lead_id': lead.id,
                                                     'lead_location': ", ".join(lead_location),
                                                     'partner_assigned_id': lead.partner_assigned_id.id,
                                                     'partner_location': ", ".join(partner_location),
                                                     'lead_link': "%s/?db=%s#id=%s&model=crm.lead" % (base_url, cr.dbname, lead.id)
                                                     })
                    res['partner_id'] = lead.partner_assigned_id.id
        return res

    def action_forward(self, cr, uid, ids, context=None):
        lead_obj = self.pool.get('crm.lead')
        record = self.browse(cr, uid, ids, context=context)
        email_template_obj = self.pool.get('email.template')
        model, template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'crm_partner_assign', 'email_template_lead_forward_mail')
        if record[0].forward_type == "single":
            email_template_obj.send_mail(cr, uid, template_id, ids[0])
            active_ids = context.get('active_ids')
            if active_ids:
                lead_obj.write(cr, uid, active_ids, {'partner_assigned_id': record[0].partner_id.id, 'user_id': record[0].partner_id.user_id.id})
        else:
            for lead in record[0].assignation_lines:
                if not lead.partner_assigned_id:
                    raise osv.except_osv(_('Assignation Error'),
                                         _('Some leads have not been assigned to any partner so assign partners manualy'))
            for lead in record[0].assignation_lines:
                self.write(cr, uid, ids, {'partner_id': lead.partner_assigned_id.id,
                                          'lead_single_link': lead.lead_link,
                                          'lead_single_id': lead.lead_id.id
                                          })
                email_template_obj.send_mail(cr, uid, template_id, ids[0])
                lead_obj.write(cr, uid, [lead.lead_id.id], {'partner_assigned_id': lead.partner_assigned_id.id, 'user_id': lead.partner_assigned_id.user_id.id})
        return True

    def get_portal_url(self, cr, uid, ids, context=None):
        portal_link = "%s/?db=%s" % (self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url'), cr.dbname)
        return portal_link

    _columns = {
        'forward_type': fields.selection([('single', 'a single partner: manual selection of partner'), ('assigned', "several partners: automatic assignation, using GPS coordinates and partner's grades"), ], 'Forward selected leads to'),
        'partner_id': fields.many2one('res.partner', 'Forward Leads To'),
        'assignation_lines': fields.one2many('crm.lead.assignation', 'forward_id', 'Partner Assignation'),
        'show_mail': fields.boolean('Show the email will be sent'),
        'body': fields.html('Contents', help='Automatically sanitized HTML contents'),
        'lead_single_id': fields.many2one('crm.lead', 'Lead'),
        'lead_single_link': fields.char('Lead  Single Links', size=128),
    }

    _defaults = {
        'forward_type': 'single',
    }


class crm_lead_assignation (osv.TransientModel):
    _name = 'crm.lead.assignation'
    _columns = {
        'forward_id': fields.many2one('crm.lead.forward.to.partner', 'Partner Assignation'),
        'lead_id': fields.many2one('crm.lead', 'Lead'),
        'lead_location': fields.char('Lead Location', size=128),
        'partner_assigned_id': fields.many2one('res.partner', 'Assigned Partner'),
        'partner_location': fields.char('Partner Location', size=128),
        'lead_link': fields.char('Lead  Single Links', size=128),
    }

    def on_change_lead_id(self, cr, uid, ids, lead_id, context=None):
        if not context:
            context = {}
        if not lead_id:
            return {'value': {'lead_location': False}}
        lead = self.pool.get('crm.lead').browse(cr, uid, lead_id, context=context)
        lead_location = []
        if lead.country_id:
            lead_location.append(lead.country_id.name)
        if lead.city:
            lead_location.append(lead.city)
        return {'value': {'lead_location': ", ".join(lead_location)}}

    def on_change_partner_assigned_id(self, cr, uid, ids, partner_assigned_id, context=None):
        if not context:
            context = {}
        if not partner_assigned_id:
            return {'value': {'lead_location': False}}
        partner = self.pool.get('res.partner').browse(cr, uid, partner_assigned_id, context=context)
        partner_location = []
        if partner.country_id:
            partner_location.append(partner.country_id.name)
        if partner.city:
            partner_location.append(partner.city)
        return {'value': {'partner_location': ", ".join(partner_location)}}

# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
