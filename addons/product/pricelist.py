# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields, osv

#from tools.misc import currency
from _common import rounding

class price_type(osv.osv):
	"""
		The price type is used to points which field in the product form
		is a price and in which currency is this price expressed.
		When a field is a price, you can use it in pricelists to base
		sale and purchase prices based on some fields of the product.
	"""
	def _price_field_get(self, cr, uid, context={}):
		cr.execute('select name, field_description from ir_model_fields where model in (%s,%s) and ttype=%s', ('product.product', 'product.template', 'float'))
		return cr.fetchall()
	_name = "product.price.type"
	_description = "Price type"
	_columns = {
		"name" : fields.char("Price Name", size=32, required=True, translate=True) ,
		"active" : fields.boolean("Active"),
		"field" : fields.selection(_price_field_get, "Product Field", required=True),
		"currency_id" : fields.many2one('res.currency', "Currency", required=True),
	}
	_defaults = {
		"active": lambda *args: True ,
	}
price_type()

#----------------------------------------------------------
# Price lists
#----------------------------------------------------------

class product_pricelist_type(osv.osv):
	_name = "product.pricelist.type"
	_description = "Pricelist Type"
	_columns = {
		'name': fields.char('Name',size=64, required=True),
		'key': fields.char('Key', size=64, required=True),
	}
product_pricelist_type()


class product_pricelist(osv.osv):
	def _pricelist_type_get(self, cr, uid, context={}):
		cr.execute('select key,name from product_pricelist_type order by name')
		return cr.fetchall()
	_name = "product.pricelist"
	_description = "Pricelist"
	_columns = {
		'name': fields.char('Name',size=64, required=True),
		'active': fields.boolean('Active'),
		'type': fields.selection(_pricelist_type_get, 'Pricelist Type', required=True),
		'version_id': fields.one2many('product.pricelist.version', 'pricelist_id', 'Pricelist Versions'),
		'currency_id': fields.many2one('res.currency', 'Currency', required=True),
	}
	_defaults = {
		'active': lambda *a: 1,
	}

	#
	# IN:
	#   Context {
	#      'uom': Unit of Measure (Int)
	#      'partner': Partner ID (int)
	#   }
	#
	def price_get(self, cr, uid, ids, prod_id, qty, partner=None, context={}):
		if context and ('partner_id' in context):
			partner = context['partner_id']
		result = {}
		for id in ids:
			cr.execute('select * from product_pricelist_version where pricelist_id=%d and active=True order by id limit 1', (id,))
			#
			# Ajouter le test de la date du jour
			# 
			plversion = False

			# Ahahahahaha
			for plversion in cr.dictfetchall():
				break
			
			if not plversion:
				raise osv.except_osv('Warning !', 'No active version for the selected pricelist !\nPlease create or activate one.')

			cr.execute('select id,categ_id from product_template where id=(select product_tmpl_id from product_product where id=%d)', (prod_id,))
			tmpl_id,categ = cr.fetchone()
			categ_ids = []
			while categ:
				categ_ids.append(str(categ))
				cr.execute('select parent_id from product_category where id=%d', (categ,))
				categ = cr.fetchone()[0]
				if str(categ) in categ_ids:
					raise osv.except_osv('Warning !', 'Could not resolve product category, you have defined cyclic categories of products !')
			if categ_ids:
				categ_where = '(categ_id in ('+','.join(categ_ids)+'))'
			else:
				categ_where = '(categ_id is null)'

			cr.execute(
				'select i.*, pl.currency_id '
				'from product_pricelist_item as i, product_pricelist_version as v, product_pricelist as pl '
				'where (product_tmpl_id is null or product_tmpl_id=%d) '
				'and (product_id is null or product_id=%d) '
				'and ('+categ_where+' or (categ_id is null)) '
				'and price_version_id=%d '
				'and (min_quantity is null or min_quantity<=%f) '
				'and i.price_version_id=v.id and v.pricelist_id=pl.id '
				'order by sequence limit 1', (tmpl_id, prod_id, plversion['id'], qty))
			res = cr.dictfetchone()
			if res:
				if res['base'] == -1:
					if not res['base_pricelist_id']:
						price = 0.0
					else:
						price_tmp = self.price_get(cr, uid, [res['base_pricelist_id']], prod_id, qty)[res['base_pricelist_id']]
						ptype_src = self.pool.get('product.pricelist').browse(cr, uid, res['base_pricelist_id']).currency_id.id
						price = self.pool.get('res.currency').compute(cr, uid, ptype_src, res['currency_id'], price_tmp)
				elif res['base'] == -2:
					where = []
					if partner:
						where = [('name', '=', partner) ] 
					sinfo = self.pool.get('product.supplierinfo').search(cr, uid, [('product_id', '=', prod_id)]+where)
					if not sinfo:
						result[id] = 0
						continue
					cr.execute('select * from pricelist_partnerinfo where suppinfo_id in (' + ','.join(map(str, sinfo)) + ') and min_quantity<=%f order by min_quantity desc limit 1', (qty,))
					res = cr.dictfetchone()
					if res:
						result[id] = res['price']
					else:
						result[id] = 0
					continue
				else:
					price_type_o=self.pool.get('product.price.type').read(cr, uid, [ res['base'] ])[0]
					price = self.pool.get('res.currency').compute(cr, uid, price_type_o['currency_id'][0], res['currency_id'], self.pool.get('product.product').price_get(cr, uid, [prod_id], price_type_o['field'])[prod_id])
				
				price_limit = price

				price = price * (1.0-(res['price_discount'] or 0.0))
				price = rounding(price, res['price_round'])
				price += (res['price_surcharge'] or 0.0)
				if res['price_min_margin']:
					price = max(price, price_limit+res['price_min_margin'])
				if res['price_max_margin']:
					price = min(price, price_limit+res['price_max_margin'])
			else:
				# False means no valid line found ! But we may not raise an 
				# exception here because it breaks the search
				price = False
			result[id] = price
			if 'uom' in context:
				result[id] = self.pool.get('product.uom')._compute_price(cr, uid, context['uom'], result[id])
		return result
