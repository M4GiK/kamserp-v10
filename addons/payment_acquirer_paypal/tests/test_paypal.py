# -*- coding: utf-8 -*-

from openerp.addons.payment_acquirer.models.payment_acquirer import ValidationError
from openerp.addons.payment_acquirer.tests.common import PaymentAcquirerCommon
from openerp.addons.payment_acquirer_paypal.controllers.main import PaypalController
from openerp.osv.orm import except_orm
from openerp.tools import mute_logger

from lxml import objectify
import urlparse


class PaypalCommon(PaymentAcquirerCommon):

    def setUp(self):
        super(PaypalCommon, self).setUp()
        cr, uid = self.cr, self.uid

        self.base_url = self.registry('ir.config_parameter').get_param(cr, uid, 'web.base.url')
        model, self.paypal_view_id = self.registry('ir.model.data').get_object_reference(cr, uid, 'payment_acquirer_paypal', 'paypal_acquirer_button')

        # create a new ogone account
        self.paypal_id = self.payment_acquirer.create(
            cr, uid, {
                'name': 'paypal',
                'env': 'test',
                'view_template_id': self.paypal_view_id,
                'paypal_email_id': 'tde+paypal-facilitator@openerp.com',
                'paypal_username': 'tde+paypal-facilitator_api1.openerp.com',
                'paypal_api_enabled': True,
                'paypal_api_username': 'AYf_uBATwly1C72DqE2njwDHmZI25UHcZMwvgvgICLkeQEgutvrhrg6y3KhZ',
                'paypal_api_password': 'EJSDgxC_LuZ9oeG-Ud_oozfiDqqN3mUVLMmzPK71IZA3TM4taicUY2uaJYU1',
            })
        # tde+seller@openerp.com - tde+buyer@openerp.com - tde+buyer-it@openerp.com

        # some CC
        self.amex = (('378282246310005', '123'), ('371449635398431', '123'))
        self.amex_corporate = (('378734493671000', '123'))
        self.autralian_bankcard = (('5610591081018250', '123'))
        self.dinersclub = (('30569309025904', '123'), ('38520000023237', '123'))
        self.discover = (('6011111111111117', '123'), ('6011000990139424', '123'))
        self.jcb = (('3530111333300000', '123'), ('3566002020360505', '123'))
        self.mastercard = (('5555555555554444', '123'), ('5105105105105100', '123'))
        self.visa = (('4111111111111111', '123'), ('4012888888881881', '123'), ('4222222222222', '123'))
        self.dankord_pbs = (('76009244561', '123'), ('5019717010103742', '123'))
        self.switch_polo = (('6331101999990016', '123'))


class PaypalServer2Server(PaypalCommon):

    def test_00(self):
        cr, uid, context = self.cr, self.uid, {}

        res = self.payment_acquirer._paypal_s2s_get_access_token(cr, uid, [self.paypal_id], context=context)
        self.assertTrue(res[self.paypal_id] is not False, 'paypal: did not generate access token')

        tx_id = self.payment_transaction.s2s_create(
            cr, uid, {
                'amount': 0.01,
                'acquirer_id': self.paypal_id,
                'currency_id': self.currency_euro_id,
                'reference': 'test_reference',
                'partner_id': self.buyer_id,
            }, {
                'number': self.visa[0][0],
                'cvc': self.visa[0][1],
                'brand': 'visa',
                'expiry_mm': 9,
                'expiry_yy': 2015,
            }, context=context
        )

        tx = self.payment_transaction.browse(cr, uid, tx_id, context=context)
        print tx.paypal_txn_id
        self.payment_transaction.s2s_get_tx_status(cr, uid, tx_id, context=context)
