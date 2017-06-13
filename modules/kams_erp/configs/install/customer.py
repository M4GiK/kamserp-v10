# -*- coding: utf-8 -*-
# @COPYRIGHT_begin
#
# Copyright [2015] Michał Szczygieł (m4gik), M4GiK Software
#
# @COPYRIGHT_end
import base64
import urllib2
from kams_erp.configs.install.configuration import InstallKamsERP_Configuration


class InstallKamsERP_Customer(InstallKamsERP_Configuration):

    def create_or_update_customer(self, order):
        """

        :param order:
        :return:
        """
        company = self.__get_company(order)
        customer = self.xml_operand.find_customer([[['email', '=', order.klient_email]]])
        if not customer:
            delivery_address = None
            if order.wysylka_ulica != '':
                delivery_address_to_insert = [{
                    'name': order.wysylka_odbiorca,
                    'phone': order.klient_telefon,
                    'street': self.__get_street_delivery(order),
                    'zip': order.klient_kod,
                    'city': order.klient_miasto,
                    'image': base64.encodestring(urllib2.urlopen(self.url + '/base/static/src/img/truck.png').read()),
                }]
                delivery_address = self.xml_operand.insert_customer(delivery_address_to_insert)

            customer_to_insert = self.__get_customer_data(order, delivery_address)
            if company:
                customer_to_insert['parent_id'] = company.get('id')

            customer = self.xml_operand.insert_customer([customer_to_insert])

        return customer

    def __get_company(self, order):
        if order.klient_firma != '':
            company = self.xml_operand.find_customer([[['name', '=', order.klient_firma]]])
            if not company:
                company_to_insert = [{
                    'name': order.klient_firma,
                    'phone': order.klient_telefon,
                    'vat': 'PL ' + order.klient_nip,
                    'street': self.__get_street(order),
                    'zip': order.klient_kod,
                    'city': order.klient_miasto,
                    'company_type': 'company',
                    'image': base64.encodestring(
                        urllib2.urlopen(self.url + '/base/static/src/img/company_image.png').read()),
                    'type': 'delivery'
                }]
                company = self.xml_operand.insert_customer(company_to_insert)

            return company

    def __get_customer_data(self, order, delivery_address=None):
        customer_data = {
            'name': order.klient_osoba,
            'email': order.klient_email,
            'phone': order.klient_telefon,
            'street': self.__get_street(order),
            'zip': order.klient_kod,
            'city': order.klient_miasto,
            'company_type': 'person',
            'image': base64.encodestring(urllib2.urlopen(self.url + '/base/static/src/img/avatar.png').read()),
        }
        if delivery_address:
            customer_data['child_ids'] = (6, 0, delivery_address.get('id'))

        return customer_data

    @staticmethod
    def __get_street(order):
        street = order.klient_ulica + ' ' + order.klient_dom
        if order.klient_mieszkanie != '':
            street = street + '/' + order.klient_mieszkanieka

        return street

    @staticmethod
    def __get_street_delivery(order):
        street = order.wysylka_ulica + ' ' + order.wysylka_dom
        if order.wysylka_mieszkanie != '':
            street = street + '/' + order.wysylka_mieszkanie

        return street
