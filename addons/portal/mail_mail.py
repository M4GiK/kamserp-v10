# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2011 OpenERP S.A (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import SUPERUSER_ID
from openerp.osv import osv
from openerp.tools.translate import _


class mail_mail(osv.Model):
    """ Update of mail_mail class, to add the signin URL to notifications. """
    _inherit = 'mail.mail'

    def send_get_mail_body_footer(self, cr, uid, mail, partner=None, context=None):
        """ add a signin link inside the body of a mail.mail
            :param mail: mail.mail browse_record
            :param partner: browse_record of the specific recipient partner
            :return: the resulting body_html
        """
        if context is None:
            context = {}
        partner_obj = self.pool.get('res.partner')
        if partner and not partner.user_ids:
            contex_signup = dict(context, signup_valid=True)
            signup_url = partner_obj._get_signup_url_for_action(cr, SUPERUSER_ID, [partner.id],
                                                                    action='login', model=mail.model, res_id=mail.res_id,
                                                                    context=contex_signup)[partner.id]
            return _("""<small>Access your messages and documents through <a style='color:inherit' href="%s">our Customer Portal</a></small>""") % signup_url
        else:
            return super(mail_mail, self).send_get_mail_body_footer(cr, uid, mail, partner=partner, context=context)
