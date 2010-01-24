# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

class hr_installer(osv.osv_memory):
    _name = 'hr.installer'
    _inherit = 'res.config.installer'

    _columns = {
        # Human Resources Management
        'hr_holidays':fields.boolean('Holidays / Leaves Management',
            help="Tracks employee leaves allocations, requests and planning."
                 "\n\nCan also plug into OpenERP's agendas and calendars "
                 "applications in order to display accepted leaves requests on"
                 " OpenERP's calendars."),
        'hr_expense':fields.boolean('Expenses',
            help="Tracks and manages employee expenses, and can "
                 "automatically re-invoice clients if the expenses are "
                 "project-related."),
        'hr_jobs':fields.boolean('Recruitment Process',
            help="Helps you manage and streamline your recruitment process."),
        'hr_timesheet_sheet':fields.boolean('Timesheets',
            help="Tracks and helps employees encode and validate timesheets "
                 "and attendance."),
        'hr_contract':fields.boolean("Employee's Contracts",
            help="Extends employee profiles to help manage their contracts."),
        'hr_evaluation':fields.boolean('Periodic Evaluations',
            help="Lets you create and manage the periodic evaluation and "
                 "performance review of employees."),
        'hr_attendance':fields.boolean('Attendances (Sign In/Out)',
            help="Simplifies the management of employee attendances."),
        }
    _defaults = {
        'hr_holidays': True,
        'hr_expense': True,
        }
hr_installer()
