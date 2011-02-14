# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2011 Tiny SPRL (<http://tiny.be>)
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

from osv import osv
from osv import fields
from tools.translate import _
import tools

#import time
#import binascii
#import email
#from email.header import decode_header
#from email.utils import parsedate
#import base64
#import re
#import logging
#import xmlrpclib

#_logger = logging.getLogger('mailgate')

#import re
import smtplib
#import base64
#from email import Encoders
#from email.mime.base import MIMEBase
#from email.mime.multipart import MIMEMultipart
#from email.mime.text import MIMEText
#from email.header import decode_header, Header
#from email.utils import formatdate
#import netsvc
#import datetime
#import tools
#import logging

#EMAIL_PATTERN = re.compile(r'([^()\[\] ,<:\\>@";]+@[^()\[\] ,<:\\>@";]+)') # See RFC822
#def extract_emails(emails_str):
#    """
#    Returns a list of email addresses recognized in a string, ignoring the rest of the string.
#    extract_emails('a@b.com,c@bcom, "John Doe" <d@b.com> , e@b.com') -> ['a@b.com','c@bcom', 'd@b.com', 'e@b.com']"
#    """
#    return EMAIL_PATTERN.findall(emails_str)
#
#
#def extract_emails_from_dict(addresses={}):
#    """
#    Extracts email addresses from a dictionary with comma-separated address string values, handling
#    separately the To, CC, BCC and Reply-To addresses.
#
#    :param addresses: a dictionary of addresses in the form {'To': 'a@b.com,c@bcom; d@b.com;e@b.com' , 'CC': 'e@b.com;f@b.com', ... }
#    :return: a dictionary with a list of separate addresses for each header (To, CC, BCC), with an additional key 'all-recipients'
#             containing all addresses for the 'To', 'CC', 'BCC' entries.
#    """
#    result = {'all-recipients':[]}
#    keys = ['To', 'CC', 'BCC', 'Reply-To']
#    for each in keys:
#        emails = extract_emails(addresses.get(each, u''))
#        while u'' in emails:
#            emails.remove(u'')
#        result[each] = emails
#        if each != 'Reply-To':
#            result['all-recipients'].extend(emails)
#    return result

