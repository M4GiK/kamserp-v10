# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.osv import osv, fields

import logging
_logger = logging.getLogger(__name__)

class base_config_settings(osv.TransientModel):
    _inherit = 'base.config.settings'

    def get_uri(self, cr, uid, context=None):
        return "%s/auth_oauth/signin" % (self.pool['ir.config_parameter'].get_param(cr, uid, 'web.base.url', context=context))

    def _get_server_uri(self, cr, uid, ids, name, arg, context=None):
        return dict.fromkeys(ids, self.get_uri(cr, uid, context))

    _columns = {
        'auth_oauth_google_enabled' : fields.boolean('Allow users to sign in with Google'),
        'auth_oauth_google_client_id' : fields.char('Client ID'),
        'server_uri_google': fields.function(_get_server_uri, type='char', string='Server uri'),
        'auth_oauth_tutorial_enabled': fields.boolean('Show tutorial'),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(base_config_settings, self).default_get(cr, uid, fields, context=context)
        res.update(self.get_oauth_providers(cr, uid, fields, context=context))
        return res

    def get_oauth_providers(self, cr, uid, fields, context=None):
        google_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'auth_oauth', 'provider_google')[1]
        rg = self.pool.get('auth.oauth.provider').read(cr, uid, [google_id], ['enabled','client_id'], context=context)
        return {
            'auth_oauth_google_enabled': rg[0]['enabled'],
            'auth_oauth_google_client_id': rg[0]['client_id'],
            'server_uri_google': self.get_uri(cr, uid, context)
        }

    def set_oauth_providers(self, cr, uid, ids, context=None):
        google_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'auth_oauth', 'provider_google')[1]
        config = self.browse(cr, uid, ids[0], context=context)
        rg = {
            'enabled':config.auth_oauth_google_enabled,
            'client_id':config.auth_oauth_google_client_id,
        }
        self.pool.get('auth.oauth.provider').write(cr, uid, [google_id], rg)
