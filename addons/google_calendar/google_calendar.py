##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2012 OpenERP SA (<http://www.openerp.com>).
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

import simplejson
import re
import urllib
import urllib2


from openerp import tools
from openerp.tools.translate import _

from openerp.addons.web.http import request
import werkzeug.utils

from datetime import datetime, timedelta, date
from dateutil import parser
import pytz
from openerp.osv import fields, osv
from openerp.osv import osv


google_state_mapping = {
    'needs-action':'needsAction',
    'declined': 'declined',
    'tentative':'tentative',
    'accepted':'accepted',
    'delegated':'declined',
}
oe_state_mapping = {
    'needsAction':'needs-action',
    'declined': 'declined',
    'tentative':'tentative',
    'accepted':'accepted',
}

class google_calendar(osv.osv):
    _name = 'google.calendar'
    
    STR_SERVICE = 'calendar'
    
#################################        
##     DISCUSS WITH GMAIL      ##
#################################
    
    def generate_data(self, cr, uid, event, context=None):
        if event.allday:
            start_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(event.date, tools.DEFAULT_SERVER_DATETIME_FORMAT) , context=context).isoformat('T').split('T')[0]
            end_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(event.date, tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(hours=event.duration), context=context).isoformat('T').split('T')[0]
            type = 'date'
        else:
            start_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(event.date, tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context).isoformat('T')
            end_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(event.date_deadline, tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context).isoformat('T')
            type = 'dateTime'
        attendee_list = []
        
        print "att for event %s : %s" % (event.id,event.attendee_ids)

        for attendee in event.attendee_ids:
            attendee_list.append({
                'email':attendee.email or 'NoEmail@mail.com',
                'displayName':attendee.partner_id.name,
                'responseStatus':google_state_mapping.get(attendee.state, 'needsAction'),
            })
        data = {
            "summary": event.name or '',
            "description": event.description or '',
            "start":{
                 type:start_date,
                 'timeZone':'UTC'
             },
            "end":{
                 type:end_date,                 
                 'timeZone':'UTC'
             },
            "attendees":attendee_list,
            "location":event.location or '',
            "visibility":event['class'] or 'public',
        }
        if event.recurrency and event.rrule:
            data["recurrence"]=["RRULE:"+event.rrule]

        if not event.active:
            data["state"] = "cancelled"
              
        return data
    
    def create_an_event(self, cr, uid,event, context=None):
        gs_pool = self.pool.get('google.service')
        
        data = self.generate_data(cr, uid,event, context=context)
        
        url = "/calendar/v3/calendars/%s/events?fields=%s&access_token=%s" % ('primary',urllib.quote('id,updated'),self.get_token(cr,uid,context))
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data_json = simplejson.dumps(data)
        
        response = gs_pool._do_request(cr, uid, url, data_json, headers, type='POST', context=context)
        #TODO Check response result
        
        return response
        
    def delete_an_event(self, cr, uid,event_id, context=None):
        gs_pool = self.pool.get('google.service')
        
        params = {
                 'access_token' : self.get_token(cr,uid,context)
                }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        
        url = "/calendar/v3/calendars/%s/events/%s" % ('primary',event_id)
        
        response = gs_pool._do_request(cr, uid, url, params, headers, type='DELETE', context=context)
        print "@@@RESPONSE",response
        return response
    
    
    def get_event_dict(self,cr,uid,token=False,nextPageToken=False,context=None):
        if not token:
            token = self.get_token(cr,uid,context)
            
        gs_pool = self.pool.get('google.service')
        
        params = {
                 'fields': 'items,nextPageToken',
                 'access_token' : token
                }
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            
        url = "/calendar/v3/calendars/%s/events" % 'primary' #?fields=%s&access_token=%s" % ('primary',urllib.quote('items,nextPageToken'), token)
        if nextPageToken:
            params['pageToken'] = nextPageToken
        
        
        content = gs_pool._do_request(cr, uid, url, params, headers, type='GET', context=context)    
        
        google_events_dict = {}
        
        print content['items']
        
                
        for google_event in content['items']:
            google_events_dict[google_event['id']] = google_event
            #if google_event.get('updated',False):
