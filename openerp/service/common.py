# -*- coding: utf-8 -*-

import logging

import openerp.osv.orm # TODO use openerp.exceptions
import openerp.pooler
import openerp.release
import openerp.tools

import security

_logger = logging.getLogger(__name__)

RPC_VERSION_1 = {
        'server_version': openerp.release.version,
        'server_version_info': openerp.release.version_info,
        'server_serie': openerp.release.serie,
        'protocol_version': 1,
}

def dispatch(method, params):
    if method in ['login', 'about', 'timezone_get', 'get_server_environment',
                  'login_message','get_stats', 'check_connectivity',
                  'list_http_services', 'version', 'authenticate']:
        pass
    elif method in ['get_available_updates', 'get_migration_scripts', 'set_loglevel', 'get_os_time', 'get_sqlcount']:
        passwd = params[0]
        params = params[1:]
        security.check_super(passwd)
    else:
        raise Exception("Method not found: %s" % method)

    fn = globals()['exp_' + method]
    return fn(*params)

def exp_login(db, login, password):
    # TODO: legacy indirection through 'security', should use directly
    # the res.users model
    res = security.login(db, login, password)
    msg = res and 'successful login' or 'bad login or password'
    _logger.info("%s from '%s' using database '%s'", msg, login, db.lower())
    return res or False

def exp_authenticate(db, login, password, user_agent_env):
    res_users = openerp.pooler.get_pool(db).get('res.users')
    return res_users.authenticate(db, login, password, user_agent_env)

def exp_version():
    return RPC_VERSION_1

def exp_about(extended=False):
    """Return information about the OpenERP Server.

    @param extended: if True then return version info
    @return string if extended is False else tuple
    """

    info = _('See http://openerp.com')

    if extended:
        return info, openerp.release.version
    return info

def exp_timezone_get(db, login, password):
    return openerp.tools.misc.get_server_timezone()

def exp_login_message():
    return openerp.tools.config.get('login_message', False)

def exp_set_loglevel(loglevel, logger=None):
    # TODO Previously, the level was set on the now deprecated
    # `openerp.netsvc.Logger` class.
    return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
