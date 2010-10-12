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

import time
from document_webdav import nodes
import logging
import StringIO

# TODO: implement DAV-aware errors, inherit from IOError

def dict_merge(*dicts):
    """ Return a dict with all values of dicts
    """
    res = {}
    for d in dicts:
        res.update(d)
    return res

def dict_merge2(*dicts):
    """ Return a dict with all values of dicts.
        If some key appears twice and contains iterable objects, the values
        are merged (instead of overwritten).
    """
    res = {}
    for d in dicts:
        for k in d.keys():
            if k in res and isinstance(res[k], (list, tuple)):
                res[k] = res[k] + d[k]
            else:
                res[k] = d[k]
    return res

# Assuming that we have set global properties right, we mark *all* 
# directories as having calendar-access.
nodes.node_dir.http_options = dict_merge2(nodes.node_dir.http_options,
            { 'DAV': ['calendar-access',] })

class node_calendar_collection(nodes.node_dir):
    DAV_PROPS = dict_merge2(nodes.node_dir.DAV_PROPS,
            { "http://calendarserver.org/ns/" : ('getctag',), } )
    DAV_M_NS = dict_merge2(nodes.node_dir.DAV_M_NS,
            { "http://calendarserver.org/ns/" : '_get_dav', } )

    def _file_get(self,cr, nodename=False):
        return []

    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        dirobj = self.context._dirobj
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        where = [('collection_id','=',self.dir_id)]
        ext = False
        if name and name.endswith('.ics'):
            name = name[:-4]
            ext = True
        if name:
            where.append(('name','=',name))
        if not domain:
            domain = []
        where = where + domain
        fil_obj = dirobj.pool.get('basic.calendar')
        ids = fil_obj.search(cr,uid,where,context=ctx)
        res = []
        for cal in fil_obj.browse(cr, uid, ids, context=ctx):
            if (not name) or not ext:
                res.append(node_calendar(cal.name, self, self.context, cal))
            if (not name) or ext:
                res.append(res_node_calendar(cal.name+'.ics', self, self.context, cal))
            # May be both of them!
        return res

    def _get_dav_owner(self, cr):
        # Todo?
        return False

    def _get_ttag(self, cr):
        return 'calen-dir-%d' % self.dir_id

    def _get_dav_getctag(self, cr):
        result = self.get_etag(cr)
        return str(result)

class node_calendar_res_col(nodes.node_res_obj):
    """ Calendar collection, as a dynamically created node
    
    This class shall be used instead of node_calendar_collection, when the
    node is under dynamic ones.
    """
    DAV_PROPS = dict_merge2(nodes.node_res_obj.DAV_PROPS,
            { "http://calendarserver.org/ns/" : ('getctag',), } )
    DAV_M_NS = dict_merge2(nodes.node_res_obj.DAV_M_NS,
            { "http://calendarserver.org/ns/" : '_get_dav', } )

    def _file_get(self,cr, nodename=False):
        return []

    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        dirobj = self.context._dirobj
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        where = [('collection_id','=',self.dir_id)]
        ext = False
        if name and name.endswith('.ics'):
            name = name[:-4]
            ext = True
        if name:
            where.append(('name','=',name))
        if not domain:
            domain = []
        where = where + domain
        fil_obj = dirobj.pool.get('basic.calendar')
        ids = fil_obj.search(cr,uid,where,context=ctx)
        res = []
        # TODO: shall we use any of our dynamic information??
        for cal in fil_obj.browse(cr, uid, ids, context=ctx):
            if (not name) or not ext:
                res.append(node_calendar(cal.name, self, self.context, cal))
            if (not name) or ext:
                res.append(res_node_calendar(cal.name+'.ics', self, self.context, cal))
            # May be both of them!
        return res

    def _get_ttag(self, cr):
        return 'calen-dir-%d' % self.dir_id

    def _get_dav_getctag(self, cr):
        result = self.get_etag(cr)
        return str(result)

