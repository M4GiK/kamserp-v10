import openerp.addons.website.tests.test_ui as test_ui

def load_tests(loader, base, _):
    base.addTest(test_ui.WebsiteUiSuite(test_ui.full_path(__file__,'website_sale-sale_process-test.js'),
        {'redirect': '/page/website.homepage'}, 120))
    base.addTest(test_ui.WebsiteUiSuite(test_ui.full_path(__file__,'website_sale-sale_process-test-2.js'),
        {'redirect': '/page/website.homepage'}))
    return base