#                 if withInstance:
#                     for instance in self.get_instance_event(cr,uid,event_id,context):
#                         google_events_dict[instance['id']] = instance
#                 else:     
                
        if content.get('nextPageToken', False):
            google_events_dict.update(self.get_event_dict(cr,uid,token,content['nextPageToken'],context=context))
        return google_events_dict    
        
    def update_to_google(self, cr, uid, oe_event, google_event, context):
        crm_meeting = self.pool['crm.meeting']
        gs_pool = self.pool.get('google.service')

        
        url = "/calendar/v3/calendars/%s/events/%s?fields=%s&access_token=%s" % ('primary', google_event['id'],'id,updated', self.get_token(cr,uid,context))
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data = self.generate_data(cr,uid ,oe_event, context)
        data['sequence'] = google_event.get('sequence', 0)
        data_json = simplejson.dumps(data)
        
        
        content = gs_pool._do_request(cr, uid, url, data_json, headers, type='PATCH', context=context)
        
        #except urllib2.HTTPError,e:
        #    error_message = json.loads(e.read())
            
        update_date = datetime.strptime(content['updated'],"%Y-%m-%dT%H:%M:%S.%fz")
        crm_meeting.write(cr, uid, [oe_event.id], {'oe_update_date':update_date})
             
    def update_an_event(self, cr, uid,event, context=None):
        gs_pool = self.pool.get('google.service')
        
        data = self.generate_data(cr, uid,event, context=context)
        
        url = "/calendar/v3/calendars/%s/events/%s" % ('primary', event.google_internal_event_id)
        headers = {}
        data['access_token'] = self.get_token(cr,uid,context) 
        
        response = gs_pool._do_request(cr, uid, url, data, headers, type='GET', context=context)
        
        #TODO, il http fail, no event, do DELETE ! ?
                
        return response
        
    def update_recurrent_event_exclu(self, cr, uid,instance_id,event_ori_google_id,event_new, context=None):
        gs_pool = self.pool.get('google.service')
        
        data = self.generate_data(cr, uid,event_new, context=context)
        
        data['recurringEventId'] = event_ori_google_id
        data['originalStartTime'] = event_new.recurrent_id_date
                
        url = "/calendar/v3/calendars/%s/events/%s?access_token=%s" % ('primary', instance_id,self.get_token(cr,uid,context))
        headers = { 'Content-type': 'application/json'}
        
        data['sequence'] = self.get_sequence(cr, uid, instance_id, context)
        
        data_json = simplejson.dumps(data)
        response = gs_pool._do_request(cr, uid, url, data_json, headers, type='PUT', context=context)

        #TODO, il http fail, no event, do DELETE ! ?
                
        return response
