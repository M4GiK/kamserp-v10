# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Associations Management',
    'version': '0.1',
    'category': 'Specific Industry Applications',
    'description': """
This module is to configure modules related to an association.
==============================================================

It installs the profile for associations to manage events, registrations, memberships, 
membership products (schemes).
    """,
    'author': 'OpenERP SA',
    'depends': ['base_setup', 'membership', 'event'],
    'data': ['profile_association.xml'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'website': 'https://www.odoo.com'
}
