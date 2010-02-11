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

from osv import fields, osv
from crm import crm
from caldav import caldav
class crm_meeting(osv.osv):   
    _inherit = 'crm.meeting'

    

    def export_cal(self, cr, uid, ids, context={}):
        ids = map(lambda x: base_calendar_id2real_id(x), ids)
        event_data = self.read(cr, uid, ids)
        event_obj = self.pool.get('basic.calendar.event')
        ical = event_obj.export_cal(cr, uid, event_data, context={'model': self._name})
        return ical.serialize()

    def import_cal(self, cr, uid, data, data_id=None, context={}):
        event_obj = self.pool.get('basic.calendar.event')
        vals = event_obj.import_cal(cr, uid, data, context=context)
        return self.check_import(cr, uid, vals, context=context)
    
    def check_import(self, cr, uid, vals, context={}):
        ids = []
        for val in vals:
            exists, r_id = caldav.uid2openobjectid(cr, val['id'], \
                                    self._name, val.get('recurrent_id'))
            if val.has_key('create_date'): val.pop('create_date')
            val['base_calendar_url'] = context.get('url') or ''
            val.pop('id')
            if exists and r_id:
                val.update({'recurrent_uid': exists})
                self.write(cr, uid, [r_id], val)
                ids.append(r_id)
            elif exists:
                self.write(cr, uid, [exists], val)
                ids.append(exists)
            else:
                event_id = self.create(cr, uid, val)
                ids.append(event_id)
        return ids

crm_meeting()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
