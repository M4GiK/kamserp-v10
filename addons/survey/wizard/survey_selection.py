# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
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

from openerp.osv import fields, osv


class survey_name_wiz(osv.osv_memory):
    _name = 'survey.name.wiz'

    _columns = {
        'survey_id': fields.many2one('survey', 'Survey', required=True, ondelete='cascade', domain=[('state', '=', 'open')]),
        'page_no': fields.integer('Page Number'),
        'note': fields.text("Description"),
        'page': fields.char('Page Position', size=12),
        'transfer': fields.boolean('Page Transfer'),
        'store_ans': fields.text('Store Answer'),
        'response': fields.char('Answer', size=16)
    }
    _defaults = {
        'page_no': -1,
        'page': 'next',
        'transfer': 1,
        'response': 0,
        'survey_id': lambda self, cr, uid, context: context.get('survey_id', False),
        'store_ans': '{}' #Setting the default pattern as '{}' as the field is of type text. The field always gets the value in dict format
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