class node_calendar(nodes.node_class):
    our_type = 'collection'
    DAV_PROPS = {
            "DAV:": ('supported-report-set',),
            # "http://cal.me.com/_namespace/" : ('user-state',),
            "http://calendarserver.org/ns/" : ( 'getctag',),
            'http://groupdav.org/': ('resourcetype',),
            "urn:ietf:params:xml:ns:caldav" : (
                    'calendar-description', 
                    'supported-calendar-component-set',
                    )}
    DAV_PROPS_HIDDEN = {
            "urn:ietf:params:xml:ns:caldav" : (
                    'calendar-data',
                    'calendar-timezone',
                    'supported-calendar-data',
                    'max-resource-size',
                    'min-date-time',
                    'max-date-time',
                    )}

    DAV_M_NS = {
           "DAV:" : '_get_dav',
           # "http://cal.me.com/_namespace/": '_get_dav', 
           'http://groupdav.org/': '_get_gdav',
           "http://calendarserver.org/ns/" : '_get_dav',
           "urn:ietf:params:xml:ns:caldav" : '_get_caldav'}

    http_options = { 'DAV': ['calendar-access'] }

    def __init__(self,path, parent, context, calendar):
        super(node_calendar,self).__init__(path, parent,context)
        self.calendar_id = calendar.id
        self.mimetype = 'application/x-directory'
        self.create_date = calendar.create_date
        self.write_date = calendar.write_date or calendar.create_date
        self.content_length = 0
        self.displayname = calendar.name
        self.cal_type = calendar.type

    def _get_dav_getctag(self, cr):
        result = self._get_ttag(cr) + ':' + str(time.time())
        return str(result)

    def _get_dav_user_state(self, cr):
        #TODO
        return 'online'

    def get_dav_resourcetype(self, cr):
        res = [ ('collection', 'DAV:'),
                (str(self.cal_type + '-collection'), 'http://groupdav.org/'),
                ('calendar', 'urn:ietf:params:xml:ns:caldav') ]
        return res

    def get_domain(self, cr, filters):
        # TODO: doc.
        res = []
        if not filters:
            return res
        _log = logging.getLogger('caldav.query')
        if filters.localName == 'calendar-query':
            res = []
            for filter_child in filters.childNodes:
                if filter_child.nodeType == filter_child.TEXT_NODE:
                    continue
                if filter_child.localName == 'filter':
                    for vcalendar_filter in filter_child.childNodes:
                        if vcalendar_filter.nodeType == vcalendar_filter.TEXT_NODE:
                            continue
                        if vcalendar_filter.localName == 'comp-filter':
                            if vcalendar_filter.getAttribute('name') == 'VCALENDAR':
                                for vevent_filter in vcalendar_filter.childNodes:
                                    if vevent_filter.nodeType == vevent_filter.TEXT_NODE:
                                        continue
                                    if vevent_filter.localName == 'comp-filter':
                                        if vevent_filter.getAttribute('name'):
                                            res = [('type','=',vevent_filter.getAttribute('name').lower() )]
                                            
                                        for cfe in vevent_filter.childNodes:
                                            if cfe.localName == 'time-range':
                                                if cfe.getAttribute('start'):
                                                    _log.warning("Ignore start.. ")
                                                    # No, it won't work in this API
                                                    #val = cfe.getAttribute('start')
                                                    #res += [('dtstart','=', cfe)]
                                                elif cfe.getAttribute('end'):
                                                    _log.warning("Ignore end.. ")
                                            else:
                                                _log.debug("Unknown comp-filter: %s", cfe.localName)
                                    else:
                                        _log.debug("Unknown comp-filter: %s", vevent_filter.localName)
                        else:
                            _log.debug("Unknown filter element: %s", vcalendar_filter.localName)
                else:
                    _log.debug("Unknown calendar-query element: %s", filter_child.localName)
            return res
        elif filters.localName == 'calendar-multiget':
            names = []
            for filter_child in filters.childNodes:
                if filter_child.nodeType == filter_child.TEXT_NODE:
                    continue
                if filter_child.localName == 'href':
                    if not filter_child.firstChild:
                        continue
                    uri = filter_child.firstChild.data
                    caluri = uri.split('/')
                    if len(caluri):
                        caluri = caluri[-2]
                        if caluri not in names : names.append(caluri)
                else:
                    _log.debug("Unknonwn multiget element: %s", filter_child.localName)
            res = [('name','in',names)]
            return res
        else:
            _log.debug("Unknown element in REPORT: %s", filters.localName)
        return res

    def children(self, cr, domain=None):
        return self._child_get(cr, domain=domain)

    def child(self,cr, name, domain=None):
        res = self._child_get(cr, name, domain=domain)
        if res:
            return res[0]
        return None


    def _child_get(self, cr, name=False, parent_id=False, domain=None):
        dirobj = self.context._dirobj
        uid = self.context.uid
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        where = []
        if name:
            if name.endswith('.ics'):
                name = name[:-4]
            try:
                where.append(('id','=',int(name)))
            except ValueError:
                # if somebody requests any other name than the ones we
                # generate (non-numeric), it just won't exist
                # FIXME: however, this confuses Evolution (at least), which
                # thinks the .ics node hadn't been saved.
                return []

        if not domain:
            domain = []

        fil_obj = dirobj.pool.get('basic.calendar')
        ids = fil_obj.search(cr, uid, domain)
        res = []
        if self.calendar_id in ids:
            res = fil_obj.get_calendar_objects(cr, uid, [self.calendar_id], self, domain=where, context=ctx)
        return res

    def create_child(self, cr, path, data):
        """ API function to create a child file object and node
            Return the node_* created
        """
        # we ignore the path, it will be re-generated automatically
        fil_obj = self.context._dirobj.pool.get('basic.calendar')
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        uid = self.context.uid

        res = self.set_data(cr, data)

        if res and len(res):
            # We arbitrarily construct only the first node of the data
            # that have been imported. ICS may have had more elements,
            # but only one node can be returned here.
            assert isinstance(res[0], (int, long))
            fnodes = fil_obj.get_calendar_objects(cr, uid, [self.calendar_id], self,
                    domain=[('id','=',res[0])], context=ctx)
            return fnodes[0]
        # If we reach this line, it means that we couldn't import any useful
        # (and matching type vs. our node kind) data from the iCal content.
        return None


    def set_data(self, cr, data, fil_obj = None):
        uid = self.context.uid
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        res = calendar_obj.import_cal(cr, uid, data, self.calendar_id)
        return res

    def get_data_len(self, cr, fil_obj = None):
        return self.content_length

    def _get_ttag(self,cr):
        return 'calendar-%d' % (self.calendar_id,)

    def rmcol(self, cr):
        return False

    def _get_caldav_calendar_data(self, cr):
        res = []
        for child in self.children(cr):
            res.append(child._get_caldav_calendar_data(cr))
        return res

    def _get_caldav_calendar_description(self, cr):
        uid = self.context.uid
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        ctx = self.context.context.copy()
        ctx.update(self.dctx)
        try:
            calendar = calendar_obj.browse(cr, uid, self.calendar_id, context=ctx)
            return calendar.description or calendar.name
        except Exception, e:
            return None

    def _get_dav_supported_report_set(self, cr):
        
        return ('supported-report', 'DAV:', 
                    ('report','DAV:',
                            ('principal-match','DAV:')
                    )
                )

    def _get_caldav_supported_calendar_component_set(self, cr):
        return ('comp', 'urn:ietf:params:xml:ns:caldav', None,
                    {'name': self.cal_type.upper()} )
        
    def _get_caldav_calendar_timezone(self, cr):
        return None #TODO
        
    def _get_caldav_supported_calendar_data(self, cr):
        return ('calendar-data', 'urn:ietf:params:xml:ns:caldav', None,
                    {'content-type': "text/calendar", 'version': "2.0" } )
        
    def _get_caldav_max_resource_size(self, cr):
        return 65535

    def _get_caldav_min_date_time(self, cr):
        return "19700101T000000Z"

    def _get_caldav_max_date_time(self, cr):
        return "21001231T235959Z" # I will be dead by then

