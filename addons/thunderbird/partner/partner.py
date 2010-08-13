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

import time
import ir
from osv import osv,fields
import base64
import netsvc
from tools.translate import _
import email
import tools
import binascii
class email_server_tools(osv.osv_memory):
    _inherit = "email.server.tools"
    def history_message(self, cr, uid, model, res_id, message):
        #@param message: string of mail which is read from EML File
        attachment_pool = self.pool.get('ir.attachment')
        msg = self.parse_message(message)
        attachments = msg.get('attachments', [])
        att_ids = []
        for attachment in attachments:
            data_attach = {
                'name': attachment,
                'datas': binascii.b2a_base64(str(attachments.get(attachment))),
                'datas_fname': attachment,
                'description': 'Mail attachment From Thunderbird msg_id: %s' %(msg.get('message_id', '')),
                'res_model': model,
                'res_id': res_id,
            }
            att_ids.append(attachment_pool.create(cr, uid, data_attach))
        return self.history(cr, uid, model, res_id, msg, att_ids)

    def parse_message(self, message):
        #TOCHECK: put this function in mailgateway
        msg_txt = email.message_from_string(message)
        message_id = msg_txt.get('message-id', False)
        msg = {}
        msg_txt = email.message_from_string(message)
        fields = msg_txt.keys()
        msg['id'] = message_id
        msg['message-id'] = message_id

        if 'Subject' in fields:
            msg['subject'] = self._decode_header(msg_txt.get('Subject'))

        if 'Content-Type' in fields:
            msg['content-type'] = msg_txt.get('Content-Type')

        if 'From' in fields:
            msg['from'] = self._decode_header(msg_txt.get('From'))

        if 'Delivered-To' in fields:
            msg['to'] = self._decode_header(msg_txt.get('Delivered-To'))

        if 'CC' in fields:
            msg['cc'] = self._decode_header(msg_txt.get('CC'))

        if 'Reply-to' in fields:
            msg['reply'] = self._decode_header(msg_txt.get('Reply-To'))

        if 'Date' in fields:
            msg['date'] = self._decode_header(msg_txt.get('Date'))

        if 'Content-Transfer-Encoding' in fields:
            msg['encoding'] = msg_txt.get('Content-Transfer-Encoding')

        if 'References' in fields:
            msg['references'] = msg_txt.get('References')

        if 'In-Reply-To' in fields:
            msg['in-reply-to'] = msg_txt.get('In-Reply-To')

        if 'X-Priority' in fields:
            msg['priority'] = msg_txt.get('X-Priority', '3 (Normal)').split(' ')[0]

        if not msg_txt.is_multipart() or 'text/plain' in msg.get('Content-Type', ''):
            encoding = msg_txt.get_content_charset()
            body = msg_txt.get_payload(decode=True)
            msg['body'] = tools.ustr(body, encoding)

        attachments = {}
        has_plain_text = False
        if msg_txt.is_multipart() or 'multipart/alternative' in msg.get('content-type', ''):
            body = ""
            for part in msg_txt.walk():
                if part.get_content_maintype() == 'multipart':
                    continue

                encoding = part.get_content_charset()
                filename = part.get_filename()
                if part.get_content_maintype()=='text':
                    content = part.get_payload(decode=True)
                    if filename:
                        attachments[filename] = content
                    elif not has_plain_text:
                        # main content parts should have 'text' maintype
                        # and no filename. we ignore the html part if
                        # there is already a plaintext part without filename,
                        # because presumably these are alternatives.
                        content = tools.ustr(content, encoding)
                        if part.get_content_subtype() == 'html':
                            body = tools.ustr(tools.html2plaintext(content))
                        elif part.get_content_subtype() == 'plain':
                            body = content
                            has_plain_text = True
                elif part.get_content_maintype() in ('application', 'image'):
                    if filename :
                        attachments[filename] = part.get_payload(decode=True)
                    else:
                        res = part.get_payload(decode=True)
                        body += tools.ustr(res, encoding)

            msg['body'] = body
            msg['attachments'] = attachments
        return msg
email_server_tools()

