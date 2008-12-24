# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
    "name" : "Membership",
    "version" : "0.1",
    "author" : "Tiny",
    "category" : "Generic Modules/Association",
    "depends" : [
        "base", "product", "account","process"
        ],
    "demo_xml" : [
        #"demo_data.xml",
        "membership_demo.xml"
        ],
    "description": """
This module allows you to manage all operations for managing memberships.
It supports different kind of members:
* Free member
* Associated member (ex: a group subscribe for a membership for all
  subsidiaries)
* Paid members,
* Special member prices, ...

It is integrated with sales and accounting to allow you to automatically
invoice and send propositions for membership renewal.
    """,
    "init_xml" : [
        "membership_data.xml",
        ],
    "update_xml" : [
        "security/ir.model.access.csv",
        "membership_view.xml","membership_wizard.xml",
        "process/membership_process.xml"
        ],
    "active" : False,
    "installable" : True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

