# -*- coding: utf-8 -*-

{
    'name': 'Advanced Events',
    'category': 'Website',
    'summary': 'Sponsors, Tracks, Agenda, Event News',
    'version': '1.0',
    'description': """
Online Events
=============

        """,
    'author': 'OpenERP SA',
    'depends': ['website_event', 'website_blog'],
    'data': [
        'data/event_data.xml',
        'views/website_event.xml',
        'views/event_backend.xml',
        'security/ir.model.access.csv',
        'security/event.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'demo': [
        'data/event_demo.xml'
    ],
    'installable': True,
}