class email_smtp_server(osv.osv):
    """
    SMTP Server
    """
    _name = "email.smtp_server"

    _columns = {
        'name': fields.char('Name',
                        size=64, required=True,
                        select=True,
                        help="The Name is used as the Sender name along with the provided From Email, \
unless it is already specified in the From Email, e.g: John Doe <john@doe.com>",
                        ),
        'email_id': fields.char('From Email',
                        size=120, required=True,
                        help="eg: 'john@doe.com' or 'John Doe <john@doe.com>'"),
        'smtpserver': fields.char('Server',
                        size=120, required=True,
                        help="Enter name of outgoing server, eg: smtp.yourdomain.com"),
        'smtpport': fields.integer('SMTP Port',
                        size=64, required=True,
                        help="Enter port number, eg: 25 or 587"),
        'smtpuname': fields.char('User Name',
                        size=120, required=False,
                        help="Specify the username if your SMTP server requires authentication, "
                        "otherwise leave it empty."),
        'smtppass': fields.char('Password',
                        size=120, 
                        required=False),
        'smtptls':fields.boolean('TLS'),
        'smtpssl':fields.boolean('SSL/TLS (only in python 2.6)'),
        'default': fields.boolean('Default', help="Only one account can be default at a time"),
    }

    _defaults = {
         'name':lambda self, cursor, user, context:self.pool.get( 'res.users'
                                                ).read(cursor, user, user, ['name'], context)['name'],
         'smtpport': tools.config.get('smtp_port',25),
         'smtpserver': tools.config.get('smtp_server','localhost'),
         'smtpssl': tools.config.get('smtp_ssl',False),
         'smtptls': True,
     }

    _sql_constraints = [
        (
         'email_uniq',
         'unique (email_id)',
         'Another setting already exists with this email ID !')
    ]

    def _constraint_unique(self, cr, uid, ids, context=None):
        default_ids = self.search(cr, uid, [('default','=',True)])
        if len(default_ids) > 1:
            return False
        elif not default_ids:
            return False
        else:
            return True

    _constraints = [
        (_constraint_unique,
         'Error: You must be define one default smtp server account !.',
         [])
    ]

    def name_get(self, cr, uid, ids, context=None):
        return [(a["id"], "%s (%s)" % (a['email_id'], a['name'])) for a in self.read(cr, uid, ids, ['name', 'email_id'], context=context)]

    def get_outgoing_server(self, cursor, user, id, context=None):
        """
        Returns the Out Going Connection (SMTP) object

        @attention: DO NOT USE except_osv IN THIS METHOD
        @param cursor: Database Cursor
        @param user: ID of current user
        @param ids: ID/list of ids of current object for
                    which connection is required
                    First ID will be chosen from lists
        @param context: Context

        @return: SMTP server object or Exception
        """
        #Type cast ids to integer
        if type(id) == list:
            id = id[0]
        smtp_data = self.browse(cursor, user, id, context=context)
        if smtp_data:
            if smtp_data.smtpserver and smtp_data.smtpport:
                try:
                    if smtp_data.smtpssl:
                        serv = smtplib.SMTP_SSL(smtp_data.smtpserver, smtp_data.smtpport)
                    else:
                        serv = smtplib.SMTP(smtp_data.smtpserver, smtp_data.smtpport)
                    if smtp_data.smtptls:
                        serv.ehlo()
                        serv.starttls()
                        serv.ehlo()
                except Exception, error:
                    raise error
                try:
                    if serv.has_extn('AUTH') or smtp_data.smtpuname or smtp_data.smtppass:
                        serv.login(str(smtp_data.smtpuname), str(smtp_data.smtppass))
                except Exception, error:
                    raise error
                return serv
            raise Exception(_("SMTP SERVER or PORT not specified"))
        raise Exception(_("Core connection for the given ID does not exist"))

    def check_outgoing_connection(self, cursor, user, ids, context=None):
        """
        checks SMTP credentials and confirms if outgoing connection works
        (Attached to button)
        @param cursor: Database Cursor
        @param user: ID of current user
        @param ids: list of ids of current object for
                    which connection is required
        @param context: Context
        """
        try:
            for id in ids:
                self.get_outgoing_server(cursor, user, id, context)
            raise osv.except_osv(_("SMTP Test Connection Was Successful"), '')
        except osv.except_osv, success_message:
            raise success_message
        except Exception, error:
            raise osv.except_osv(
                                 _("Out going connection test failed"),
                                 _("Reason: %s") % error
                                 )