# {
#     "id":"PAY-2LL14628DB722091TKKHXZHQ",
#     "create_time":"2013-11-22T15:47:42Z",
#     "update_time":"2013-11-22T15:48:05Z",
#     "state":"pending",
#     "intent":"sale",
#     "payer": {
#         "payment_method":"credit_card",
#         "funding_instruments": [{
#             "credit_card": {
#                 "type":"visa",
#                 "number":"xxxxxxxxxxxx1111",
#                 "expire_month":"9",
#                 "expire_year":"2015",
#                 "first_name":"Norbert Buyer",
#                 "last_name":"Norbert Buyer",
#                 "billing_address": {
#                     "line1":"Huge Street 2/543",
#                     "city":"Sin City",
#                     "postal_code":"1000",
#                     "country_code":"BE"
#                 }
#             }
#         }]
#     },
#     "transactions": [{
#         "amount": {
#             "total":"0.01",
#             "currency":"EUR",
#             "details": {
#                 "subtotal":"0.01"
#             }
#         },
#         "related_resources": [{
#             "sale": {
#                 "id":"4KU52719R3958614J",
#                 "create_time":"2013-11-22T15:47:42Z",
#                 "update_time":"2013-11-22T15:48:05Z",
#                 "state":"pending",
#                 "amount": {
#                     "total":"0.01",
#                     "currency":"EUR"
#                 },
#                 "pending_reason":"multicurrency",
#                 "parent_payment":"PAY-2LL14628DB722091TKKHXZHQ",
#                 "links": [{
#                     "href":"https://api.sandbox.paypal.com/v1/payments/sale/4KU52719R3958614J",
#                     "rel":"self",
#                     "method":"GET"
#                     },{
#                     "href":"https://api.sandbox.paypal.com/v1/payments/sale/4KU52719R3958614J/refund",
#                     "rel":"refund",
#                     "method":"POST"
#                     },{
#                     "href":"https://api.sandbox.paypal.com/v1/payments/payment/PAY-2LL14628DB722091TKKHXZHQ",
#                     "rel":"parent_payment",
#                     "method":"GET"
#                     }]
#                 }
#             }]
#         }],
#     "links": [{
#         "href":"https://api.sandbox.paypal.com/v1/payments/payment/PAY-2LL14628DB722091TKKHXZHQ",
#         "rel":"self",
#         "method":"GET"
#     }]
# }


