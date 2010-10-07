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

import xmlrpclib
import sys
import socket
import os
import pythoncom
import time
from manager import ustr
import email

waittime = 10
wait_count = 0
wait_limit = 12

def execute(connector, method, *args):
    global wait_count
    res = False
    try:
        res = getattr(connector,method)(*args)
    except socket.error,e:
        if e.args[0] == 111:
            if wait_count > wait_limit:
                print "Server is taking too long to start, it has exceeded the maximum limit of %d seconds."%(wait_limit)
                clean()
                sys.exit(1)
            print 'Please wait %d sec to start server....'%(waittime)
            wait_count += 1
            time.sleep(waittime)
            res = execute(connector, method, *args)
        else:
            return res
    wait_count = 0
    return res

class XMLRpcConn(object):
    __name__ = 'XMLRpcConn'
    _com_interfaces_ = ['_IDTExtensibility2']
    _public_methods_ = ['GetDBList', 'login', 'GetAllObjects', 'GetObjList', 'InsertObj', 'DeleteObject', 'GetCSList', \
                        'ArchiveToOpenERP', 'IsCRMInstalled', 'GetPartners', 'GetObjectItems', \
                        'CreateCase', 'MakeAttachment', 'CreateContact', 'CreatePartner', 'getitem', 'setitem', \
                        'SearchPartnerDetail', 'WritePartnerValues', 'GetAllState', 'GetAllCountry', 'SearchPartner', 'SearchEmailResources', \
                        'GetCountry', 'GetStates', 'FindCountryForState']
    _reg_clsctx_ = pythoncom.CLSCTX_INPROC_SERVER
    _reg_clsid_ = "{C6399AFD-763A-400F-8191-7F9D0503CAE2}"
    _reg_progid_ = "Python.OpenERP.XMLRpcConn"
    _reg_policy_spec_ = "win32com.server.policy.EventHandlerPolicy"
    def __init__(self,server='localhost',port=8069,uri='http://localhost:8069'):
        self._server=server
        self._port=port
        self._uri=uri
        self._obj_list=[]
        self._dbname=''
        self._uname='admin'
        self._pwd='a'
        self._login=False
        self._running=False
        self._uid=False
        self._iscrm=True
        self.partner_id_list=None
        self.protocol=None

    def getitem(self, attrib):
        v=self.__getattribute__(attrib)
        return str(v)

    def setitem(self, attrib, value):
        return self.__setattr__(attrib, value)

    def GetDBList(self):
        conn = xmlrpclib.ServerProxy(self._uri + '/xmlrpc/db')
        try:
            db_list = execute(conn, 'list')
            if db_list == False:
                self._running=False
                return []
            else:
                self._running=True
        except:
            db_list=-1
            self._running=True
        return db_list

    def login(self,dbname, user, pwd):
        self._dbname = dbname
        self._uname = user
        self._pwd = pwd
        conn = xmlrpclib.ServerProxy(str(self._uri) + '/xmlrpc/common')
        uid = execute(conn,'login',dbname, ustr(user), ustr(pwd))
        return uid

    def GetAllObjects(self):
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','search',[])
        objects = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','read',ids,['model'])
        obj_list = [item['model'] for item in objects]
        return obj_list

    def GetObjList(self):
        self._obj_list=list(self._obj_list)
        self._obj_list.sort(reverse=True)
        return self._obj_list

    def InsertObj(self, obj_title,obj_name,image_path):
        self._obj_list=list(self._obj_list)
        self._obj_list.append((obj_title,obj_name,ustr(image_path)))
        self._obj_list.sort(reverse=True)

    def DeleteObject(self,sel_text):
        self._obj_list=list(self._obj_list)
        for obj in self._obj_list:
            if obj[0] == sel_text:
                self._obj_list.remove(obj)
                break

    def ArchiveToOpenERP(self, recs, mail):
        import win32ui, win32con
        conn = xmlrpclib.ServerProxy(self._uri + '/xmlrpc/object')
        import eml
        new_msg = files = ext_msg =""
        new_mail=eml.generateEML(mail)
        attachments=mail.Attachments
        for rec in recs: #[('res.partner', 3, 'Agrolait')]
            model = rec[0]
            res_id = rec[1]

            #Check if mailgate installed
            object_id = execute ( conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','search',[('model','=','mailgate.message')])
            if not object_id:
                win32ui.MessageBox("Mailgate is not installed on your configured database '%s' !!\n\nPlease install it to archive the mail."%(self._dbname),"Mailgate not installed",win32con.MB_ICONERROR)
                return

            object_ids = execute ( conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','search',[('model','=',model)])
            object_name  = execute( conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','read',object_ids,['name'])[0]['name']

            #Reading the Object ir.model Name

            ext_ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'mailgate.message','search',[('message_id','=',mail.EntryID),('model','=',model),('res_id','=',res_id)])
            if ext_ids:
                name = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,model,'read',res_id,['name'])['name']
                ext_msg += """This mail is already archived to {1} '{2}'.
""".format(object_name,name)
                continue

            msg = {
                'subject':mail.Subject,
                'date':str(mail.ReceivedTime),
                'body':mail.Body,
                'cc':mail.CC,
                'from':mail.SenderEmailAddress,
                'to':mail.To,
                'message-id':str(new_mail.get('Message-Id')),
                'references':str(new_mail.get('References')),
            }
            result = {}
            if attachments:
                result = self.MakeAttachment([rec], mail)
            attachment_ids = result.get(model, {}).get(res_id, [])
            ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'email.server.tools','history',model, res_id, msg, attachment_ids)
            new_msg += """- {0} : {1}\n""".format(object_name,str(rec[2]))
            flag = True

        if flag:
            t = ext_msg
            t += """Mail archived Successfully with attachments.\n"""+new_msg
            win32ui.MessageBox(t,"Archived to OpenERP",win32con.MB_ICONINFORMATION)
        return flag

    def IsCRMInstalled(self):
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        id = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','search',[('model','=','crm.lead')])
        return id

    def GetCSList(self):
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids = execute(conn,'execute',self._dbname,int(int(self._uid)),self._pwd,'crm.case.section','search',[])
        objects = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'crm.case.section','read',ids,['name'])
        obj_list = [ustr(item['name']).encode('iso-8859-1') for item in objects]
        return obj_list

    def GetPartners(self, search_partner=''):
        import win32ui
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids=[]
        obj_list=[]
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner','search',[('name','ilike',ustr(search_partner))])
        if ids:
            ids.sort()
            obj_list.append((-999, ustr('')))
            for id in ids:
                object = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner','read',[id],['id','name'])[0]
                obj_list.append((object['id'], ustr(object['name'])))
            obj_list.sort(lambda x, y: cmp(x[1],y[1]))
        return obj_list

    def GetObjectItems(self, search_list=[], search_text=''):
        import win32ui
        res = []
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        for obj in search_list:
            object_ids = execute ( conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','search',[('model','=',obj)])
            object_name = execute( conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','read',object_ids,['name'])[0]['name']
            if obj == "res.partner.address":
                ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,obj,'search',['|',('name','ilike',ustr(search_text)),('email','ilike',ustr(search_text))])
                recs = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,obj,'read',ids,['id','name','street','city'])
                for rec in recs:
                    name = ustr(rec['name'])
                    if rec['street']:
                        name += ', ' + ustr(rec['street'])
                    if rec['city']:
                        name += ', ' + ustr(rec['city'])
                    res.append((obj,rec['id'],name,object_name))
            else:
                ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,obj,'search',[('name','ilike',ustr(search_text))])
                recs = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,obj,'read',ids,['id','name'])
                for rec in recs:
                    name = ustr(rec['name'])
                    res.append((obj,rec['id'],name,object_name))
        return res

    def CreateCase(self, section, mail, partner_ids, with_attachments=True):
        import win32ui
        import eml
        section=str(section)
        flag = False
        id = -1
        try:
            conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
            email=eml.generateEML(mail)
            id = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'email.server.tools','process_email',section, email)
            if id > 0:
                flag = True
                return flag
            else:
                flag = False
                return flag
        except Exception,e:
            win32ui.MessageBox("Create Case\n"+str(e),"Mail Reading Error")
            return flag

    def MakeAttachment(self, recs, mail):
        attachments = mail.Attachments
        result = {}
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        att_folder_path = os.path.abspath(os.path.dirname(__file__)+"\\dialogs\\resources\\mails\\attachments\\")
        if not os.path.exists(att_folder_path):
            os.makedirs(att_folder_path)
        for rec in recs: #[('res.partner', 3, 'Agrolait')]

            obj = rec[0]
            obj_id = rec[1]
            res={}
            res['res_model'] = obj
            attachment_ids = []
            if obj not in result:
                result[obj] = {}
            for i in xrange(1, attachments.Count+1):
                fn = ustr(attachments[i].FileName)
                if len(fn) > 64:
                    l = 64 - len(fn)
                    f = fn.split('.')
                    fn = f[0][0:l] + '.' + f[-1]
                att_path = os.path.join(att_folder_path,fn)
                attachments[i].SaveAsFile(att_path)
                f=open(att_path,"rb")
                content = "".join(f.readlines()).encode('base64')
                f.close()
                res['name'] = ustr(attachments[i].DisplayName)
                res['datas_fname'] = ustr(fn)
                res['datas'] = content
                res['res_id'] = obj_id
                id = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.attachment','create',res)
                attachment_ids.append(id)
            result[obj].update({obj_id: attachment_ids})
        return result

    def CreateContact(self, res=None):
        res=eval(str(res))
        partner = res['partner_id']
        state = res['state_id']
        country = res['country_id']
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        partner_id = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.partner', 'search', [('name','=',ustr(partner))])
        res.update({'partner_id' : partner_id[0]})
        if not state == "":
            country_id = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.country', 'search', [('name','=',ustr(country))])
            res.update({'country_id' : country_id[0]})
        if not country == "":
            state_id = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.country.state', 'search', [('name','=',ustr(state))])
            res.update({'state_id' : state_id[0]})
        id = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner.address','create',res)
        return id

    def CreatePartner(self, res):
        res=eval(str(res))
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner','search',[('name','=',res['name'])])
        if ids:
            return False
        id = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner','create',res)
        return id

    def SearchPartnerDetail(self, search_email_id):
        import win32ui
        res_vals = []
        address = {}
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        address_id = execute(conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.partner.address', 'search', [('email','ilike',ustr(search_email_id))])
        if not address_id :
            return
        address = execute(conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.partner.address','read',address_id[0],['id','partner_id','name','street','street2','city','state_id','country_id','phone','mobile','email','fax','zip'])
        for key, vals in address.items():
            res_vals.append([key,vals])
        return res_vals

    def WritePartnerValues(self, new_vals):
        import win32ui
        flag = -1
        new_dict = dict(new_vals)
        email=new_dict['email']
        partner = new_dict['partner']
        country_val = new_dict['country']
        state_val = new_dict['state']
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        partner_id = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.partner', 'search', [('name','=',ustr(partner))])
        country_id = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.country', 'search', [('name','=',ustr(country_val))])
        state_id = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.country.state', 'search', [('name','=',ustr(state_val))])
        address_id = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.partner.address', 'search', [('email','=',ustr(email))])
        if not partner_id or not address_id or not country_id or not state_id:
            return flag
        address = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.partner.address','read',address_id[0],['id','partner_id','state_id','country_id'])
        vals_res_address={
                           'partner_id' : partner_id[0],
                           'name' : new_dict['name'],
                           'street':new_dict['street'],
                           'street2' : new_dict['street2'],
                           'city' : new_dict['city'],
                           'phone' : new_dict['phone'],
                           'mobile' : new_dict['mobile'],
                           'fax' : new_dict['fax'],
                           'zip' : new_dict['zip'],
                           'country_id' : country_id[0],
                           'state_id' : state_id[0]
                         }
        temp = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.partner.address', 'write', address_id, vals_res_address)
        if temp:
            flag=1
        else:
            flag=0
        return flag

    def GetAllState(self):
        import win32ui
        state_list = []
        state_ids = []
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        state_ids = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.country.state', 'search', [])
        for state_id in state_ids:
            obj = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.country.state', 'read', [state_id],['id','name'])[0]
            state_list.append((obj['id'], ustr(obj['name'])))
        return state_list

    def GetAllCountry(self):
        import win32ui
        country_list = []
        country_ids = []
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        country_ids = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.country', 'search', [])
        for country_id in country_ids:
            obj = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.country','read', [country_id], ['id','name'])[0]
            country_list.append((obj['id'], ustr(obj['name'])))
        return country_list

    def SearchPartner(self, partner = ""):
        import win32ui
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        partner_id = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'res.partner', 'search', [('name','=',ustr(partner))])
        if not partner_id:
        	return None
        return partner_id[0]

    def SearchEmailResources(self, mail):
        import win32ui
        import eml

        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        sub = ""
        res_vals = []

        try:
#            new_mail = eml.generateEML(mail)
            email.SaveAs()
            message_id = str(new_mail.get('message-id'))
        except Exception,e:
            win32ui.MessageBox(str(e),"Mail Reading Error")
            return None
        mail_id = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'mailgate.message', 'search', [('message_id','=',message_id)])
        if not mail_id:
            return None
        address = execute( conn, 'execute', self._dbname, int(self._uid), self._pwd, 'mailgate.message','read',mail_id[0],['model','res_id'])
        for key, vals in address.items():
            res_vals.append([key,vals])
        return res_vals


    def GetCountry(self, country_search=''):
        import win32ui
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids=[]
        obj_list=[]
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.country','search',[('name','ilike',ustr(country_search))])
        if ids:
            ids.sort()
            for id in ids:
                object = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.country','read',[id],['id','name'])[0]
                obj_list.append((object['id'], ustr(object['name'])))
            obj_list.sort(lambda x, y: cmp(x[1],y[1]))
        return obj_list

    def GetStates(self, state_search=''):
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids=[]
        obj_list=[]
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.country.state','search',[('name','ilike',ustr(state_search))])
        if ids:
            ids.sort()
            for id in ids:
                object = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.country.state','read',[id],['id','name'])[0]
                obj_list.append((object['id'], ustr(object['name'])))
            obj_list.sort(lambda x, y: cmp(x[1],y[1]))
        return obj_list
    def FindCountryForState(self, state_search=''):
        import win32ui
        res_vals = []
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.country.state','search',[('name','=',ustr(state_search))])
        if not ids:
            return None
        object = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.country.state','read',ids)[0]
        country = object['country_id'][1]
        return country
