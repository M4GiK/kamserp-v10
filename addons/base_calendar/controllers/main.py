import simplejson
import urllib
import openerp
import openerp.addons.web.http as http
from openerp.addons.web.http import request
import openerp.addons.web.controllers.main as webmain
import json
from openerp.addons.web.http import SessionExpiredException
from werkzeug.exceptions import BadRequest

class meetting_invitation(http.Controller):

    def check_security(self, db, token):
        registry = openerp.modules.registry.RegistryManager.get(db)
        attendee_pool = registry.get('calendar.attendee')
        error_message = False
        with registry.cursor() as cr:
            attendee_id = attendee_pool.search(cr, openerp.SUPERUSER_ID, [('access_token','=',token)])
            if not attendee_id:
                # if token is not match
                error_message = """Invalid Invitation Token."""
            elif request.session.uid and request.session.login != 'anonymous':
                # if valid session but user is not match
                attendee = attendee_pool.browse(cr, openerp.SUPERUSER_ID, attendee_id[0])
                user = registry.get('res.users').browse(cr, openerp.SUPERUSER_ID, request.session.uid)
                if attendee.user_id.id != user.id:
                    error_message  = """Invitation cannot be forwarded via email. This event/meeting belongs to %s and you are logged in as %s. Please ask organizer to add you.""" % (attendee.email, user.email)
        if error_message:
            raise BadRequest(error_message)
        return True

    @http.route('/meeting_invitation/accept', type='http', auth="none")
    def accept(self, db, token, action, id):
        # http://hostname:8069/meeting_invitation/accept?db=#token=&action=&id=
        self.check_security(db, token)
        registry = openerp.modules.registry.RegistryManager.get(db)
        attendee_pool = registry.get('calendar.attendee')
        with registry.cursor() as cr:
            attendee_id = attendee_pool.search(cr, openerp.SUPERUSER_ID, [('access_token','=',token),('state','!=', 'accepted')])
            if attendee_id:
                attendee_pool.do_accept(cr, openerp.SUPERUSER_ID, attendee_id)
        return self.view(db, token, action, id, view='form')

    @http.route('/meeting_invitation/decline', type='http', auth="none")
    def declined(self, db, token, action, id):
        # http://hostname:8069/meeting_invitation/decline?db=#token=&action=&id=
        self.check_security(db, token)
        registry = openerp.modules.registry.RegistryManager.get(db)
        attendee_pool = registry.get('calendar.attendee')
        with registry.cursor() as cr:
            attendee_id = attendee_pool.search(cr, openerp.SUPERUSER_ID, [('access_token','=',token),('state','!=', 'declined')])
            if attendee_id:
                attendee_pool.do_decline(cr, openerp.SUPERUSER_ID, attendee_id)
        return self.view(db, token, action, id, view='form')

    @http.route('/meeting_invitation/view', type='http', auth="none")
    def view(self, db, token, action, id, view='calendar'):
        # http://hostname:8069/meeting_invitation/view?db=#token=&action=&id=
        self.check_security(db, token)
        registry = openerp.modules.registry.RegistryManager.get(db)
        meeting_pool = registry.get('crm.meeting')
        attendee_pool = registry.get('calendar.attendee')
        with registry.cursor() as cr:
            attendee_data = meeting_pool.get_attendee(cr, openerp.SUPERUSER_ID, id);
            attendee = attendee_pool.search_read(cr, openerp.SUPERUSER_ID, [('access_token','=',token)],[])
        if attendee:
            attendee_data['current_attendee'] = attendee[0]
        js = "\n        ".join('<script type="text/javascript" src="%s"></script>' % i for i in webmain.manifest_list('js', db=db))
        css = "\n        ".join('<link rel="stylesheet" href="%s">' % i for i in webmain.manifest_list('css',db=db))
        return webmain.html_template % {
            'js': js,
            'css': css,
            'modules': simplejson.dumps(webmain.module_boot(db)),
            'init': "s.base_calendar.event('%s', '%s', '%s', '%s' , '%s');" % (db, action, id, view, json.dumps(attendee_data)),
        }