class thunderbird_partner(osv.osv_memory):
    _name = "thunderbird.partner"
    _description="Thunderbid mails"

    def create_contact(self,cr,user,vals):
        dictcreate = dict(vals)
        if not eval(dictcreate.get('partner_id')):
            dictcreate.update({'partner_id': False})
        create_id = self.pool.get('res.partner.address').create(cr, user, dictcreate)
        return create_id

    def history_message(self,cr,uid,vals):
        dictcreate = dict(vals)
        server_tools_pool = self.pool.get('email.server.tools')
        res_id = int(dictcreate.get('res_id'))
        model = str(dictcreate.get('model'))
        message = str(dictcreate.get('message'))
        server_tools_pool.history_message(cr,uid,model,res_id,message)
        return True

    def process_email(self,cr,uid,vals):
        dictcreate = dict(vals)
        model = str(dictcreate.get('model'))
        message = str(dictcreate.get('message'))
        return self.pool.get('email.server.tools').process_email(cr, uid, model, message, attach=True, context=None)

    def search_contact(self, cr, user, vals):
        address_obj = self.pool.get('res.partner.address')
        partner = address_obj.search(cr, user,[('email','=',vals)])
        res = {}
        res1 = {}

        if not partner:
            res1 = {
                'email': '',
                    }
            return res1.items()

        if partner:
            partner=partner[0]
            data = address_obj.read(cr,user, partner)
            res = {
                'partner_name': data['partner_id'] and data['partner_id'][1] or '',
                'contactname': data['name'] or '',
                'street': data['street'] or '',
                'street2': data['street2'] or '',
                'zip': data['zip'] or '',
                'city': data['city'] or '',
                'country': data['country_id'] and data['country_id'][1] or '',
                'state': data['state_id'] and data['state_id'][1] or '',
                'email': data['email'] or '',
                'phone': data['phone'] or '',
                'mobile': data['mobile'] or '',
                'fax': data['fax'] or '',
                'res_id': str(partner),
            }
        return res.items()

    def update_contact(self,cr,user,vals):
        dictcreate = dict(vals)
        res_id = dictcreate.get('res_id',False)
        result={}

        if not (dictcreate.get('partner_id')):
            dictcreate.update({'partner_id': False})
            create_id = self.pool.get('res.partner.address').create(cr, user, dictcreate)
            return create_id

        if res_id:
            address_obj = self.pool.get('res.partner.address')
            address_data = address_obj.read(cr, user, int(res_id), [])
            result = {
               'partner_id': address_data['partner_id'] and address_data['partner_id'][0] or False,
               'country_id': dictcreate['country_id'] and int(dictcreate['country_id'][0]) or False,
               'state_id': dictcreate['state_id'] and int(dictcreate['state_id'][0]) or False,
               'name': dictcreate['name'],
               'street': dictcreate['street'],
               'street2': dictcreate['street2'],
               'zip': dictcreate['zip'],
               'city': dictcreate['city'],
               'phone': dictcreate['phone'],
               'fax': dictcreate['fax'],
               'mobile': dictcreate['mobile'],
               'email': dictcreate['email'],
            }
        address_obj.write(cr, user,int(res_id),result )
        return True

    def create_partner(self,cr,user,vals):
        dictcreate = dict(vals)
        partner_obj = self.pool.get('res.partner')
        search_id =  partner_obj.search(cr, user,[('name','=',dictcreate['name'])])
        if search_id:
            return 0
        create_id =  partner_obj.create(cr, user, dictcreate)
        return create_id

    def search_document(self,cr,user,vals):
        dictcreate = dict(vals)
        search_id = self.pool.get('ir.model').search(cr, user,[('model','=',dictcreate['model'])])
        return (search_id and search_id[0]) or 0

    def search_checkbox(self,cr,user,vals):
        if vals[0]:
            value = vals[0][0]
        if vals[1]:
            obj = vals[1];
        name_get=[]
        er_val=[]
        for object in obj:
            dyn_object = self.pool.get(object)
            if object == 'res.partner.address':
                search_id1 = dyn_object.search(cr,user,[('name','ilike',value)])
                search_id2 = dyn_object.search(cr,user,[('email','=',value)])
                if search_id1:
                    name_get.append(object)
                    name_get.append(dyn_object.name_get(cr, user, search_id1))
                elif search_id2:
                    name_get.append(object)
                    name_get.append(dyn_object.name_get(cr, user, search_id2))
            else:
                try:
                    search_id1 = dyn_object.search(cr,user,[('name','ilike',value)])
                    if search_id1:
                        name_get.append(object)
                        name_get.append(dyn_object.name_get(cr, user, search_id1))
                except:
                    er_val.append(object)
                    continue
        if len(er_val) > 0:
            name_get.append('error')
            name_get.append(er_val)
        return name_get



    def list_alldocument(self,cr,user,vals):
        obj_list= [('crm.lead','Lead'),('project.issue','Project Issue'), ('hr.applicant','HR Recruitment')]
        object=[]
        model_obj = self.pool.get('ir.model')
        for obj in obj_list:
            if model_obj.search(cr, user, [('model', '=', obj[0])]):
                object.append(obj)
        return object

    def list_allcountry(self,cr,user,vals):
        country_list = []
        cr.execute("SELECT id, name from res_country")
        country_list = cr.fetchall()
        return country_list

    def list_allstate(self,cr,user,vals):
        cr.execute("SELECT id, name from res_country_state")
        state_country_list = cr.fetchall()
        return state_country_list

    def search_document_attachment(self,cr,user,vals):
        model_obj = self.pool.get('ir.model')
        object=''
        for obj in vals[0][1].split(','):
            if model_obj.search(cr, user, [('model', '=', obj)]):
                object += obj + ","
            else:
                object += "null,"
        return object

thunderbird_partner()
