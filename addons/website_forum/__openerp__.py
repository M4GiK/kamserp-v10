# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
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

{
    'name': 'Forum',
    'category': 'Website',
    'summary': 'Forum, FAQ, Q&A',
    'version': '1.0',
    'description': """
Ask questions, get answers, no distractions
        """,
    'author': 'OpenERP SA',
    'depends': [
        'auth_signup',
        'gamification',
        'website_mail',
        'website_partner'
    ],
    'data': [
        'data/forum_data.xml',
        'views/website_forum.xml',
        'security/ir.model.access.csv',
        'security/website_forum.xml',
        'data/forum_badges_data.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'demo': [
        'data/forum_demo.xml',
    ],
    'css': ['static/src/css/website_forum.css'],
    'installable': True,
    'application': True,
}