#################################        
##   MANAGE SYNCHRO TO GMAIL   ##
#################################        
       
    def update_from_google(self, cr, uid, event, single_event_dict, type, context):
        crm_meeting = self.pool['crm.meeting']
        res_partner_obj = self.pool['res.partner']
        calendar_attendee_obj = self.pool['calendar.attendee']
        attendee_record= [] 
        result = {}
       
        if single_event_dict.get('attendees',False):
            for google_attendee in single_event_dict['attendees']:
                if type == "write":
                    for oe_attendee in event['attendee_ids']:
                        if calendar_attendee_obj.browse(cr, uid ,oe_attendee,context=context).email == google_attendee['email']:
                            calendar_attendee_obj.write(cr, uid,[oe_attendee] ,{'state' : oe_state_mapping[google_attendee['responseStatus']]})
                            google_attendee['found'] = True
                if google_attendee.get('found',False):
                    continue
                attendee_id = res_partner_obj.search(cr, uid,[('email', '=', google_attendee['email'])], context=context)
                if not attendee_id:
                    attendee_id = [res_partner_obj.create(cr, uid,{'email': google_attendee['email'], 'name': google_attendee.get("displayName",False) or google_attendee['email'] }, context=context)]
                attendee = res_partner_obj.read(cr, uid, attendee_id[0], ['email'], context=context)
                attendee['partner_id'] = attendee.pop('id')
                attendee['state'] = oe_state_mapping[google_attendee['responseStatus']]
                attendee_record.append((0, 0, attendee))
        UTC = pytz.timezone('UTC')                
        if single_event_dict['start'].get('dateTime',False) and single_event_dict['end'].get('dateTime',False):
            date = parser.parse(single_event_dict['start']['dateTime'])
            date_deadline = parser.parse(single_event_dict['end']['dateTime'])
            delta = date_deadline.astimezone(UTC) - date.astimezone(UTC)
            date = str(date.astimezone(UTC))[:-6]
            date_deadline = str(date_deadline.astimezone(UTC))[:-6]
            allday = False
        else:            
            date = (single_event_dict['start']['date'] + ' 00:00:00')
            date_deadline = (single_event_dict['end']['date'] + ' 00:00:00')
            d_start = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            d_end = datetime.strptime(date_deadline, "%Y-%m-%d %H:%M:%S")
            delta = (d_end - d_start)
            allday = True
        
        result['duration'] = (delta.seconds / 60) / 60.0 + delta.days *24
            
        update_date = datetime.strptime(single_event_dict['updated'],"%Y-%m-%dT%H:%M:%S.%fz")
        result.update({
            'attendee_ids': attendee_record,
            'date': date,
            'date_deadline': date_deadline,
            'allday': allday,
            'name': single_event_dict.get('summary','Event'),
            'description': single_event_dict.get('description',False),
            'location':single_event_dict.get('location',False),
            'class':single_event_dict.get('visibility','public'),
            'oe_update_date':update_date,
            'google_internal_event_id': single_event_dict.get('id',False),
        })
        print "Location = <%s> vs <%s>" % (single_event_dict.get('location'),result['location'])
        #import ipdb; ipdb.set_trace()
        if single_event_dict.get("recurrence",False):
            rrule = [rule for rule in single_event_dict["recurrence"] if rule.startswith("RRULE:")][0][6:]
            result['rrule']=rrule
                    
        if type == "write":
            crm_meeting.write(cr, uid, event['id'], result, context=context)
        elif type == "copy":
            result['write_type'] = "copy"
            crm_meeting.write(cr, uid, event['id'], result, context=context)
        elif type == "create":
            crm_meeting.create(cr, uid, result, context=context)        
        
    def synchronize_events(self, cr, uid, ids, context=None):
        gc_obj = self.pool.get('google.calendar')
                
        self.create_new_events(cr, uid, context=context)
        cr.commit()

        self.bind_recurring_events_to_google(cr, uid, context)
        cr.commit()

        res = self.update_events(cr, uid, context)
    
        return {
                "status" :  res and "NeedRefresh" or "NoNewEventFromGoogle",
                "url" : '' 
                }
     
    def create_new_events(self, cr, uid, context):
        gc_pool = self.pool.get('google.calendar')
        
        crm_meeting = self.pool['crm.meeting']
        user_obj = self.pool['res.users']
        myPartnerID = user_obj.browse(cr,uid,uid,context=context).partner_id.id
        
        context_norecurrent = context.copy()
        context_norecurrent['virtual_id'] = False
        
        new_events_ids = crm_meeting.search(cr, uid,[('partner_ids', 'in', myPartnerID),('google_internal_event_id', '=', False),'|',('recurrent_id', '=', 0),('recurrent_id', '=', False)], context=context_norecurrent)

        for event in crm_meeting.browse(cr, uid, list(set(new_events_ids)), context):
            response = self.create_an_event(cr,uid,event,context=context)
            update_date = datetime.strptime(response['updated'],"%Y-%m-%dT%H:%M:%S.%fz")
            crm_meeting.write(cr, uid, event.id, {'google_internal_event_id': response['id'], 'oe_update_date':update_date})
            #Check that response OK and return according to that
        
        return True
    
    
    def get_empty_synchro_summarize(self) :
        return {
                'oe_event_id' : False,
                'oe_isRecurrence':False,
                'oe_isInstance':False,
                'oe_update':False,
                'oe_status':False,
                                
                'gg_isRecurrence':False,
                'gg_isInstance':False,
                'gg_update':False,
                'gg_status':False,                
        }
    

    def bind_recurring_events_to_google(self, cr, uid,  context):
        crm_meeting = self.pool['crm.meeting']
        
        user_obj = self.pool['res.users']
        myPartnerID = user_obj.browse(cr,uid,uid,context=context).partner_id.id
        
        context_norecurrent = context.copy()
        context_norecurrent['virtual_id'] = False
        
        
        new_events_ids = crm_meeting.search(cr, uid,[('partner_ids', 'in', myPartnerID),('google_internal_event_id', '=', False),('recurrent_id', '>', 0),'|',('active', '=', False),('active', '=', True)], context=context_norecurrent)
        new_google_internal_event_id = False
        
        for event in crm_meeting.browse(cr, uid, new_events_ids, context):
            source_record = crm_meeting.browse(cr, uid ,event.recurrent_id,context)
            
            if event.recurrent_id_date and source_record.allday and source_record.google_internal_event_id:
                new_google_internal_event_id = source_record.google_internal_event_id +'_'+ event.recurrent_id_date.split(' ')[0].replace('-','') 
            elif event.recurrent_id_date and source_record.google_internal_event_id:
                new_google_internal_event_id = source_record.google_internal_event_id +'_'+ event.recurrent_id_date.replace('-','').replace(' ','T').replace(':','') + 'Z'
            
            if new_google_internal_event_id:
                crm_meeting.write(cr, uid, [event.id], {'google_internal_event_id': new_google_internal_event_id})
                #Create new event calendar with exlude recuureent_id on RecurringEventID
                
                #TODO WARNING, NEED TO CHECK THAT EVENT and ALl insatance NOT DELETE IN GMAIL BEFORE !
                self.update_recurrent_event_exclu(cr,uid,new_google_internal_event_id,source_record.google_internal_event_id,event,context=context)
            
                
    def check_and_sync(self, cr, uid, oe_event, google_event, context):
        if datetime.strptime(oe_event.oe_update_date,"%Y-%m-%d %H:%M:%S.%f") > datetime.strptime(google_event['updated'],"%Y-%m-%dT%H:%M:%S.%fz"):
            self.update_to_google(cr, uid, oe_event, google_event, context)
        elif datetime.strptime(oe_event.oe_update_date,"%Y-%m-%d %H:%M:%S.%f") < datetime.strptime(google_event['updated'],"%Y-%m-%dT%H:%M:%S.%fz"):
            self.update_from_google(cr, uid, oe_event, google_event, 'write', context)
    
    def get_sequence(self,cr,uid,instance_id,context=None):
        gs_pool = self.pool.get('google.service')
        
        params = {
                 'fields': 'sequence',
                 'access_token' : self.get_token(cr,uid,context)
                }
        
        headers = {'Content-type': 'application/json'}
            
        url = "/calendar/v3/calendars/%s/events/%s" % ('primary',instance_id) 
                
        content = gs_pool._do_request(cr, uid, url, params, headers, type='GET', context=context)
        return content.get('sequence',0)
        
    def update_events(self, cr, uid, context):
        crm_meeting = self.pool['crm.meeting']
        user_obj = self.pool['res.users']
        myPartnerID = user_obj.browse(cr,uid,uid,context=context).partner_id.id
                
        context_novirtual = context.copy()
        context_novirtual['virtual_id'] = False
        
        all_event_from_google = self.get_event_dict(cr,uid,context=context)
        all_new_event_from_google = all_event_from_google.copy()
        
        events_ids = crm_meeting.search(cr, uid,[('partner_ids', 'in', myPartnerID),('google_internal_event_id', '!=', False),('oe_update_date','!=', False),'|',('active','=',False),('active','=',True)],order='google_internal_event_id',context=context_novirtual) #MORE ACTIVE = False

        print " $ Event IN Google "
        print " $-----------------"
        for ev in all_event_from_google:
            print ' $ %s (%s) [%s]' % (all_event_from_google[ev].get('id'), all_event_from_google[ev].get('sequence'),all_event_from_google[ev].get('status'))
        print " $-----------------"
        print ""
        print " $ Event IN OPENERP "
        print " $------------------"
        for event in crm_meeting.browse(cr, uid, events_ids, context):
            print ' $ %s (%s) [%s]' % (event.google_internal_event_id, event.id,event.active)
        print " $------------------"        
        
        #For each Event in MY CALENDAR (ALL has been already create in GMAIL in the past)
        
        # WARNING, NEED TO KEEP IDS SORTED !!!
        # AS THAT, WE THREAT ALWAYS THE PARENT BEFORE THE RECURRENT
        
        for event_id in events_ids:
            event = crm_meeting.browse(cr, uid, event_id, context)
            cr.commit()
            
            # IF I HAVE BEEN DELETED FROM GOOGLE
            if event.google_internal_event_id not in all_event_from_google:
                print " __  !! OERP %s (%s) NOT IN google" % (event.google_internal_event_id,event.id) 
                
                #If m the parent, we delete all all recurrence
                if not event.recurrent_id or event.recurrent_id == 0: 
                    print " __  !! Master Event (%s) has been deleted has been delete in google" % (event.google_internal_event_id)
                    ids_deleted = crm_meeting.delete(cr,uid,event.id,context=context)
                    print "IDS DELETED : ",ids_deleted
                    for id_deleted in [x for x in ids_deleted if x in events_ids]:
                        #if id_deleted in events_ids:
                        events_ids.remove(id_deleted)
                else: # I 'm and recurrence, removed from gmail
                    print "Unlink me simply ? Where i m passed ?"
                    raise "Unlink me simply ? Where i m passed ?"
                    
                    
            else:
                print " __  OERP %s (%s) IN google" % (event.google_internal_event_id,event.id)
                
                if event.active == False:
                    if all_event_from_google[event.google_internal_event_id].get('status')!='cancelled':
                        print " __  !! Event (%s) has been removed from OPENERP" % (event.google_internal_event_id)
                        #if len(crm_meeting.get_linked_ids(cr,uid,event.id,show_unactive=False,context=context)) == 1: #IF I'M ALONE
                        if crm_meeting.count_left_instance(cr,uid,event.id,context=context)==0:    
                            print "COUNT LEFT INTANCE==="                            
                            print crm_meeting.count_left_instance(cr,uid,event.id,context=context)
                            temp = crm_meeting.get_linked_ids(cr,uid,event.id,show_unactive=False,context=context)
                            print "IDS LINKEND : IM ALONE = ",temp 
                            print "@1___DELETE FROM GOOGLE THE EVENT AND DELETE FROM OPENERP : ",event.id
                            print "delete event from google : ",event.google_internal_event_id.split('_')[0]
                            print "delete event from openerp : ",event.id
                            
                            content = self.delete_an_event(cr,uid,event.google_internal_event_id.split('_')[0],context=context_novirtual)
                            ids_deleted = crm_meeting.delete(cr,uid,event.id,context=context_novirtual)
                            print "IDS DELETED : ",ids_deleted
                            for id_deleted in ids_deleted:
                                if id_deleted in events_ids:
                                    events_ids.remove(id_deleted)
                        else :
                            print "@2___DELETE FROM GOOGLE THE EVENT AND HIDE FROM OPENERP : %s [%s]"  % (event.id,event.google_internal_event_id)
                            content = self.delete_an_event(cr,uid,event.google_internal_event_id,context=context_novirtual)
                            crm_meeting.unlink(cr,uid,event.id,unlink_level=0,context=context)
                        
                elif all_event_from_google[event.google_internal_event_id].get('status')=='cancelled':
                    print "@3___HAS BEEN REMOVED IN GOOGLE, HIDE IT IN OPENERP : ",event.id
                    crm_meeting.unlink(cr,uid,event.id,unlink_level=1,context=context) #Try to delete really in db if not recurrent
                else:
                    print "@4___NEED UPDATE : %s " % (event.id)
                    self.check_and_sync(cr, uid, event, all_event_from_google[event.google_internal_event_id], context)
                
                if event.google_internal_event_id in all_new_event_from_google:
                    del all_new_event_from_google[event.google_internal_event_id]
                     
        #FOR EACH EVENT CREATE IN GOOGLE, WE ADD THEM IN OERP
        print " $ New Event IN Google "
        print " $-----------------"
        for ev in all_new_event_from_google:
            print ' $ %s (%s) [%s]' % (all_new_event_from_google[ev].get('id'), all_new_event_from_google[ev].get('sequence'),all_new_event_from_google[ev].get('status'))
        print " $-----------------"
        print ""
        
        for new_google_event in all_new_event_from_google.values():
             if new_google_event.get('status','') == 'cancelled':
                continue
