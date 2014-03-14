# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from datetime import datetime
from dateutil import relativedelta

from openerp import tools
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools.translate import _
from openerp.osv import osv, fields


class MassMailingCategory(osv.Model):
    """Model of categories of mass mailing, i.e. marketing, newsletter, ... """
    _name = 'mail.mass_mailing.category'
    _description = 'Mass Mailing Category'

    _columns = {
        'name': fields.char('Name', required=True),
    }


class MassMailingContact(osv.Model):
    """Model of a contact. This model is different from the partner model
    because it holds only some basic information: name, email. The purpose is to
    be able to deal with large contact list to email without bloating the partner
    database. """
    _name = 'mail.mass_mailing.contact'
    _description = 'Mass Mailing Contact'

    _columns = {
        'name': fields.char('Name', required=True),
        'email': fields.char('Email', required=True),
        'list_id': fields.many2one(
            'mail.mass_mailing.list', string='Mailing List',
            required=True, ondelete='cascade',
        ),
        'opt_out': fields.boolean('Opt Out', help='The contact has chosen not to receive news anymore from this mailing list'),
    }


class MassMailingList(osv.Model):
    """Model of a contact list. """
    _name = 'mail.mass_mailing.list'
    _description = 'Contact List'

    def default_get(self, cr, uid, fields, context=None):
        """Override default_get to handle active_domain coming from the list view. """
        res = super(MassMailingList, self).default_get(cr, uid, fields, context=context)
        if 'domain' in fields and 'active_domain' in context:
            res['domain'] = '%s' % context['active_domain']
            res['model'] = context.get('active_model', 'res.partner')
        return res

    def _get_contact_nbr(self, cr, uid, ids, name, arg, context=None):
        """Compute the number of contacts linked to the mailing list. """
        results = dict.fromkeys(ids, 0)
        for contact_list in self.browse(cr, uid, ids, context=context):
            if contact_list.model == 'mail.mass_mailing.contact':
                results[contact_list.id] = len(contact_list.contact_ids)
            else:
                domain = self.compute_domain(cr, uid, [contact_list.id], context=context)
                results[contact_list.id] = self.pool[contact_list.model].search(cr, uid, domain, count=True, context=context)
        return results

    def _get_model_list(self, cr, uid, context=None):
        return [
            ('res.partner', 'Customers'),
            ('mail.mass_mailing.contact', 'Mailing Contacts')
        ]

    # indirections for inheritance
    _model_list = lambda self, *args, **kwargs: self._get_model_list(*args, **kwargs)

    _columns = {
        'name': fields.char('Name', required=True),
        'contact_nbr': fields.function(
            _get_contact_nbr, type='integer',
            string='Contact Number',
        ),
        # contact-based list
        'contact_ids': fields.one2many(
            'mail.mass_mailing.contact', 'list_id', string='Contacts',
            domain=[('opt_out', '=', False)],
        ),
        # filter-based list
        'model': fields.selection(
            _model_list, type='char', required=True,
            string='Applies To'
        ),
        # 'model_id': fields.many2one(
        #     'ir.model', string='Related Model',
        #     domain="[('model', '=', model')]",
        # ),
        'filter_id': fields.many2one(
            'ir.filters', string='Custom Filter',
            # domain="[('model_id', '=', model_id)]",
        ),
        'domain': fields.text('Domain'),
    }

    def on_change_model(self, cr, uid, ids, model, context=None):
        values = {}
        if model == 'mail.mass_mailing.contact':
            values.update(domain=False, filter_id=False)
        else:
            values.update(filter_id=False)
        return {'value': values}

    def on_change_filter_id(self, cr, uid, ids, filter_id, context=None):
        values = {}
        if filter_id:
            ir_filter = self.pool['ir.filters'].browse(cr, uid, filter_id, context=context)
            values['domain'] = ir_filter.domain
        else:
            values['domain'] = False
        return {'value': values}

    def action_see_records(self, cr, uid, ids, context=None):
        contact_list = self.browse(cr, uid, ids[0], context=context)
        ctx = dict(context)
        ctx['search_default_not_opt_out'] = True
        return {
            'name': _('See Contact List'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': contact_list.model,
            'views': [(False, 'tree'), (False, 'form')],
            'view_id': False,
            'target': 'current',
            'context': ctx,
            'domain': contact_list.domain,
        }

    def compute_domain(self, cr, uid, ids, context=None):
        domains = []
        for contact_list in self.browse(cr, uid, ids, context=context):
            domain = eval(contact_list.domain)
            if domain:
                domain = ['&', ('opt_out', '=', False)] + domain
            else:
                domain = [('opt_out', '=', False)]
            if domain is not False:
                domains.append(domain)
        if domains:
            final_domain = ['|'] * (len(domains) - 1) + [leaf for dom in domains for leaf in dom]
        else:
            final_domain = domains
        return final_domain


class MassMailingCampaign(osv.Model):
    """Model of mass mailing campaigns.
    """
    _name = "mail.mass_mailing.campaign"
    _description = 'Mass Mailing Campaign'
    # number of embedded mailings in kanban view
    _kanban_mailing_nbr = 4

    def _get_statistics(self, cr, uid, ids, name, arg, context=None):
        """ Compute statistics of the mass mailing campaign """
        results = dict.fromkeys(ids, False)
        for campaign in self.browse(cr, uid, ids, context=context):
            results[campaign.id] = {
                'sent': len(campaign.statistics_ids),
                # delivered: shouldn't be: all mails - (failed + bounced) ?
                'delivered': len([stat for stat in campaign.statistics_ids if not stat.bounced]),  # stat.state == 'sent' and
                'opened': len([stat for stat in campaign.statistics_ids if stat.opened]),
                'replied': len([stat for stat in campaign.statistics_ids if stat.replied]),
                'bounced': len([stat for stat in campaign.statistics_ids if stat.bounced]),
            }
        return results

    def _get_mass_mailing_kanban_ids(self, cr, uid, ids, name, arg, context=None):
        """ Gather data about mass mailings to display them in kanban view as
        nested kanban views is not possible currently. """
        results = dict.fromkeys(ids, '')
        for campaign in self.browse(cr, uid, ids, context=context):
            mass_mailing_results = []
            for mass_mailing in campaign.mass_mailing_ids[:self._kanban_mailing_nbr]:
                mass_mailing_object = {}
                for attr in ['name', 'sent', 'delivered', 'opened', 'replied', 'bounced']:
                    mass_mailing_object[attr] = getattr(mass_mailing, attr)
                mass_mailing_results.append(mass_mailing_object)
            results[campaign.id] = mass_mailing_results
        return results

    def _get_state_list(self, cr, uid, context=None):
        return [('draft', 'Schedule'), ('design', 'Design'), ('done', 'Sent')]

    # indirections for inheritance
    _state = lambda self, *args, **kwargs: self._get_state_list(*args, **kwargs)

    _columns = {
        'name': fields.char(
            'Campaign Name', required=True,
        ),
        'user_id': fields.many2one(
            'res.users', 'Responsible',
            required=True,
        ),
        'state': fields.selection(
            _state, string='Status', required=True,
        ),
        'category_id': fields.many2one(
            'mail.mass_mailing.category', 'Category',
            help='Category'),
        'mass_mailing_ids': fields.one2many(
            'mail.mass_mailing', 'mass_mailing_campaign_id',
            'Mass Mailings',
        ),
        'mass_mailing_kanban_ids': fields.function(
            _get_mass_mailing_kanban_ids,
            type='text', string='Mass Mailings (kanban data)',
            help='This field has for purpose to gather data about mass mailings '
                 'to display them in kanban view as nested kanban views is not '
                 'possible currently',
        ),
        'statistics_ids': fields.one2many(
            'mail.mail.statistics', 'mass_mailing_campaign_id',
            'Sent Emails',
        ),
        'color': fields.integer('Color Index'),
        # stat fields
        'sent': fields.function(
            _get_statistics,
            string='Sent Emails',
            type='integer', multi='_get_statistics'
        ),
        'delivered': fields.function(
            _get_statistics,
            string='Delivered',
            type='integer', multi='_get_statistics',
        ),
        'opened': fields.function(
            _get_statistics,
            string='Opened',
            type='integer', multi='_get_statistics',
        ),
        'replied': fields.function(
            _get_statistics,
            string='Replied',
            type='integer', multi='_get_statistics'
        ),
        'bounced': fields.function(
            _get_statistics,
            string='Bounced',
            type='integer', multi='_get_statistics'
        ),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, ctx=None: uid,
        'state': 'draft',
    }

    #------------------------------------------------------
    # Technical stuff
    #------------------------------------------------------

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        """ Override read_group to always display all states. """
        if groupby and groupby[0] == "state":
            # Default result structure
            states = self._get_state_list(cr, uid, context=context)
            read_group_all_states = [{
                '__context': {'group_by': groupby[1:]},
                '__domain': domain + [('state', '=', state_value)],
                'state': state_value,
                'state_count': 0,
            } for state_value, state_name in states]
            # Get standard results
            read_group_res = super(MassMailingCampaign, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby)
            # Update standard results with default results
            result = []
            for state_value, state_name in states:
                res = filter(lambda x: x['state'] == state_value, read_group_res)
                if not res:
                    res = filter(lambda x: x['state'] == state_value, read_group_all_states)
                res[0]['state'] = [state_value, state_name]
                result.append(res[0])
            return result
        else:
            return super(MassMailingCampaign, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby)

    #------------------------------------------------------
    # Actions
    #------------------------------------------------------

    def launch_mass_mailing_create_wizard(self, cr, uid, ids, context=None):
        ctx = dict(context)
        ctx.update({
            'default_mass_mailing_campaign_id': ids[0],
        })
        return {
            'name': _('Create a Mass Mailing for the Campaign'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.mass_mailing.create',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }


class MassMailing(osv.Model):
    """ MassMailing models a wave of emails for a mass mailign campaign.
    A mass mailing is an occurence of sending emails. """

    _name = 'mail.mass_mailing'
    _description = 'Mass Mailing'
    # number of periods for tracking mail_mail statistics
    _period_number = 6
    _order = 'date DESC'

    def __get_bar_values(self, cr, uid, id, obj, domain, read_fields, value_field, groupby_field, context=None):
        """ Generic method to generate data for bar chart values using SparklineBarWidget.
            This method performs obj.read_group(cr, uid, domain, read_fields, groupby_field).

            :param obj: the target model (i.e. crm_lead)
            :param domain: the domain applied to the read_group
            :param list read_fields: the list of fields to read in the read_group
            :param str value_field: the field used to compute the value of the bar slice
            :param str groupby_field: the fields used to group

            :return list section_result: a list of dicts: [
                                                {   'value': (int) bar_column_value,
                                                    'tootip': (str) bar_column_tooltip,
                                                }
                                            ]
        """
        date_begin = datetime.strptime(self.browse(cr, uid, id, context=context).date, tools.DEFAULT_SERVER_DATETIME_FORMAT).date()
        section_result = [{'value': 0,
                           'tooltip': (date_begin + relativedelta.relativedelta(days=i)).strftime('%d %B %Y'),
                           } for i in range(0, self._period_number)]
        group_obj = obj.read_group(cr, uid, domain, read_fields, groupby_field, context=context)
        field_col_info = obj._all_columns.get(groupby_field.split(':')[0])
        pattern = tools.DEFAULT_SERVER_DATE_FORMAT if field_col_info.column._type == 'date' else tools.DEFAULT_SERVER_DATETIME_FORMAT
        for group in group_obj:
            group_begin_date = datetime.strptime(group['__domain'][0][2], pattern).date()
            timedelta = relativedelta.relativedelta(group_begin_date, date_begin)
            section_result[timedelta.days] = {'value': group.get(value_field, 0), 'tooltip': group.get(groupby_field)}
        return section_result

    def _get_daily_statistics(self, cr, uid, ids, field_name, arg, context=None):
        """ Get the daily statistics of the mass mailing. This is done by a grouping
        on opened and replied fields. Using custom format in context, we obtain
        results for the next 6 days following the mass mailing date. """
        obj = self.pool['mail.mail.statistics']
        res = {}
        for id in ids:
            res[id] = {}
            date_begin = datetime.strptime(self.browse(cr, uid, id, context=context).date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
            date_end = date_begin + relativedelta.relativedelta(days=self._period_number - 1)
            date_begin_str = date_begin.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
            date_end_str = date_end.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
            domain = [('mass_mailing_id', '=', id), ('opened', '>=', date_begin_str), ('opened', '<=', date_end_str)]
            res[id]['opened_dayly'] = self.__get_bar_values(cr, uid, id, obj, domain, ['opened'], 'opened_count', 'opened:day', context=context)
            domain = [('mass_mailing_id', '=', id), ('replied', '>=', date_begin_str), ('replied', '<=', date_end_str)]
            res[id]['replied_dayly'] = self.__get_bar_values(cr, uid, id, obj, domain, ['replied'], 'replied_count', 'replied:day', context=context)
        return res

    def _get_statistics(self, cr, uid, ids, name, arg, context=None):
        """ Compute statistics of the mass mailing campaign """
        results = dict.fromkeys(ids, False)
        for mass_mailing in self.browse(cr, uid, ids, context=context):
            results[mass_mailing.id] = {
                'sent': len(mass_mailing.statistics_ids),
                'delivered': len([stat for stat in mass_mailing.statistics_ids if not stat.bounced]),  # mail.state == 'sent' and
                'opened': len([stat for stat in mass_mailing.statistics_ids if stat.opened]),
                'replied': len([stat for stat in mass_mailing.statistics_ids if stat.replied]),
                'bounced': len([stat for stat in mass_mailing.statistics_ids if stat.bounced]),
            }
        return results

    def _get_mailing_type(self, cr, uid, context=None):
        return [
            ('res.partner', 'Customers'),
            ('mail.mass_mailing.contact', 'Contacts')
        ]

    def _get_state_list(self, cr, uid, context=None):
        return [('draft', 'Schedule'), ('test', 'Tested'), ('done', 'Sent')]

    # indirections for inheritance
    _mailing_type = lambda self, *args, **kwargs: self._get_mailing_type(*args, **kwargs)
    _state = lambda self, *args, **kwargs: self._get_state_list(*args, **kwargs)

    _columns = {
        'name': fields.char('Subject', required=True),
        'date': fields.datetime('Date'),
        'state': fields.selection(
            _state, string='Status', required=True,
        ),
        'template_id': fields.many2one(
            'email.template', 'Email Template',
            domain=[('use_in_mass_mailing', '=', True)],
            ondelete='set null',
        ),
        'body_html': fields.related(
            'template_id', 'body_html', type='html',
            string='Body', readonly='True',
            help='Technical field: used only to display a view of the template in the form view',
        ),
        'mass_mailing_campaign_id': fields.many2one(
            'mail.mass_mailing.campaign', 'Mass Mailing Campaign',
            ondelete='set null',
        ),
        'color': fields.related(
            'mass_mailing_campaign_id', 'color',
            type='integer', string='Color Index',
        ),
        # mailing options
        'email_from': fields.char('From'),
        'email_to': fields.char('Send to Emails'),
        'reply_to': fields.char('Reply To'),
        'mailing_type': fields.selection(_mailing_type, string='Type', required=True),
        'contact_list_ids': fields.many2many(
            'mail.mass_mailing.list', 'mail_mass_mailing_list_rel',
            string='Mailing Lists',
            domain="[('model', '=', mailing_type)]",
        ),
        'contact_nbr': fields.integer('Contact Number'),
        # statistics data
        'statistics_ids': fields.one2many(
            'mail.mail.statistics', 'mass_mailing_id',
            'Emails Statistics',
        ),
        'sent': fields.function(
            _get_statistics,
            string='Sent Emails',
            type='integer', multi='_get_statistics'
        ),
        'delivered': fields.function(
            _get_statistics,
            string='Delivered',
            type='integer', multi='_get_statistics',
        ),
        'opened': fields.function(
            _get_statistics,
            string='Opened',
            type='integer', multi='_get_statistics',
        ),
        'replied': fields.function(
            _get_statistics,
            string='Replied',
            type='integer', multi='_get_statistics'
        ),
        'bounced': fields.function(
            _get_statistics,
            string='Bounce',
            type='integer', multi='_get_statistics'
        ),
        # monthly ratio
        'opened_dayly': fields.function(
            _get_daily_statistics,
            string='Opened',
            type='char', multi='_get_daily_statistics',
            oldname='opened_monthly',
        ),
        'replied_dayly': fields.function(
            _get_daily_statistics,
            string='Replied',
            type='char', multi='_get_daily_statistics',
            oldname='replied_monthly',
        ),
    }

    _defaults = {
        'state': 'draft',
        'date': fields.datetime.now,
        'email_from': lambda self, cr, uid, ctx=None: self.pool['mail.message']._get_default_from(cr, uid, context=ctx),
        'mailing_type': 'res.partner',
    }

    #------------------------------------------------------
    # Technical stuff
    #------------------------------------------------------

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        """ Override read_group to always display all states. """
        if groupby and groupby[0] == "state":
            # Default result structure
            states = self._get_state_list(cr, uid, context=context)
            read_group_all_states = [{
                '__context': {'group_by': groupby[1:]},
                '__domain': domain + [('state', '=', state_value)],
                'state': state_value,
                'state_count': 0,
            } for state_value, state_name in states]
            # Get standard results
            read_group_res = super(MassMailing, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby)
            # Update standard results with default results
            result = []
            for state_value, state_name in states:
                res = filter(lambda x: x['state'] == state_value, read_group_res)
                if not res:
                    res = filter(lambda x: x['state'] == state_value, read_group_all_states)
                res[0]['state'] = [state_value, state_name]
                result.append(res[0])
            return result
        else:
            return super(MassMailing, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby)

    #------------------------------------------------------
    # Views & Actions
    #------------------------------------------------------

    def on_change_mailing_type(self, cr, uid, ids, mailing_type, context=None):
        return {'value': {'contact_list_ids': []}}

    def on_change_template_id(self, cr, uid, ids, template_id, context=None):
        values = {}
        if template_id:
            template = self.pool['email.template'].browse(cr, uid, template_id, context=context)
            if template.email_from:
                values['email_from'] = template.email_from
            if template.reply_to:
                values['reply_to'] = template.reply_to
            values['body_html'] = template.body_html
        else:
            values['email_from'] = self.pool['mail.message']._get_default_from(cr, uid, context=context)
            values['reply_to'] = False
            values['body_html'] = False
        return {'value': values}

    def send_mail(self, cr, uid, ids, context=None):
        Mail = self.pool['mail.mail']
        for mailing in self.browse(cr, uid, ids, context=context):
            contact_list_ids = [contact_list.id for contact_list in mailing.contact_list_ids]

            # contact-based list: aggregate all contacts
            if mailing.mailing_type == 'mail.mass_mailing.list':
                res_ids = [contact.id for contact in contact_list.contact_ids for contact_list in mailing.contact_list_ids]
            elif mailing.mailing_type == 'res.partner':
                domain = self.pool['mail.mass_mailing.list'].compute_domain(cr, uid, contact_list_ids, context=context)
                print domain
                res_ids = self.pool[contact_list.model].search(cr, uid, domain, context=context)

            all_mail_values = self.pool['mail.compose.message'].generate_email_for_composer_batch(
                cr, uid, mailing.template_id.id, res_ids,
                context=context,
                fields=['body_html', 'attachment_ids', 'mail_server_id']
            )
            for res_id, mail_values in all_mail_values.iteritems():
                mail_values.update({
                    'email_from': mailing.email_from,
                    'reply_to': mailing.reply_to,
                    'subject': mailing.name,
                    'body_html': mail_values.get('body'),
                    'auto_delete': True,
                    'statistics_ids': [(0, 0, {
                        'model': mailing.mailing_type,
                        'res_id': res_id,
                        'mass_mailing_id': mailing.id,
                    })]
                })
                m2m_attachment_ids = self.pool['mail.thread']._message_preprocess_attachments(
                    cr, uid, mail_values.pop('attachments', []),
                    mail_values.pop('attachment_ids', []),
                    'mail.message', 0,
                    context=context)
                mail_values['attachment_ids'] = m2m_attachment_ids
                if mailing.mailing_type == 'mail.mass_mailing.list':
                    contact = self.pool['mail.mass_mailing.contact'].browse(cr, uid, res_id, context=context)
                    mail_values['email_to'] = '"%s" <%s>' % (contact.name, contact.email)
                elif mailing.mailing_type == 'res.partner':
                    mail_values['recipient_ids'] = [(4, res_id)]
                Mail.create(cr, uid, mail_values, context=context)
            # todo: handle email_to
        return True

    def send_mail_to_myself(self, cr, uid, ids, context=None):
        Mail = self.pool['mail.mail']
        for mailing in self.browse(cr, uid, ids, context=context):
            mail_values = {
                'email_from': mailing.email_from,
                'reply_to': mailing.reply_to,
                'email_to': self.pool['res.users'].browse(cr, uid, uid, context=context).email,
                'subject': mailing.name,
                'body_html': mailing.template_id.body_html,
                'auto_delete': True,
            }
            mail_id = Mail.create(cr, uid, mail_values, context=context)
            Mail.send(cr, uid, [mail_id], context=context)
        return True

    def select_customers(self, cr, uid, ids, context=None):
        sid = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'base.view_res_partner_filter')

        aid = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'mass_mailing.action_partner_to_mailing_list')
        print sid, aid
        ctx = dict(context)
        ctx['view_manager_highlight'] = [aid]
        return {
            'name': _('Choose Customers'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            # 'views': [(False, 'tree'), (False, 'form')],
            'view_id': False,
            'search_view_id': sid,
            # 'target': 'new',
            'context': ctx,
        }


class MailMailStats(osv.Model):
    """ MailMailStats models the statistics collected about emails. Those statistics
    are stored in a separated model and table to avoid bloating the mail_mail table
    with statistics values. This also allows to delete emails send with mass mailing
    without loosing the statistics about them. """

    _name = 'mail.mail.statistics'
    _description = 'Email Statistics'
    _rec_name = 'message_id'
    _order = 'message_id'

    _columns = {
        'mail_mail_id': fields.integer(
            'Mail ID',
            help='ID of the related mail_mail. This field is an integer field because'
                 'the related mail_mail can be deleted separately from its statistics.'
        ),
        'message_id': fields.char(
            'Message-ID',
        ),
        'model': fields.char(
            'Document model',
        ),
        'res_id': fields.integer(
            'Document ID',
        ),
        # campaign / wave data
        'mass_mailing_id': fields.many2one(
            'mail.mass_mailing', 'Mass Mailing',
            ondelete='set null',
        ),
        'mass_mailing_campaign_id': fields.related(
            'mass_mailing_id', 'mass_mailing_campaign_id',
            type='many2one', ondelete='set null',
            relation='mail.mass_mailing.campaign',
            string='Mass Mailing Campaign',
            store=True, readonly=True,
        ),
        'template_id': fields.related(
            'mass_mailing_id', 'template_id',
            type='many2one', ondelete='set null',
            relation='email.template',
            string='Email Template',
            store=True, readonly=True,
        ),
        # Bounce and tracking
        'opened': fields.datetime(
            'Opened',
            help='Date when this email has been opened for the first time.'),
        'replied': fields.datetime(
            'Replied',
            help='Date when this email has been replied for the first time.'),
        'bounced': fields.datetime(
            'Bounced',
            help='Date when this email has bounced.'
        ),
    }

    def set_opened(self, cr, uid, ids=None, mail_mail_ids=None, mail_message_ids=None, context=None):
        """ Set as opened """
        if not ids and mail_mail_ids:
            ids = self.search(cr, uid, [('mail_mail_id', 'in', mail_mail_ids)], context=context)
        elif not ids and mail_message_ids:
            ids = self.search(cr, uid, [('message_id', 'in', mail_message_ids)], context=context)
        else:
            ids = []
        for stat in self.browse(cr, uid, ids, context=context):
            if not stat.opened:
                self.write(cr, uid, [stat.id], {'opened': fields.datetime.now()}, context=context)
        return ids

    def set_replied(self, cr, uid, ids=None, mail_mail_ids=None, mail_message_ids=None, context=None):
        """ Set as replied """
        if not ids and mail_mail_ids:
            ids = self.search(cr, uid, [('mail_mail_id', 'in', mail_mail_ids)], context=context)
        elif not ids and mail_message_ids:
            ids = self.search(cr, uid, [('message_id', 'in', mail_message_ids)], context=context)
        else:
            ids = []
        for stat in self.browse(cr, uid, ids, context=context):
            if not stat.replied:
                self.write(cr, uid, [stat.id], {'replied': fields.datetime.now()}, context=context)
        return ids

    def set_bounced(self, cr, uid, ids=None, mail_mail_ids=None, mail_message_ids=None, context=None):
        """ Set as bounced """
        if not ids and mail_mail_ids:
            ids = self.search(cr, uid, [('mail_mail_id', 'in', mail_mail_ids)], context=context)
        elif not ids and mail_message_ids:
            ids = self.search(cr, uid, [('message_id', 'in', mail_message_ids)], context=context)
        else:
            ids = []
        for stat in self.browse(cr, uid, ids, context=context):
            if not stat.bounced:
                self.write(cr, uid, [stat.id], {'bounced': fields.datetime.now()}, context=context)
        return ids
