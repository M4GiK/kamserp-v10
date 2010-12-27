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

from osv import osv, fields
from tools import config
import base64
import addons

class caldav_browse(osv.osv_memory):
    _name = 'caldav.browse'
    _description = 'Caldav Browse'

    _columns = {
        'url' : fields.char('Caldav Server', size=264, required=True),
        'caldav_doc_file':fields.binary('Caldav Document', readonly=True, help="Caldav Document ile."),
        'description':fields.text('Description', readonly=True)
    }

    def default_get(self, cr, uid, fields, context=None):
        res = {}
        host = ''
        port = ''
        prefix = 'http://'  
        if not config.get('xmlrpc'):
            if not config.get('netrpc'):
                prefix = 'https://' 
                host = config.get('xmlrpcs_interface', None)
                port = config.get('xmlrpcs_port', 8071)
            else:
                host = config.get('netrpc_interface', None)
                port = config.get('netrpc_port',8070) 
        else: 
            host = config.get('xmlrpc_interface', None)
            port = config.get('xmlrpc_port',8069)
        if host ==  '' or None:
                host = 'localhost'
                port = 8069
        if not config.get_misc('webdav','enable',True):
            raise Exception("WebDAV is disabled, cannot continue")
        user_pool = self.pool.get('res.users')
        current_user = user_pool.browse(cr, uid, uid, context=context)
        pref_obj = self.pool.get('user.preference')
        pref_ids = pref_obj.browse(cr, uid ,context.get('rec_id',False), context=context)
        if pref_ids:
           pref_ids = pref_ids[0] 
           url = host + ':' + str(port) + '/'+ pref_ids.service + '/' + cr.dbname + '/'+'calendar/'+ 'users/'+ current_user.login + '/'+ pref_ids.collection.name+ '/'+ pref_ids.calendar.name
        file = open(addons.get_module_resource('caldav','doc', 'Caldav_doc.pdf'),'rb')
        res['caldav_doc_file'] = base64.encodestring(file.read())
        res['description'] = """
  * Webdav server that provides remote access to calendar
  * Synchronisation of calendar using WebDAV
  * Customize calendar event and todo attribute with any of OpenERP model
  * Provides iCal Import/Export functionality

    To access Calendars using CalDAV clients, point them to:
        http://HOSTNAME:PORT/webdav/DATABASE_NAME/calendars/users/USERNAME/c

    To access OpenERP Calendar using WebCal to remote site use the URL like:
        http://HOSTNAME:PORT/webdav/DATABASE_NAME/Calendars/CALENDAR_NAME.ics

      Where,
        HOSTNAME: Host on which OpenERP server(With webdav) is running
        PORT : Port on which OpenERP server is running (By Default : 8069)
        DATABASE_NAME: Name of database on which OpenERP Calendar is created
        CALENDAR_NAME: Name of calendar to access
     """
        res['url'] = prefix+url
        return res

    def browse_caldav(self, cr, uid, ids, context):

        return {}

caldav_browse()

class user_preference(osv.osv_memory):
    
    _name = 'user.preference'
    _description = 'User preference FOrm'

    _columns = {
               'collection' :fields.many2one('document.directory', "Calendar Collection", required=True, domain = [('calendar_collection', '=', True)]),
               'calendar' :fields.many2one('basic.calendar', 'Calendar', required=True),
               'service': fields.selection([('webdav','WEBDAV'),('vdir','VDIR')], "Services")
    }    
    _defaults={
              'service': lambda *a: 'webdav' 
   }    
    def open_window(self, cr, uid, ids, context=None):
        obj_model = self.pool.get('ir.model.data')
        model_data_ids = obj_model.search(cr,uid,[('model','=','ir.ui.view'),('name','=','caldav_Browse')])
        resource_id = obj_model.read(cr, uid, model_data_ids, fields=['res_id'])
        context.update({'rec_id': ids})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'caldav.browse',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
    
    
user_preference()
