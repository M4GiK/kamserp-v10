# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Event - Project',
    'version': '0.1',
    'category': 'Generic Modules/Association',
    'description': """Organization and management of events.

    This module allow you to create retro planning for managing your events.
""",
    'author': 'Tiny',
    'depends': ['project_retro_planning', 'event'],
    'init_xml': [],
    'update_xml': ['event_wizard.xml', 'event_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '0028125369597165',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
