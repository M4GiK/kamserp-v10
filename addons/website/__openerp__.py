# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Builder',
    'category': 'Website',
    'sequence': 50,
    'summary': 'Build Your Enterprise Website',
    'website': 'https://www.odoo.com/page/website-builder',
    'version': '1.0',
    'description': """
Odoo Website CMS
===================

        """,
    'depends': ['web', 'web_editor', 'web_planner', 'base_setup'],
    'installable': True,
    'data': [
        'data/website_data.xml',
        'data/web_planner_data.xml',
        'security/ir.model.access.csv',
        'security/website_security.xml',

        'views/website_templates.xml',
        'views/website_navbar_templates.xml',
        'views/snippets.xml',
        'views/website_views.xml',
        'views/res_config_views.xml',
        'views/ir_actions_views.xml',

        'wizard/base_language_install_views.xml',
    ],
    'demo': [
        'data/website_demo.xml',
    ],
    'qweb': ['static/src/xml/website.backend.xml'],
    'application': True,
}
