{
'name': 'Public Partners References',
    'category': 'Website',
    'summary': 'Publish Customer References',
    'version': '1.0',
    'description': """
OpenERP Blog
============

        """,
    'author': 'OpenERP SA',
    'depends': ['website', 'website_worldmap'],
    'data': [
        'views/website_crm_partner_assign.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
}
