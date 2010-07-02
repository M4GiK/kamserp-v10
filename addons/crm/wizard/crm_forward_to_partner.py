# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

import base64
import itertools

from osv import osv, fields
import tools
from tools.translate import _

class crm_lead_forward_to_partner(osv.osv_memory):
    """Forwards lead history"""
    _name = 'crm.lead.forward.to.partner'

    _columns = {
        'name': fields.selection([('user', 'User'), ('partner', 'Partner'), \
                         ('email', 'Email Address')], 'Send to', required=True),
        'user_id': fields.many2one('res.users', "User"),
        'partner_id' : fields.many2one('res.partner', 'Partner'),
        'address_id' : fields.many2one('res.partner.address', 'Address'),
        'email_from' : fields.char('From', required=True, size=128),
        'email_to' : fields.char('To', required=True, size=128),
        'subject' : fields.char('Subject', required=True, size=128),
        'message' : fields.text('Message', required=True),
        'history': fields.selection([('latest', 'Latest email'), ('whole', 'Whole Story'), ('info', 'Case Information')], 'Send history', required=True),
        'add_cc': fields.boolean('Add as CC', required=False, help="Check this box if you want this address to be added in the CC list"\
            " for this case, in order to receive all future conversations"),
    }

    _defaults = {
        'name' : 'email',
        'history': 'latest',
        'add_cc': True,
        'email_from': lambda self, cr, uid, *a: self.pool.get('res.users')._get_email_from(cr, uid, uid)[uid]
    }

    def get_whole_history(self, cr, uid, ids, context=None):
        """This function gets whole communication history and returns as top posting style
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of history IDs
        @param context: A standard dictionary for contextual values
        """
        whole = []
        for hist_id in ids:
            whole.append(self.get_latest_history(cr, uid, hist_id, context=context))
        whole = '\n\n'.join(whole)
        return whole or ''

    def get_latest_history(self, cr, uid, hist_id, context=None):
        """This function gets latest communication and returns as top posting style
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param hist_id: Id of latest history
        @param context: A standard dictionary for contextual values
        """
        log_pool = self.pool.get('mailgate.message')
        hist = log_pool.browse(cr, uid, hist_id, context=context)
        header = '-------- Original Message --------'
        sender = 'From: %s' %(hist.email_from or '')
        to = 'To: %s' % (hist.email_to or '')
        sentdate = 'Date: %s' % (hist.date or '')
        desc = '\n%s'%(hist.description)
        original = [header, sender, to, sentdate, desc]
        original = '\n'.join(original)
        return original

    def on_change_email(self, cr, uid, ids, user):
        """This function fills email information based on user selected
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Mail’s IDs
        @param user: Changed User id
        @param partner: Changed Partner id  
        """
        if not user:
            return {'value': {'email_to': False}}
        email = self.pool.get('res.users')._get_email_from(cr, uid, [user])[user]
        return {'value': {'email_to': email}}

    def on_change_history(self, cr, uid, ids, history_type, context=None):
        """Gives message body according to type of history selected
            * info: Forward the case information
            * whole: Send the whole history
            * latest: Send the latest histoy
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of history IDs
        @param context: A standard dictionary for contextual values
        """
        #TODO: ids and context are not comming
        res = False
        res_id = context.get('active_id')
        msg_val = self._get_case_history(cr, uid, history_type, res_id, context=context)
        if msg_val:
            res = {'value': {'message' : '\n\n' + msg_val}}
        return res

    def _get_case_history(self, cr, uid, history_type, res_id, context=None):
        if not res_id:
            return

        msg_val = ''
        model_pool = self.pool.get('crm.lead')
        if history_type == 'info':
            msg_val = self.get_lead_details(cr, uid, res_id, context=context)

        elif history_type == 'whole':
            log_ids = model_pool.browse(cr, uid, res_id, context=context).message_ids
            log_ids = [x.id for x in log_ids]
            if not log_ids:
                raise osv.except_osv('Warning!', 'There is no history to send')
            msg_val = self.get_whole_history(cr, uid, log_ids, context=context)

        elif history_type == 'latest':
            log_ids = model_pool.browse(cr, uid, res_id, context=context).message_ids
            if not log_ids:
                raise osv.except_osv('Warning!', 'There is no history to send')
            msg_val = self.get_latest_history(cr, uid, log_ids[0].id, context=context)

        return msg_val

    def on_change_partner(self, cr, uid, ids, partner_id):
        """This function fills address information based on partner/user selected
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Mail’s IDs
        @param user: Changed User id
        @param partner: Changed Partner id  
        """
        if not partner_id:
            return {'value' : {'email_to' : False, 'address_id': False}}

        addr = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['contact'])
        data = {'address_id': addr['contact']}
        data.update(self.on_change_address(cr, uid, ids, addr['contact'])['value'])
        return {
            'value' : data, 
            'domain' : {'address_id' : partner_id and "[('partner_id', '=', partner_id)]" or "[]"}
            }

    def on_change_address(self, cr, uid, ids, address_id):
        email = ''
        if address_id:
            email = self.pool.get('res.partner.address').browse(cr, uid, address_id).email
        return {'value': {'email_to' : email}}

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type' : 'ir.actions.act_window_close'}

    def action_forward(self, cr, uid, ids, context=None):
        """
        Forward the lead to a partner
        """
        if context is None:
            context = {}

        res_id = context.get('active_id', False)

        model = context.get('active_model', False)
        if not res_id or not model:
            return {}

        this = self.browse(cr, uid, ids[0], context=context)

        case_pool = self.pool.get(model)
        case = case_pool.browse(cr, uid, res_id, context=context)

        emails = [this.email_to]
        body = case_pool.format_body(this.message)
        email_from = this.email_from or False

        # extract attachements from case and emails according to mode
        attachments = []
        attach_pool = self.pool.get('ir.attachment')
        direct_attachments = attach_pool.search(cr, uid, [('res_model', '=', 'crm.lead'), ('res_id', '=', res_id)], context=context)
        attachments += attach_pool.browse(cr, uid, direct_attachments, context=context)
        if this.history in ['latest', 'whole'] and case.message_ids:
            msgs = case.message_ids
            if this.history == 'latest':
                msgs = msgs[:1]
            attachments.extend(itertools.chain(*[m.attachment_ids for m in msgs]))
        attach = [(a.datas_fname or a.name, base64.decodestring(a.datas)) for a in attachments if a.datas]

        result = tools.email_send(
            email_from,
            emails,
            this.subject,
            body,
            openobject_id=str(case.id),
            attach=attach,
            reply_to=case.section_id.reply_to,
        )

        if result:
            case_pool._history(cr, uid, [case], _('Forward'), history=True, email=this.email_to, subject=this.subject, details=body, email_from=email_from, attach=attach)
        else:
            raise osv.except_osv(_('Error!'), _('Unable to send mail. Please check SMTP is configured properly.'))

        if this.add_cc and (not case.email_cc or not this.email_to in case.email_cc):
            case_pool.write(cr, uid, case.id, {'email_cc' : case.email_cc and case.email_cc + ', ' + this.email_to or this.email_to})

        return {}

    def get_lead_details(self, cr, uid, lead_id, context=None):
        message = []
        lead_proxy = self.pool.get('crm.lead')
        lead = lead_proxy.browse(cr, uid, lead_id, context=context)
        if not lead.type or lead.type == 'lead':
                field_names = [
                    'partner_name', 'title', 'function', 'street', 'street2', 
                    'zip', 'city', 'country_id', 'state_id', 'email_from', 
                    'phone', 'fax', 'mobile'
                ]

                for field_name in field_names:
                    field_definition = lead_proxy._columns[field_name]
                    value = None

                    if field_definition._type == 'selection':
                        if hasattr(field_definition.selection, '__call__'):
                            key = field_definition.selection(lead_proxy, cr, uid, context=context)
                        else:
                            key = field.definition.selection
                        value = dict(key).get(lead[field_name], lead[field_name])
                    elif field_definition._type == 'many2one':
                        if lead[field_name]:
                            value = lead[field_name].name_get()[0][1]
                    else:
                        value = lead[field_name]

                    message.append("%s: %s" % (field_definition.string, value or ''))
        elif lead.type == 'opportunity':
            pa = lead.partner_address_id
            message = [
            "Partner: %s" % (lead.partner_id.name_get()[0][1]), 
            "Contact: %s" % (pa.name or ''), 
            "Title: %s" % (pa.title or ''), 
            "Function: %s" % (pa.function and pa.function.name_get()[0][1] or ''), 
            "Street: %s" % (pa.street or ''), 
            "Street2: %s" % (pa.street2 or ''), 
            "Zip: %s" % (pa.zip or ''), 
            "City: %s" % (pa.city or ''), 
            "Country: %s" % (pa.country_id and pa.country_id.name_get()[0][1] or ''), 
            "State: %s" % (pa.state_id and pa.state_id.name_get()[0][1] or ''), 
            "Email: %s" % (pa.email or ''), 
            "Phone: %s" % (pa.phone or ''), 
            "Fax: %s" % (pa.fax or ''), 
            "Mobile: %s" % (pa.mobile or ''), 
            ]
        return "\n".join(message + ['---'])

    def default_get(self, cr, uid, fields, context=None):
        """
        This function gets default values
        """
        if context is None:
            context = {}

        defaults = super(crm_lead_forward_to_partner, self).default_get(cr, uid, fields, context=context)

        active_id = context.get('active_id')
        if not active_id:
            return defaults

        lead_proxy = self.pool.get('crm.lead')
        lead = lead_proxy.browse(cr, uid, active_id, context=context)

        message = self._get_case_history(cr, uid, defaults.get('history', 'latest'), lead.id, context=context)
        defaults.update({
            'subject' : '%s: %s' % (_('Fwd'), lead.name),
            'message' : message,
        })
        return defaults

crm_lead_forward_to_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