#             print "#### IN FOR #########"
             elif new_google_event.get('recurringEventId',False):
                 
                 reccurent_event = crm_meeting.search(cr, uid, [('google_internal_event_id', '=', new_google_event['recurringEventId'])])
                 
                 new_google_event_id = new_google_event['id'].split('_')[1]
                 if 'T' in new_google_event_id:
                     new_google_event_id = new_google_event_id.replace('T','')[:-1]
                 else:
                     new_google_event_id = new_google_event_id + "000000"
                 print "#############rec_event : ",reccurent_event
                 print "Google id : %s [%s]" % (new_google_event_id,new_google_event['id'])
                 for event_id in reccurent_event:
                     print "EVENT_ID = %s (%s)" % (event_id,event_id.split('-')[1])
                     
                     if isinstance(event_id, str) and len(event_id.split('-'))>1 and event_id.split('-')[1] == new_google_event_id:
                         reccurnt_event_id = int(event_id.split('-')[0].strip())
                         parent_event = crm_meeting.read(cr,uid, reccurnt_event_id, [], context)
                         parent_event['id'] = event_id
                         #recurrent update from google
                         
                         if new_google_event.get('status','') == 'cancelled':
                             print 'unlink -> cancelled in google'
                             crm_meeting.unlink(cr,uid,event_id,context)
                         else:    
                             print "DO COPY?"
                             self.update_from_google(cr, uid, parent_event, new_google_event, "copy", context)
                     else:
                             print "ELSE"
             elif new_google_event.get('recurrence',False) != False: #If was origin event from recurrent:
                 print "NEED TO CHECK IF AN INSTANCE ACTIVE..."
                 if True: #if a instance exist
                     self.update_from_google(cr, uid, False, new_google_event, "create", context)
 #               
                 else:
                     self.delete_an_event(cr, uid, new_google_event, context)
                     print ''#ELSE WE DELETE THE ORIGIN EVENT
             else :
                 print "@and not recurring event"
                 #new event from google
                 self.update_from_google(cr, uid, False, new_google_event, "create", context)
 #                 del google_events_dict[new_google_event['id']]
        return True
    