class PaypalForm(PaypalCommon):

    def test_00_paypal_acquirer(self):
        cr, uid, context = self.cr, self.uid, {}
        # forgot some mandatory fields: should crash
        with self.assertRaises(except_orm):
            self.payment_acquirer.create(
                cr, uid, {
                    'name': 'paypal',
                    'env': 'test',
                    'view_template_id': self.paypal_view_id,
                    'paypal_email_id': 'tde+paypal-facilitator@openerp.com',
                }, context=context)

        paypal = self.payment_acquirer.browse(self.cr, self.uid, self.paypal_id, None)
        self.assertEqual(paypal.env, 'test', 'test without test env')

    def test_10_paypal_form_render(self):
        cr, uid, context = self.cr, self.uid, {}

        # ----------------------------------------
        # Test: button direct rendering
        # ----------------------------------------

        form_values = {
            'cmd': '_xclick',
            'business': 'tde+paypal-facilitator@openerp.com',
            'item_name': 'test_ref0',
            'item_number': 'test_ref0',
            'first_name': 'Buyer',
            'last_name': 'Norbert',
            'amount': '0.01',
            'currency_code': 'EUR',
            'address1': 'Huge Street 2/543',
            'city': 'Sin City',
            'zip': '1000',
            'country': 'Belgium',
            'email': 'norbert.buyer@example.com',
            'return': '%s' % urlparse.urljoin(self.base_url, PaypalController._return_url),
            'notify_url': '%s' % urlparse.urljoin(self.base_url, PaypalController._notify_url),
            'cancel_return': '%s' % urlparse.urljoin(self.base_url, PaypalController._cancel_url),
        }

        # render the button
        res = self.payment_acquirer.render(
            cr, uid, self.paypal_id,
            'test_ref0', 0.01, self.currency_euro,
            partner_id=None,
            partner_values=self.buyer_values,
            context=context)

        # check form result
        tree = objectify.fromstring(res)
        self.assertEqual(tree.get('action'), 'https://www.sandbox.paypal.com/cgi-bin/webscr', 'paypal: wrong form POST url')
        for form_input in tree.input:
            if form_input.get('name') in ['submit']:
                continue
            self.assertEqual(
                form_input.get('value'),
                form_values[form_input.get('name')],
                'paypal: wrong value for form: received %s instead of %s' % (form_input.get('value'), form_values[form_input.get('name')])
            )

    @mute_logger('openerp.addons.payment_acquirer_paypal.models.paypal', 'ValidationError')
    def test_20_paypal_form_management(self):
        cr, uid, context = self.cr, self.uid, {}

        # typical data posted by paypal after client has successfully paid
        paypal_post_data = {
            'protection_eligibility': u'Ineligible',
            'last_name': u'Poilu',
            'txn_id': u'08D73520KX778924N',
            'receiver_email': u'tde+paypal-facilitator@openerp.com',
            'payment_status': u'Pending',
            'payment_gross': u'',
            'tax': u'0.00',
            'residence_country': u'FR',
            'address_state': u'Alsace',
            'payer_status': u'verified',
            'txn_type': u'web_accept',
            'address_street': u'Av. de la Pelouse, 87648672 Mayet',
            'handling_amount': u'0.00',
            'payment_date': u'03:21:19 Nov 18, 2013 PST',
            'first_name': u'Norbert',
            'item_name': u'test_ref_2',
            'address_country': u'France',
            'charset': u'windows-1252',
            'custom': u'',
            'notify_version': u'3.7',
            'address_name': u'Norbert Poilu',
            'pending_reason': u'multi_currency',
            'item_number': u'test_ref_2',
            'receiver_id': u'DEG7Z7MYGT6QA',
            'transaction_subject': u'',
            'business': u'tde+paypal-facilitator@openerp.com',
            'test_ipn': u'1',
            'payer_id': u'VTDKRZQSAHYPS',
            'verify_sign': u'An5ns1Kso7MWUdW4ErQKJJJ4qi4-AVoiUf-3478q3vrSmqh08IouiYpM',
            'address_zip': u'75002',
            'address_country_code': u'FR',
            'address_city': u'Paris',
            'address_status': u'unconfirmed',
            'mc_currency': u'EUR',
            'shipping': u'0.00',
            'payer_email': u'tde+buyer@openerp.com',
            'payment_type': u'instant',
            'mc_gross': u'1.95',
            'ipn_track_id': u'866df2ccd444b',
            'quantity': u'1'
        }

        # should raise error about unknown tx
        with self.assertRaises(ValidationError):
            self.payment_transaction.form_feedback(cr, uid, paypal_post_data, 'paypal', context=context)

        # create tx
        tx_id = self.payment_transaction.create(
            cr, uid, {
                'amount': 1.95,
                'acquirer_id': self.paypal_id,
                'currency_id': self.currency_euro_id,
                'reference': 'test_ref_2',
                'partner_name': 'Norbert Buyer',
            }, context=context
        )
        # validate it
        self.payment_transaction.form_feedback(cr, uid, paypal_post_data, 'paypal', context=context)
        # check
        tx = self.payment_transaction.browse(cr, uid, tx_id, context=context)
        self.assertEqual(tx.state, 'pending', 'paypal: wrong state after receiving a valid pending notification')
        self.assertEqual(tx.state_message, 'multi_currency', 'paypal: wrong state message after receiving a valid pending notification')
        self.assertEqual(tx.paypal_txn_id, '08D73520KX778924N', 'paypal: wrong txn_id after receiving a valid pending notification')
        self.assertFalse(tx.date_validate, 'paypal: validation date should not be updated whenr receiving pending notification')

        # update tx
        self.payment_transaction.write(cr, uid, [tx_id], {
            'state': 'draft',
            'paypal_txn_id': False,
        }, context=context)
        # update notification from paypal
        paypal_post_data['payment_status'] = 'Completed'
        # validate it
        self.payment_transaction.form_feedback(cr, uid, paypal_post_data, 'paypal', context=context)
        # check
        tx = self.payment_transaction.browse(cr, uid, tx_id, context=context)
        self.assertEqual(tx.state, 'done', 'paypal: wrong state after receiving a valid pending notification')
        self.assertEqual(tx.paypal_txn_id, '08D73520KX778924N', 'paypal: wrong txn_id after receiving a valid pending notification')
        self.assertEqual(tx.date_validate, '2013-11-18 03:21:19', 'paypal: wrong validation date')
