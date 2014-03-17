import os

import unittest2

import openerp.tests

inject = [
    ("openerp.website.Tour", os.path.join(os.path.dirname(__file__), '../../website/static/src/js/website.tour.js')),
    ("openerp.website.Tour.ShopTest", os.path.join(os.path.dirname(__file__), "../static/src/js/website.tour.sale.js")),
]

class TestUi(openerp.tests.HttpCase):
    def test_01_admin_shop_tour(self):
        self.phantom_js("/", "openerp.website.Tour.run_test('shop')", "openerp.website.Tour.Shop", login="admin")

    def test_02_admin_checkout(self):
        self.phantom_js("/", "openerp.website.Tour.run_test('shop_buy_product')", "openerp.website.Tour", login="admin", inject=inject)

    def test_03_demo_checkout(self):
        self.phantom_js("/", "openerp.website.Tour.run_test('shop_buy_product')", "openerp.website.Tour.ShopTest", login="demo", inject=inject)

    @unittest2.expectedFailure
    def test_04_public_checkout(self):
        self.phantom_js("/", "openerp.website.Tour.run_test('shop_buy_product')", "openerp.website.Tour.ShopTest", inject=inject)