#    def do_approval(self, cr, uid, ids, context=None):
#        #TODO: Check if user has rights
#        self.write(cr, uid, ids, {'state':'approved'}, context=context)
##        wf_service = netsvc.LocalService("workflow")
#
#    def smtp_connection(self, cursor, user, id, context=None):
#        """
#        This method should now wrap smtp_connection
#        """
#        #This function returns a SMTP server object
#        logger = netsvc.Logger()
#        core_obj = self.browse(cursor, user, id, context=context)
#        if core_obj.smtpserver and core_obj.smtpport and core_obj.state == 'approved':
#            try:
#                serv = self.get_outgoing_server(cursor, user, id, context)
#            except Exception, error:
#                logger.notifyChannel(_("Email Template"), netsvc.LOG_ERROR, _("Mail from Account %s failed on login. Probable Reason:Could not login to server\nError: %s") % (id, error))
#                return False
#            #Everything is complete, now return the connection
#            return serv
#        else:
#            logger.notifyChannel(_("Email Template"), netsvc.LOG_ERROR, _("Mail from Account %s failed. Probable Reason:Account not approved") % id)
#            return False
#
##**************************** MAIL SENDING FEATURES ***********************#
#    def send_email(self, cr, uid, ids, addresses, subject='', body=None, payload=None, message_id=None, context=None):
#        #TODO: Replace all this with a single email object
#        if body is None:
#            body = {}
#        if payload is None:
#            payload = {}
#        if context is None:
#            context = {}
#        logger = netsvc.Logger()
#        for id in ids:
#            core_obj = self.browse(cr, uid, id, context)
#            serv = self.smtp_connection(cr, uid, id)
#            if serv:
#                try:
#                    # Need a multipart/mixed wrapper for attachments if content is alternative
#                    if payload:
#                        payload_part = MIMEMultipart(_subtype='mixed')
#                        text_part = MIMEMultipart(_subtype='mixed')
#                        payload_part.attach(text_part)
#                    else:
#                        # otherwise a single multipart/mixed will do the whole job
#                        payload_part = text_part = MIMEMultipart(_subtype='mixed')
#
#                    if subject:
#                        payload_part['Subject'] = subject
#                    from_email = core_obj.email_id
#                    if '<' in from_email:
#                        # We have a structured email address, keep it untouched
#                        payload_part['From'] = Header(core_obj.email_id, 'utf-8').encode()
#                    else:
#                        # Plain email address, construct a structured one based on the name:
#                        sender_name = Header(core_obj.name, 'utf-8').encode()
#                        payload_part['From'] = sender_name + " <" + core_obj.email_id + ">"
#                    payload_part['Organization'] = tools.ustr(core_obj.user.company_id.name)
#                    payload_part['Date'] = formatdate()
#                    addresses_l = extract_emails_from_dict(addresses)
#                    if addresses_l['To']:
#                        payload_part['To'] = u','.join(addresses_l['To'])
#                    if addresses_l['CC']:
#                        payload_part['CC'] = u','.join(addresses_l['CC'])
#                    if addresses_l['Reply-To']:
#                        payload_part['Reply-To'] = addresses_l['Reply-To'][0]
#                    if message_id:
#                        payload_part['Message-ID'] = message_id
#                    if body.get('text', False):
#                        temp_body_text = body.get('text', '')
#                        l = len(temp_body_text.replace(' ', '').replace('\r', '').replace('\n', ''))
#                        if l == 0:
#                            body['text'] = u'No Mail Message'
#                    # Attach parts into message container.
#                    # According to RFC 2046, the last part of a multipart message, in this case
#                    # the HTML message, is best and preferred.
##                    if core_obj.send_pref in ('text', 'mixed', 'alternative'):
##                        body_text = body.get('text', u'<Empty Message>')
##                        body_text = tools.ustr(body_text)
##                        text_part.attach(MIMEText(body_text.encode("utf-8"), _charset='UTF-8'))
##                    if core_obj.send_pref in ('html', 'mixed', 'alternative'):
#                    html_body = body.get('html', u'')
#                    if len(html_body) == 0 or html_body == u'':
#                        html_body = body.get('text', u'<p>&lt;Empty Message&gt;</p>').replace('\n', '<br/>').replace('\r', '<br/>')
#                    html_body = tools.ustr(html_body)
#                    text_part.attach(MIMEText(html_body.encode("utf-8"), _subtype='html', _charset='UTF-8'))
#
#                    #Now add attachments if any, wrapping into a container multipart/mixed if needed
#                    if payload:
#                        for file in payload:
#                            part = MIMEBase('application', "octet-stream")
#                            part.set_payload(base64.decodestring(payload[file]))
#                            part.add_header('Content-Disposition', 'attachment; filename="%s"' % file)
#                            Encoders.encode_base64(part)
#                            payload_part.attach(part)
#                except Exception, error:
#                    logger.notifyChannel(_("Email Template"), netsvc.LOG_ERROR, _("Mail from Account %s failed. Probable Reason:MIME Error\nDescription: %s") % (id, error))
#                    return {'error_msg': _("Server Send Error\nDescription: %s")%error}
#                try:
#                    serv.sendmail(payload_part['From'], addresses_l['all-recipients'], payload_part.as_string())
#                except Exception, error:
#                    logging.getLogger('email_template').error(_("Mail from Account %s failed. Probable Reason: Server Send Error\n Description: %s"), id, error, exc_info=True)
#                    return {'error_msg': _("Server Send Error\nDescription: %s")%error}
#                #The mail sending is complete
#                serv.close()
#                logger.notifyChannel(_("Email Template"), netsvc.LOG_INFO, _("Mail from Account %s successfully Sent.") % (id))
#                return True
#            else:
#                logger.notifyChannel(_("Email Template"), netsvc.LOG_ERROR, _("Mail from Account %s failed. Probable Reason:Account not approved") % id)
#                return {'nodestroy':True,'error_msg': _("Mail from Account %s failed. Probable Reason:Account not approved")% id}
#
#    def extracttime(self, time_as_string):
#        """
#        TODO: DOC THis
#        """
#        logger = netsvc.Logger()
#        #The standard email dates are of format similar to:
#        #Thu, 8 Oct 2009 09:35:42 +0200
#        date_as_date = False
#        convertor = {'+':1, '-':-1}
#        try:
#            time_as_string = time_as_string.replace(',', '')
#            date_list = time_as_string.split(' ')
#            date_temp_str = ' '.join(date_list[1:5])
#            if len(date_list) >= 6:
#                sign = convertor.get(date_list[5][0], False)
#            else:
#                sign = False
#            try:
#                dt = datetime.datetime.strptime(
#                                            date_temp_str,
#                                            "%d %b %Y %H:%M:%S")
#            except:
#                try:
#                    dt = datetime.datetime.strptime(
#                                            date_temp_str,
#                                            "%d %b %Y %H:%M")
#                except:
#                    return False
#            if sign:
#                try:
#                    offset = datetime.timedelta(
#                                hours=sign * int(
#                                             date_list[5][1:3]
#                                                ),
#                                             minutes=sign * int(
#                                                            date_list[5][3:5]
#                                                                )
#                                                )
#                except Exception, e2:
#                    """Looks like UT or GMT, just forget decoding"""
#                    return False
#            else:
#                offset = datetime.timedelta(hours=0)
#            dt = dt + offset
#            date_as_date = dt.strftime('%Y-%m-%d %H:%M:%S')
#        except Exception, e:
#            logger.notifyChannel(
#                    _("Email Template"),
#                    netsvc.LOG_WARNING,
#                    _(
#                      "Datetime Extraction failed.Date:%s \
#                      \tError:%s") % (
#                                    time_as_string,
#                                    e)
#                      )
#        return date_as_date
#
#    def send_receive(self, cr, uid, ids, context=None):
#        for id in ids:
#            ctx = context.copy()
#            ctx['filters'] = [('account_id', '=', id)]
#            self.pool.get('email.message').send_all_mail(cr, uid, [], context=ctx)
#        return True
#
#    def decode_header_text(self, text):
#        """ Decode internationalized headers RFC2822.
#            To, CC, BCC, Subject fields can contain
#            text slices with different encodes, like:
#                =?iso-8859-1?Q?Enric_Mart=ED?= <enricmarti@company.com>,
#                =?Windows-1252?Q?David_G=F3mez?= <david@company.com>
#            Sometimes they include extra " character at the beginning/
#            end of the contact name, like:
#                "=?iso-8859-1?Q?Enric_Mart=ED?=" <enricmarti@company.com>
#            and decode_header() does not work well, so we use regular
#            expressions (?=   ? ?   ?=) to split the text slices
#        """
#        if not text:
#            return text
#        p = re.compile("(=\?.*?\?.\?.*?\?=)")
#        text2 = ''
#        try:
#            for t2 in p.split(text):
#                text2 += ''.join(
#                            [s.decode(
#                                      t or 'ascii'
#                                    ) for (s, t) in decode_header(t2)]
#                                ).encode('utf-8')
#        except:
#            return text
#        return text2

email_smtp_server()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
