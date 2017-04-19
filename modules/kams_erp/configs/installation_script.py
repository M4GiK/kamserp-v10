# -*- coding: utf-8 -*-
# @COPYRIGHT_begin
#
# Copyright [2016] Michał Szczygieł (m4gik), M4GiK Software
#
# @COPYRIGHT_end
import base64
from functools import partial
import urllib2
import time

from sqlalchemy import asc
from sqlalchemy.orm import create_session

import datetime
from datetime import date
from kams_erp.models.kamserp_config import DOMAIN, SUBIEKT_DATABASE_PASSWORD, SUBIEKT_DATABASE_ADDRESS, \
    SUBIEKT_DATABASE_DATABASE_NAME, SUBIEKT_DATABASE_PORT, SUBIEKT_DATABASE_DRIVER, SUBIEKT_DATABASE_CONNECTOR, \
    SUBIEKT_DATABASE_USER, SALES_PERSON, ODOO_DATABASE_CONNECTOR, ODOO_DATABASE_ADDRESS, ODOO_PORT, \
    SHIPMENT_PREPAYMENT_NAME, SHIPMENT_PREPAYMENT_DESCRIPTION, SHIPMENT_PREPAYMENT_PRICE, \
    SHIPMENT_PERSONAL_COLLECTION_NAME, SHIPMENT_PAYMENT_ON_DELIVERY_NAME, SHIPMENT_INPOST_NAME, \
    SHIPMENT_PERSONAL_COLLECTION_DESCRIPTION, SHIPMENT_PERSONAL_COLLECTION_PRICE, \
    SHIPMENT_PAYMENT_ON_DELIVERY_DESCRIPTION, \
    SHIPMENT_PAYMENT_ON_DELIVERY_PRICE, SHIPMENT_INPOST_PRICE, SHIPMENT_INPOST_DESCRIPTION, SHIPMENT_PREPAYMENT_COST, \
    SHIPMENT_PERSONAL_COLLECTION_COST, SHIPMENT_PAYMENT_ON_DELIVERY_COST, SHIPMENT_INPOST_COST

