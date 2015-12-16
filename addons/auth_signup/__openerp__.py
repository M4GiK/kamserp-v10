# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Signup',
    'description': """
Allow users to sign up and reset their password
===============================================
    """,
    'category': 'Authentication',
    'auto_install': True,
    'depends': [
        'base_setup',
        'mail',
        'web',
    ],
    'data': [
        'data/auth_signup_data.xml',
        'views/res_config_views.xml',
        'views/res_users_views.xml',
        'views/auth_signup_login_templates.xml',
    ],
    'bootstrap': True,
}
