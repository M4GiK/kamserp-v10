# -*- coding: utf-8 -*-

from openerp.osv import osv, fields

# defined for access rules
class hr_job(osv.osv):
    _inherit = "hr.job"
    _columns = {
        'write_date': fields.datetime('Update Date', readonly=True),
    }