from kams_erp.models.kqs_images import KqsGaleriaZaczepy, KqsGaleria
from kams_erp.models.kqs_manufacturer import KqsProducenci
from kams_erp.models.kqs_order import KqsZamowieniaProdukty, KqsZamowienia
from kams_erp.models.kqs_products import KqsProdukty
from kams_erp.models.kqs_products_attribute import KqsProduktyOpcje, KqsProduktyWartosci, KqsProduktyAtrybuty
from kams_erp.models.kqs_products_category import KqsProduktyKategorie
from kams_erp.models.kqs_supplier import KqsDostawcy
from kams_erp.models.subiekt_product import TwTowar, TwStan, TwCena, get_last_buy_price
from kams_erp.utils.database_connector import DatabaseConnector
from kams_erp.utils.kams_erp_tools import clean_html
from kams_erp.utils.xml_rpc_connector import XmlRpcConnector
from kams_erp.utils.xml_rpc_operations import XmlRpcOperations, convert_decimal_to_float
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class InstallKamsERP(object):
    """
    Class resposible for install all required data.
    """

    def __init__(self):
        self.connector = XmlRpcConnector()
        self.xml_operand = XmlRpcOperations()
        self.session = create_session(bind=DatabaseConnector(dbname="kamsbhp_sklep2").get_engine())
        dbobject = DatabaseConnector(connector=SUBIEKT_DATABASE_CONNECTOR,
                                     user=SUBIEKT_DATABASE_USER,
                                     password=SUBIEKT_DATABASE_PASSWORD,
                                     host=SUBIEKT_DATABASE_ADDRESS + ':' + SUBIEKT_DATABASE_PORT,
                                     dbname=SUBIEKT_DATABASE_DATABASE_NAME,
                                     driver=SUBIEKT_DATABASE_DRIVER,
                                     charset=None)
        self.subiekt_session = create_session(bind=dbobject.get_engine())
        self.url = ODOO_DATABASE_CONNECTOR + '://' + ODOO_DATABASE_ADDRESS + ':' + ODOO_PORT

    def install_data_from_kqs(self, insert_all=False):
        """
        Install data from KQS databse to Odoo database integrated with Subiekt.
        :param insert_all: When is False, insert only product have relation in subiekt database.
        """
        self.__insert_transport_as_product()
        self.__insert_all_product_with_complete_data(insert_all)

    def __insert_or_find_category(self, category):
        odoo_category = self.xml_operand.find_category([[['kqs_original_id', '=', category.numer]]])

        if not odoo_category:
            if int(category.kat_matka) != 0:
                parent_kqs = self.session.query(KqsKategorie).filter(
                    KqsKategorie.numer == category.kat_matka).first()
                parent_odoo_id = self.xml_operand.find_category([[['name', '=', parent_kqs.nazwa]]])
                if not parent_odoo_id:
                    category_to_insert = [{
                        'name': parent_kqs.nazwa,
                        'kqs_original_id': parent_kqs.numer
                    }]
                    parent_odoo_id = self.xml_operand.insert_category(category_to_insert)

                category_to_insert = [{
                    'name': category.nazwa,
                    'parent_id': parent_odoo_id.get('id'),
                    'kqs_original_id': category.numer
                }]

                cat_id = self.xml_operand.insert_category(category_to_insert).get('id')
            else:
                category_to_insert = [{
                    'name': category.nazwa,
                    'kqs_original_id': category.numer
                }]

                cat_id = self.xml_operand.insert_category(category_to_insert).get('id')
        else:
            cat_id = odoo_category.get('id')

        return cat_id

    def __update_category(self, id_category, inserted_product):
        data_to_update = {
            'product_ids': [(4, inserted_product.get('id'))],
        }
        self.xml_operand.update_category(id_category, data_to_update)

    def __insert_or_find_manufacturer(self, manufacturers, producent_id, is_supplier):
        odoo_manufacturer = self.xml_operand.find_partner([[['kqs_original_id', '=', producent_id]]])
        if not odoo_manufacturer:
            manufacturer = next((manufacturer for manufacturer in manufacturers if manufacturer.numer == producent_id))
            try:
                image_manufacturer = "http://kams.com.pl/galerie/producenci/" + manufacturer.logo_producenta
                manufacturer_to_insert = [{
                    'name': manufacturer.nazwa,
                    'kqs_original_id': producent_id,
                    'image': base64.encodestring(urllib2.urlopen(image_manufacturer).read()),
                    'supplier': is_supplier
                }]
            except (urllib2.HTTPError, AttributeError):
                manufacturer_to_insert = [{
                    'name': manufacturer.nazwa,
                    'kqs_original_id': producent_id,
                    'image': base64.encodestring(
                        urllib2.urlopen(self.url + '/base/static/src/img/company_image.png').read()),
                    'supplier': is_supplier
                }]
            manufacturer_id = self.xml_operand.insert_partner(manufacturer_to_insert).get('id')
        else:
            manufacturer_id = odoo_manufacturer.get('id')
        return manufacturer_id

    def __insert_or_find_supplier(self, suppliers, producent_id, purchase_price):
        supplier_to_insert = [{
            'name': self.__insert_or_find_manufacturer(suppliers, producent_id, True),
            'kqs_original_id': producent_id,
            'price': purchase_price,
            'image': base64.encodestring(
                urllib2.urlopen(self.url + '/base/static/src/img/company_image.png').read()),
        }]
        supplier_id = self.xml_operand.insert_supplier(supplier_to_insert).get('id')

        return supplier_id

    def __get_image(self, product_id):
        query = self.session.query(KqsGaleriaZaczepy).filter(
            KqsGaleriaZaczepy.produkt_id == product_id).filter(
            KqsGaleriaZaczepy.kolejnosc == 1)
        image = query.first()
        if image:
            get_image = self.session.query(KqsGaleria).filter(KqsGaleria.numer == image.obraz_id).first()
        else:
            get_image = None
        return get_image

    def __insert_or_find_attributes(self, attributes, product, inserted_product):
        attributes_lst = filter(partial(self.__product_attributes, product=product), attributes)
        values_to_insert = []
        attribute_kind = None
        for attribute in attributes_lst:
            options = self.session.query(KqsProduktyOpcje).filter(
                KqsProduktyOpcje.numer == attribute.opcja_id).all()
            for option in options:
                odoo_attribute = self.xml_operand.find_attribute(
                    [[['kqs_original_id', '=', option.numer]]])
                if not odoo_attribute:
                    attribute_to_insert = [{
                        'name': option.opcja,
                        'sequence': option.kolejnosc,
                        'kqs_original_id': option.numer,
                    }]
                    odoo_attribute = self.xml_operand.insert_attribute(attribute_to_insert)
                if attribute_kind != odoo_attribute.get('id'):
                    values_to_insert = []
                attribute_kind = odoo_attribute.get('id')
                values = self.session.query(KqsProduktyWartosci).filter(
                    KqsProduktyWartosci.numer == attribute.wartosc_id).all()
                for value in values:
                    odoo_attribute_value = self.xml_operand.find_attribute_values(
                        [['&', ['name', '=', value.wartosc], ['attribute_id', 'ilike',
                                                              odoo_attribute.get('id')]]])
                    if not odoo_attribute_value:
                        attribute_value_to_insert = [{
                            'name': value.wartosc,
                            'price_extra': float(value.zmiana_wartosc),
                            'attribute_id': odoo_attribute.get('id'),
                            'kqs_original_id': value.numer,
                            'sequence': value.kolejnosc,
                        }]
                        odoo_attribute_value = self.xml_operand.insert_attribute_values(attribute_value_to_insert)

                    values_to_insert.append(odoo_attribute_value.get('id'))
                    odoo_attribute_line = self.xml_operand.find_attribute_line([['&', ['product_tmpl_id', '=',
                                                                                       inserted_product.get(
                                                                                           'product_tmpl_id')[0]],
                                                                                 ['attribute_id', 'ilike',
                                                                                  odoo_attribute.get('id')]]])

                    attribute_line_to_insert = {
                        'product_tmpl_id': inserted_product.get('product_tmpl_id')[0],
                        'attribute_id': odoo_attribute.get('id'),
                        'value_ids': [(6, 0, values_to_insert)]
                    }
                    if not odoo_attribute_line:
                        odoo_attribute_line = self.xml_operand.insert_attribute_line([attribute_line_to_insert])
                    else:
                        self.xml_operand.update_attribute_line(odoo_attribute_line.get('id'),
                                                               attribute_line_to_insert, read=False)

                    product_variants_to_update = {
                        'attribute_line_ids': [(4, odoo_attribute_line.get('id'))],
                    }

                    self.xml_operand.update_product_template(inserted_product.get('product_tmpl_id')[0],
                                                             product_variants_to_update, read=False)

    def __insert_all_product_with_complete_data(self, insert_all=False):
        # This fetching all data could be heavy, but operations have low affect on database.
        products = self.session.query(KqsProdukty).all()  # filter(KqsProdukty.numer == 64)
        categories = self.session.query(KqsKategorie).order_by(asc(KqsKategorie.numer)).all()
        kqs_products_category = self.session.query(KqsProduktyKategorie).all()
        manufacturers = self.session.query(KqsProducenci).all()
        suppliers = self.session.query(KqsDostawcy).all()
        attributes = self.session.query(KqsProduktyAtrybuty).all()

        for product in products:
            category_product = next((category_product for category_product in kqs_products_category if
                                     category_product.produkt_id == product.numer))
            if category_product is not None:
                try:
                    category = next(
                        (category for category in categories if category_product.kategoria_id == category.numer))
                except StopIteration:
                    category = None
                if insert_all:
                    if category is not None:
                        if not self.xml_operand.find_product([[['unique_product_number', '=', product.kod_produktu]]]):
                            if product.kod_kreskowy != '':
                                # Create a session for subiekt.
                                query = self.subiekt_session.query(TwTowar).filter(
                                    TwTowar.tw_PodstKodKresk == product.kod_kreskowy)
                                result = query.first()
                                if result is not None:
                                    query = self.subiekt_session.query(TwCena).filter(TwCena.tc_IdTowar == result.tw_Id)
                                    price = query.first()
                                    query = self.subiekt_session.query(TwStan).filter(TwStan.st_TowId == result.tw_Id)
                                    stan = query.first()
                                    self.subiekt_session.close()
                                    # End a session for subiekt.
                                    self.__insert_product(product, category, manufacturers, suppliers, attributes,
                                                          price.tc_CenaBrutto1, stan.st_Stan)
                            else:
                                if product:
                                    self.__insert_product(product, category, manufacturers, suppliers, attributes)
                else:
                    if category is not None and product.kod_kreskowy != '':
                        if not self.xml_operand.find_product([[['barcode', '=', product.kod_kreskowy]]]):
                            # Create a session for subiekt.
                            query = self.subiekt_session.query(TwTowar).filter(
                                TwTowar.tw_PodstKodKresk == product.kod_kreskowy)
                            result = query.first()
                            if result is not None:
                                query = self.subiekt_session.query(TwCena).filter(TwCena.tc_IdTowar == result.tw_Id)
                                price = query.first()
                                query = self.subiekt_session.query(TwStan).filter(TwStan.st_TowId == result.tw_Id)
                                stan = query.first()
                                self.subiekt_session.close()
                            else:
                                continue
                            # End a session for subiekt.

                            self.__insert_product(product, category, manufacturers, suppliers, attributes,
                                                  price.tc_CenaBrutto1, stan.st_Stan)

    def __get_shipment_xml(self, shipment_name, shipment_description, shipment_price, shipment_cost):
        odoo_category = self.xml_operand.find_category([[['name', '=', 'Transport']]])
        if not odoo_category:
            category_to_insert = [{
                'name': 'Transport',
            }]
            odoo_category = self.xml_operand.insert_category(category_to_insert)

        return {
            'name': shipment_name,
            'categ_id': odoo_category.get('id'),
            'description': shipment_description,
            'description_sale': shipment_description,
            'price': float(InstallKamsERP.__calculate_netto_price(shipment_price, 23)),
            'price_subiekt': float(InstallKamsERP.__calculate_netto_price(shipment_price, 23)),
            'standard_price': float(InstallKamsERP.__calculate_netto_price(shipment_cost, 23)),
            'image': base64.encodestring(urllib2.urlopen(self.url + '/base/static/src/img/truck.png').read()),
            'warehouse_id':
                self.connector.search('stock.warehouse', [[['name', '=', 'Kams Magazyn']]])[0],
        }

    def __insert_transport_as_product(self):
        if not self.xml_operand.find_product([[['name', '=', SHIPMENT_PREPAYMENT_NAME]]]):
            self.xml_operand.insert_products([self.__get_shipment_xml(SHIPMENT_PREPAYMENT_NAME,
                                                                      SHIPMENT_PREPAYMENT_DESCRIPTION,
                                                                      SHIPMENT_PREPAYMENT_PRICE,
                                                                      SHIPMENT_PREPAYMENT_COST)])

        if not self.xml_operand.find_product([[['name', '=', SHIPMENT_PERSONAL_COLLECTION_NAME]]]):
            self.xml_operand.insert_products([self.__get_shipment_xml(SHIPMENT_PERSONAL_COLLECTION_NAME,
                                                                      SHIPMENT_PERSONAL_COLLECTION_DESCRIPTION,
                                                                      SHIPMENT_PERSONAL_COLLECTION_PRICE,
                                                                      SHIPMENT_PERSONAL_COLLECTION_COST)])

        if not self.xml_operand.find_product([[['name', '=', SHIPMENT_PAYMENT_ON_DELIVERY_NAME]]]):
            self.xml_operand.insert_products([self.__get_shipment_xml(SHIPMENT_PAYMENT_ON_DELIVERY_NAME,
                                                                      SHIPMENT_PAYMENT_ON_DELIVERY_DESCRIPTION,
                                                                      SHIPMENT_PAYMENT_ON_DELIVERY_PRICE,
                                                                      SHIPMENT_PAYMENT_ON_DELIVERY_COST)])

        if not self.xml_operand.find_product([[['name', '=', SHIPMENT_INPOST_NAME]]]):
            self.xml_operand.insert_products([self.__get_shipment_xml(SHIPMENT_INPOST_NAME,
                                                                      SHIPMENT_INPOST_DESCRIPTION,
                                                                      SHIPMENT_INPOST_PRICE,
                                                                      SHIPMENT_INPOST_COST)])

    def __insert_kqs_product_number(self, product, inserted_product):
        unique_number_to_insert = {
            'unique_product_number': product.kod_produktu,
        }
        self.xml_operand.update_product_template(inserted_product.get('product_tmpl_id')[0],
                                                 unique_number_to_insert, read=False)

    def __insert_product(self, product, category, manufacturers, suppliers, attributes, price=0.00, stan=0):
        purchase_price = convert_decimal_to_float(
            get_last_buy_price(self.subiekt_session, product.kod_kreskowy))

        id_category = self.__insert_or_find_category(category)
        id_manufacturer = self.__insert_or_find_manufacturer(manufacturers, product.producent_id, False)
        id_supplier = self.__insert_or_find_supplier(suppliers, product.dostawca_id, purchase_price)

        # Prepare object to insert
        product_template = {
            'name': product.nazwa,
            'description': product.krotki_opis + '\n' + clean_html(product.opis),
            'price': float(self.__get_netto_price_for_product(product)),
            'price_subiekt': float(price),
            'description_sale': product.krotki_opis,
            'warehouse_id':
                self.connector.search('stock.warehouse', [[['name', '=', 'Kams Magazyn']]])[0],
            'manufacturer_id': id_manufacturer,
            'seller_ids': [(4, id_supplier)],
            'weight': convert_decimal_to_float(product.waga),
            'categ_id': id_category,
            'standard_price': purchase_price,
            'taxes_id': [(6, 0, [self.__get_tax_id(product)])],
        }
        print product.nazwa
        image_name = self.__get_image(product.numer)
        if image_name:
            image = DOMAIN + "/galerie/" + image_name.obraz[0] + "/" + image_name.obraz + ".jpg"
            # image_small = DOMAIN + "/galerie/" + image_name.obraz[0] + "/" + image_name.obraz + "_k.jpg"
            # image_medium = DOMAIN + "/galerie/" + image_name.obraz[0] + "/" + image_name.obraz + "_m.jpg"
            product_template['image'] = base64.encodestring(urllib2.urlopen(image).read())
            # product_template['image_medium'] = base64.encodestring(urllib2.urlopen(image_medium).read())
            # product_template['image_small'] = base64.encodestring(urllib2.urlopen(image_small).read())

        if product.kod_kreskowy != '':
            product_template['barcode'] = str(product.kod_kreskowy)

        inserted_product = self.xml_operand.insert_products([product_template])
        self.__insert_kqs_product_number(product, inserted_product)
        self.__insert_or_find_attributes(attributes, product, inserted_product)
        self.__update_products_variant_price(inserted_product, purchase_price, price)
        self.__update_product_quantity(inserted_product, convert_decimal_to_float(stan))

    @staticmethod
    def __product_attributes(attribute, product):
        return attribute.produkt_id == product.numer

    def __update_product_quantity(self, inserted_product, product_quantity):

        stock_quant = self.xml_operand.find_stock_quant([[['product_id', '=', inserted_product.get('id')]]])

        if not stock_quant:
            stock_to_insert = [{
                'name': "Aktualizacja Stanu",
                'product_id': self.connector.search('product.product', [
                    [['product_tmpl_id', '=', inserted_product.get('product_tmpl_id')[0]]]])[0],
                'qty': product_quantity,
                'location_id': self.connector.search('stock.location', [[['name', '=', 'WH']]])[0],
            }]
            self.xml_operand.insert_stock_quant(stock_to_insert)
        else:
            stock_to_update = {
                'qty': product_quantity
            }
            self.xml_operand.update_stock_quant(stock_quant.get('id'), stock_to_update, read=False)

    def __update_products_variant_price(self, inserted_product, purchase_price, subiekt_price):
        product_list_ids = self.connector.search('product.product', [
            [['product_tmpl_id', '=', inserted_product.get('product_tmpl_id')[0]]]])

        for product_id in product_list_ids:
            product_to_update = {
                'standard_price': purchase_price,
                'price_subiekt': float(subiekt_price),
            }
            self.xml_operand.update_product(product_id, product_to_update, read=False)

    @staticmethod
    def __calculate_netto_price(price, tax):
        return convert_decimal_to_float(price) - (
            (convert_decimal_to_float(price) * (tax / 100.0)) / ((tax / 100.0) + 1.00))

    @staticmethod
    def __get_netto_price_for_product(product):
        price = 0.00
        if product.podatek == 8:
            price = InstallKamsERP.__calculate_netto_price(product.cena, 8)

        if product.podatek == 23:
            price = InstallKamsERP.__calculate_netto_price(product.cena, 23)

        return price

    def __get_tax_id(self, product):
        if product.podatek == 8:
            tax = self.xml_operand.find_tax([[['name', '=', 'VAT-8%']]])
        else:
            tax = self.xml_operand.find_tax([[['name', '=', 'VAT-23%']]])

        return tax.get('id')

    @staticmethod
    def __get_time_before(years=0, months=0, days=0):
        year = date.today().year - years
        month = date.today().month - months
        if month <= 0:
            month += 12
            year -= 1
        day = date.today().day - days
        if day <= 0:
            day += 28
            month -= 1
        t = datetime.datetime(year, month, day, 0, 0)
        return time.mktime(t.timetuple())

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

    def __create_or_update_customer(self, order):
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

    def __get_proper_recipt(self, order):
        if order.dokument > 0:
            document_type = 'invoice'
        else:
            document_type = 'receipt'
        return document_type

    def __create_order(self, order, salesperson, customer):
        customer_order = self.xml_operand.find_order([[['unique_number', '=', order.unikalny_numer]]])
        if not customer_order:
            order_to_insert = {
                'name': order.id,
                'user_id': salesperson,
                'partner_id': customer.get('id'),
                'state': 'draft',
                'date_order': datetime.datetime.fromtimestamp(int(order.data)).strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'create_date': datetime.datetime.fromtimestamp(int(order.data)).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT),
                'note': order.uwagi,
                'unique_number': order.unikalny_numer,
                'customer_ip': order.klient_ip,
                'document_type': self.__get_proper_recipt(order)
                # 'order_line': [(6, 0, self.__create_order_line(order))]
            }

            if order.klient_nip != '':
                order_to_insert['partner_invoice_id'] = customer.get('parent_id')[0]
            if order.dokument > 0:
                order_to_insert['document_type'] = 'invoice'
            else:
                order_to_insert['document_type'] = 'receipt'

            customer_order = self.xml_operand.insert_order([order_to_insert])

        return customer_order

    def __get_product_id(self, line):
        attribute_values = []
        for attribute in line.atrybuty.split(", "):
            attribute_values.append(
                self.xml_operand.find_attribute_values([['&', ['name', '=', attribute.split(": ")[1]],
                                                         ['attribute_id', '=', self.xml_operand.find_attribute(
                                                             [[['name', '=', attribute.split(": ")[0]]]]).get(
                                                             'id')]]]).get('id'))
        if len(attribute_values) > 0:
            attribute_conditions = ['&', ['name', 'ilike', line.produkt_nazwa]]
            for attribute_value in attribute_values:
                attribute_conditions.append(['attribute_value_ids', '=', attribute_value])
            product_id = self.xml_operand.find_product([attribute_conditions]).get('id')
        else:
            product_id = self.xml_operand.find_product([[['name', '=', line.produkt_nazwa]]]).get('id')

        return product_id

    def __create_order_line(self, order, customer_order):
        fetched_order_line = self.session.query(KqsZamowieniaProdukty).filter(
            KqsZamowieniaProdukty.zamowienie_id == order.id)
        for line in fetched_order_line:
            if line:
                order_line_to_insert = {
                    'order_id': customer_order.get('id'),
                    'price_unit': float(self.__get_netto_price_for_product(line)),
                    'price_tax': convert_decimal_to_float(line.cena * line.podatek / 100),
                    'qty_to_invoice': convert_decimal_to_float(line.ilosc),
                    'discount': convert_decimal_to_float(line.rabat),
                    'product_id': self.__get_product_id(line),
                }
                self.xml_operand.insert_order_line([order_line_to_insert])

        shipment_to_insert = {
            'order_id': customer_order.get('id'),
            'price_unit': float(InstallKamsERP.__calculate_netto_price(order.przesylka_koszt_brutto, 23)),
            'product_id': self.xml_operand.find_product([[['name', '=', order.przesylka_nazwa]]]).get('id'),
            'qty_to_invoice': 1,
        }
        self.xml_operand.insert_order_line([shipment_to_insert])

    def get_orders(self):
        """ Gets orders from KQS and insert to Odoo """
        orders = self.session.query(KqsZamowienia).filter(
            KqsZamowienia.data >= self.__get_time_before(months=6)).filter(
            KqsZamowienia.id == 10651)
        salesperson = self.connector.search('res.users', [[['login', '=', SALES_PERSON]]])[0]
        for order in orders:
            customer = self.__create_or_update_customer(order)  # need update
            customer_order = self.__create_order(order, salesperson, customer)
            if customer_order:
                self.__create_order_line(order, customer_order)
            break


# InstallKamsERP().install_data_from_kqs(True)
InstallKamsERP().get_orders()