#################################        
##  MANAGE CONNEXION TO GMAIL  ##
#################################
      
    def get_token(self,cr,uid,context=None):
        current_user = self.pool.get('res.users').browse(cr,uid,uid,context=context)
            
        if datetime.strptime(current_user.google_calendar_token_validity.split('.')[0], "%Y-%m-%d %H:%M:%S") < (datetime.now() + timedelta(minutes=1)):
            print "@@ REFRESH TOKEN NEEDED !!!!"
            self.do_refresh_token(cr,uid,context=context)
            print "@@ REFRESH TOKEN DONE !!!!"
            current_user.refresh()
        else:
           print "TOKEN OK : ",datetime.strptime(current_user.google_calendar_token_validity.split('.')[0], "%Y-%m-%d %H:%M:%S"), " > ", (datetime.now() - timedelta(minutes=1))
        
        return current_user.google_calendar_token

    def do_refresh_token(self,cr,uid,context=None):
        current_user = self.pool.get('res.users').browse(cr,uid,uid,context=context)
        gs_pool = self.pool.get('google.service')
        
        refresh = current_user.google_calendar_rtoken
        all_token = gs_pool._refresh_google_token_json(cr, uid, current_user.google_calendar_rtoken,self.STR_SERVICE,context=context)
                
        vals = {}
        vals['google_%s_token_validity' % self.STR_SERVICE] = datetime.now() + timedelta(seconds=all_token.get('expires_in')) 
        vals['google_%s_token' % self.STR_SERVICE] = all_token.get('access_token')  
    
        self.pool.get('res.users').write(cr,uid,uid,vals,context=context)

    def need_authorize(self,cr,uid,context=None):
        current_user = self.pool.get('res.users').browse(cr,uid,uid,context=context)        
        return current_user.google_calendar_rtoken == False
            
    def get_calendar_scope(self,RO=False):
        readonly = RO and '.readonly' or '' 
        return 'https://www.googleapis.com/auth/calendar%s' % (readonly)        

    def authorize_google_uri(self,cr,uid,from_url='http://www.openerp.com',context=None):
        url = self.pool.get('google.service')._get_authorize_uri(cr,uid,from_url,self.STR_SERVICE,scope=self.get_calendar_scope(),context=context)
        return url        
        
    def set_all_tokens(self,cr,uid,authorization_code,context=None):
        gs_pool = self.pool.get('google.service')
        all_token = gs_pool._get_google_token_json(cr, uid, authorization_code,self.STR_SERVICE,context=context)
                
        vals = {}
        vals['google_%s_rtoken' % self.STR_SERVICE] = all_token.get('refresh_token')
        vals['google_%s_token_validity' % self.STR_SERVICE] = datetime.now() + timedelta(seconds=all_token.get('expires_in')) #NEED A CALCUL
        vals['google_%s_token' % self.STR_SERVICE] = all_token.get('access_token')           
        self.pool.get('res.users').write(cr,uid,uid,vals,context=context)
         