product_pricelist()

class product_pricelist_version(osv.osv):
	_name = "product.pricelist.version"
	_description = "Pricelist Version"
	_columns = {
		'pricelist_id': fields.many2one('product.pricelist', 'Price List', required=True, select=True),
		'name': fields.char('Name', size=64, required=True),
		'active': fields.boolean('Active'),
		'items_id': fields.one2many('product.pricelist.item', 'price_version_id', 'Price List Items', required=True),
		'date_start': fields.date('Start Date'),
		'date_end': fields.date('End Date')
	}
	_defaults = {
		'active': lambda *a: 1,
	}
product_pricelist_version()

class product_pricelist_item(osv.osv):
	def _price_field_get(self, cr, uid, context={}):
		cr.execute('select id,name from product_price_type where active')
		result = cr.fetchall()
		result.append((-1,'Other Pricelist'))
		result.append((-2,'Partner section of the product form'))
		return result

	_name = "product.pricelist.item"
	_description = "Pricelist item"
	_order = "sequence, min_quantity desc"
	_defaults = {
		'base': lambda *a: -1,
		'min_quantity': lambda *a: 1,
		'sequence': lambda *a: 5,
		'price_discount': lambda *a: 0,
	}
	_columns = {
		'name': fields.char('Name', size=64),
		'price_version_id': fields.many2one('product.pricelist.version', 'Price List Version', required=True, select=True),
		'product_tmpl_id': fields.many2one('product.template', 'Product Template'),
		'product_id': fields.many2one('product.product', 'Product'),
		'categ_id': fields.many2one('product.category', 'Product Category'),

		'min_quantity': fields.integer('Min. Quantity', required=True),
		'sequence': fields.integer('Sequence', required=True),
		'base': fields.selection(_price_field_get, 'Based on', required=True, size=-1),
		#'base':	fields.many2one('product.price.type', 'Based on', required=True),
		'base_pricelist_id': fields.many2one('product.pricelist', 'If Other Pricelist'),

		'price_surcharge': fields.float('Price Surcharge'),
		'price_discount': fields.float('Price Discount'),
		'price_round': fields.float('Price Rounding'),
		'price_min_margin': fields.float('Price Min. Margin'),
		'price_max_margin': fields.float('Price Max. Margin'),
	}
	def product_id_change(self, cr, uid, ids, product_id, context={}):
		if not product_id:
			return {}
		prod = self.pool.get('product.product').read(cr, uid, [product_id], ['code','name'])
		if prod[0]['code']:
			return {'value': {'name': prod[0]['code']}}
		return {}
product_pricelist_item()