class res_node_calendar(nodes.node_class):
    our_type = 'file'
    DAV_PROPS = {
            "http://calendarserver.org/ns/" : ('getctag',),
            "urn:ietf:params:xml:ns:caldav" : (
                    'calendar-description',
                    'calendar-data',
                    )}
    DAV_M_NS = {
           "http://calendarserver.org/ns/" : '_get_dav',
           "urn:ietf:params:xml:ns:caldav" : '_get_caldav'}

    http_options = { 'DAV': ['calendar-access'] }

    def __init__(self,path, parent, context, res_obj, res_model=None, res_id=None):
        super(res_node_calendar,self).__init__(path, parent, context)
        self.mimetype = 'text/calendar'
        self.create_date = parent.create_date
        self.write_date = parent.write_date or parent.create_date
        self.calendar_id = hasattr(parent, 'calendar_id') and parent.calendar_id or False
        if res_obj:
            if not self.calendar_id: self.calendar_id = res_obj.id
            pr = res_obj.perm_read()[0]
            self.create_date = pr.get('create_date')
            self.write_date = pr.get('write_date') or pr.get('create_date')
            self.displayname = res_obj.name

        self.content_length = 0

        self.model = res_model
        self.res_id = res_id

    def open(self, cr, mode=False):
        if self.type in ('collection','database'):
            return False
        s = StringIO.StringIO(self.get_data(cr))
        s.name = self
        return s

    def get_data(self, cr, fil_obj = None):
        uid = self.context.uid
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        context = self.context.context.copy()
        context.update(self.dctx)
        context.update({'model': self.model, 'res_id':self.res_id})
        res = calendar_obj.export_cal(cr, uid, [self.calendar_id], context=context)
        return res
  
    def _get_caldav_calendar_data(self, cr):
        return self.get_data(cr)

    def get_data_len(self, cr, fil_obj = None):
        return self.content_length

    def set_data(self, cr, data, fil_obj = None):
        uid = self.context.uid
        context = self.context.context.copy()
        context.update(self.dctx)
        context.update({'model': self.model, 'res_id':self.res_id})
        calendar_obj = self.context._dirobj.pool.get('basic.calendar')
        res =  calendar_obj.import_cal(cr, uid, data, self.calendar_id, context=context)
        return res

    def _get_ttag(self,cr):
        res = False
        if self.model and self.res_id:
            res = '%s_%d' % (self.model, self.res_id)
        elif self.calendar_id:
            res = '%d' % (self.calendar_id)
        return res


    def rm(self, cr):
        uid = self.context.uid
        res = False
        if self.type in ('collection','database'):
            return False
        if self.model and self.res_id:
            document_obj = self.context._dirobj.pool.get(self.model)
            if document_obj:
                res =  document_obj.unlink(cr, uid, [self.res_id])

        return res

   

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4
