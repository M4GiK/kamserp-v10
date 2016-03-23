# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _name = 'delivery.carrier'
    _inherit = ['delivery.carrier', 'website.published.mixin']

    website_description = fields.Text(related='product_id.description_sale', string='Description for Online Quotations')
    website_published = fields.Boolean(default=False)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_delivery = fields.Monetary(
        compute='_compute_amount_delivery', digits=0,
        string='Delivery Amount',
        help="The amount without tax.", store=True, track_visibility='always')
    has_delivery = fields.Boolean(
        compute='_compute_has_delivery', string='Has delivery',
        help="Has an order line set for delivery", store=True)
    website_order_line = fields.One2many(
        'sale.order.line', 'order_id',
        string='Order Lines displayed on Website', readonly=True,
        domain=[('is_delivery', '=', False)],
        help='Order Lines to be displayed on the website. They should not be used for computation purpose.')

    @api.depends('order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
    def _compute_amount_delivery(self):
        for order in self:
            order.amount_delivery = sum(order.order_line.filtered('is_delivery').mapped('price_subtotal'))

    @api.depends('order_line.is_delivery')
    def _compute_has_delivery(self):
        for order in self:
            order.has_delivery = any(order.order_line.filtered('is_delivery'))

    def _check_carrier_quotation(self, force_carrier_id=None):
        # check to add or remove carrier_id
        if not self:
            return False
        self.ensure_one()
        DeliveryCarrier = self.env['delivery.carrier']
        if self.only_services:
            self.write({'carrier_id': None})
            self._delivery_unset()
            return True
        else:
            carrier = force_carrier_id and DeliveryCarrier.browse(force_carrier_id) or self.carrier_id
            available_carriers = self._get_delivery_methods()
            if carrier:
                if carrier not in available_carriers:
                    carrier = DeliveryCarrier
                else:
                    # set the forced carrier at the beginning of the list to be verfied first below
                    available_carriers -= carrier
                    available_carriers = carrier + available_carriers
            if force_carrier_id or not carrier or carrier not in available_carriers:
                for delivery in available_carriers:
                    verified_carrier = delivery.verify_carrier(self.partner_shipping_id)
                    if verified_carrier:
                        carrier = delivery
                        break
                self.write({'carrier_id': carrier.id})
            if carrier:
                self.delivery_set()
            else:
                self._delivery_unset()

        return bool(carrier)

    def _get_delivery_methods(self):
        """Return the available and published delivery carriers"""
        self.ensure_one()
        available_carriers = DeliveryCarrier = self.env['delivery.carrier']
        # Following loop is done to avoid displaying delivery methods who are not available for this order
        # This can surely be done in a more efficient way, but at the moment, it mimics the way it's
        # done in delivery_set method of sale.py, from delivery module
        carrier_ids = DeliveryCarrier.sudo().search(
            [('website_published', '=', True)]).ids
        for carrier_id in carrier_ids:
            carrier = DeliveryCarrier.browse(carrier_id)
            try:
                _logger.debug("Checking availability of carrier #%s" % carrier_id)
                available = carrier.with_context(order_id=self.id).read(fields=['available'])[0]['available']
                if available:
                    available_carriers += carrier
            except ValidationError as e:
                # RIM TODO: hack to remove, make available field not depend on a SOAP call to external shipping provider
                # The validation error is used in backend to display errors in fedex config, but should fail silently in frontend
                _logger.debug("Carrier #%s removed from e-commerce carrier list. %s" % (carrier_id, e))
        return available_carriers

    @api.model
    def _get_errors(self, order):
        errors = super(SaleOrder, self)._get_errors(order)
        if not order._get_delivery_methods():
            errors.append(
                (_('Sorry, we are unable to ship your order'),
                 _('No shipping method is available for your current order and shipping address. '
                   'Please contact us for more information.')))
        return errors

    @api.model
    def _get_website_data(self, order):
        """ Override to add delivery-related website data. """
        values = super(SaleOrder, self)._get_website_data(order)
        # We need a delivery only if we have stockable products
        has_stockable_products = any(order.order_line.filtered(lambda line: line.product_id.type in ['consu', 'product']))
        if not has_stockable_products:
            return values

        delivery_carriers = order._get_delivery_methods()
        values['deliveries'] = delivery_carriers.sudo().with_context(order_id=order.id)
        return values

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        """ Override to update carrier quotation if quantity changed """

        values = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)

        if add_qty or set_qty is not None:
            for sale_order in self:
                self._check_carrier_quotation()

        return values

    def _get_shipping_country(self, values):
        countries = self.env['res.country']
        states = self.env['res.country.state']
        values['shipping_countries'] = values['countries']
        values['shipping_states'] = values['states']

        delivery_carriers = self.env['delivery.carrier'].sudo().search([('website_published', '=', True)])
        for carrier in delivery_carriers:
            if not carrier.country_ids and not carrier.state_ids:
                return values
            # Authorized shipping countries
            countries |= carrier.country_ids
            # Authorized shipping countries without any state restriction
            state_countries = carrier.country_ids - carrier.state_ids.mapped('country_id')
            # Authorized shipping states + all states from shipping countries without any state restriction
            states |= carrier.state_ids | values['states'].filtered(lambda state: state.country_id in state_countries)

        values['shipping_countries'] = values['countries'] & countries
        values['shipping_states'] = values['states'] & states
        return values
