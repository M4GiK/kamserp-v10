{
    'name': 'Tests',
    'category': 'Hidden',
    'description': """
OpenERP Web test suite.
=======================

""",
    'version': '2.0',
    'depends': ['web'],
    'data' : [
        'views/web_tests.xml',
    ],
    'auto_install': True,
}
