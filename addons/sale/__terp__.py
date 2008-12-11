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
    "name" : "Sales Management",
    "version" : "1.0",
    "author" : "Tiny",
    "website" : "http://www.openerp.com",
    "depends" : ["product", "stock", "mrp", "process"],
    "category" : "Generic Modules/Sales & Purchases",
    "init_xml" : [],
    "demo_xml" : ["sale_demo.xml"],
    "description": """
    The base module to manage quotations and sales orders.

    * Workflow with validation steps:
        - Quotation -> Sale order -> Invoice
    * Invoicing methods:
        - Invoice on order (before or after shipping)
        - Invoice on delivery
        - Invoice on timesheets
        - Advance invoice
    * Partners preferences (shipping, invoicing, incoterm, ...)
    * Products stocks and prices
    * Delivery methods:
        - all at once, multi-parcel
        - delivery costs
    """,
    "update_xml" : [
        "security/sale_security.xml",
        "security/ir.model.access.csv",
        "sale_workflow.xml",
        "sale_sequence.xml",
        "sale_data.xml",
        "sale_wizard.xml",
        "sale_view.xml",
        "sale_report.xml",
        "sale_wizard.xml",
        "stock_view.xml",
        "process/sale_process.xml",
        "product_view.xml",
    ],
    "active": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