class res_users(osv.osv): 
    _inherit = 'res.users'
    
    _columns = {
        'google_calendar_rtoken': fields.char('Refresh Token'),
        'google_calendar_token': fields.char('User token'), 
        'google_calendar_token_validity': fields.datetime('Token Validity'),       
     }
        
#     def get_cal_token_info(self, cr, uid, partner_id=False, context=None):
#         if partner_id:
#             user = self.pool.get('res.partner').browse(cr,uid,partner_id,context=context).user_id
#         else:
#             user = self.pool.get('res.users').browse(cr,uid,uid,context=context)
#         return dict(authcode=user.google_cal_authcode, token=user.google_cal_token, validity=user.google_cal_token_validity,)


class crm_meeting(osv.osv):
    _inherit = "crm.meeting"
    
    def write(self, cr, uid, ids, vals, context=None):
        sync_fields = set(['name', 'description', 'date', 'date_closed', 'date_deadline', 'attendee_ids', 'location', 'class'])
        if (set(vals.keys()) & sync_fields) and 'oe_update_date' not in vals.keys():
            vals['oe_update_date'] = datetime.now()
        
        return super(crm_meeting, self).write(cr, uid, ids, vals, context=context)
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default['attendee_ids'] = False
        if default.get('write_type', False):
            del default['write_type']
        elif default.get('recurrent_id', False):
            default['oe_update_date'] = datetime.now()
            default['google_internal_event_id'] = False
        else:
            default['google_internal_event_id'] = False
            default['oe_update_date'] = False
        return super(crm_meeting, self).copy(cr, uid, id, default, context)
    
    _columns = {
        'google_internal_event_id': fields.char('Google Calendar Event Id', size=124),
        'oe_update_date': fields.datetime('OpenERP Update Date'),
    }
    _sql_constraints = [('google_id_uniq','unique(google_internal_event_id)', 'Google ID must be unique!')]
# If attendees are updated, we need to specify that next synchro need an action    
class calendar_attendee(osv.osv):
    _inherit = 'calendar.attendee'
    
    def write(self, cr, uid, ids, vals, context=None):
        for id in ids:
            ref = vals.get('event_id',self.browse(cr,uid,id,context=context).event_id)
            self.pool.get('crm.meeting').write(cr, uid, ref, {'oe_update_date':datetime.now()})
            
        return super(calendar_attendee, self).write(cr, uid, ids, vals, context=context)

