# -*- coding: utf-8 -*-
from odoo import http


class KamsErp(http.Controller):

    @http.route('/kams_erp/', auth='public')
    def index(self, **kw):
        return http.request.render('kams_erp.index', {
            'root': '/kams_erp',
            'users': http.request.env['kams_erp.order'].search([])
        })

    @http.route('/kams_erp/<model("kams_erp.order"):user>/', auth='public')
    def object(self, user):
        return http.request.render('kams_erp.object', {
            'object': user
        })
