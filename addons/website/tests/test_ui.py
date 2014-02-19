import os

import unittest2

import openerp.tests

relfile = lambda *args: os.path.join(os.path.dirname(__file__), *args)

inject = [
    ('openerp.website.Tour', relfile('../static/src/js/website.tour.js')),
    ('openerp.website.Tour.LoginEdit', relfile('../static/src/js/website.tour.test.admin.js')),
]

class TestUi(openerp.tests.HttpCase):
    def test_01_public_homepage(self):
        self.phantom_js("/", "console.log('ok')", "openerp.website.snippet")

    @unittest2.expectedFailure
    def test_02_public_login_logout(self):
        self.phantom_js("/", "openerp.website.Tour.run_test('login_edit')", "openerp.website.Tour", inject=inject)

    def test_03_admin_homepage(self):
        self.phantom_js("/", "console.log('ok')", "openerp.website.editor", login='admin')

    def test_04_admin_tour_banner(self):
        self.phantom_js("/", "openerp.website.Tour.run_test('banner')", "openerp.website.Tour", login='admin')

# vim:et:
