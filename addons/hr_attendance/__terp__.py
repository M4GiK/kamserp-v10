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
    "name" : "Attendances Of Employees",
    "version" : "1.0",
    "author" : "Tiny",
    "category" : "Generic Modules/Human Resources",
    "description": "This module aims to manage employee's attendances.",
    "depends" : ["base","hr",],
    "demo_xml" : ["hr_attendance_demo.xml"],
    "update_xml" : [
       "security/hr_security.xml",
       "hr_attendance_view.xml",
       "hr_attendance_wizard.xml",
       "hr_attendance_report.xml",
       "security/ir.model.access.csv"
    ],
    "active": False,
    "installable": True,
}
