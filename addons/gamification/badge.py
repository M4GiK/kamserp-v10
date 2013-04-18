# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.safe_eval import safe_eval

from templates import TemplateHelper
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class gamification_badge_user(osv.Model):
    """User having received a badge"""

    _name = 'gamification.badge.user'
    _description = 'Gamification user badge'

    _columns = {
        'user_id': fields.many2one('res.users', string="User", required=True),
        'badge_id': fields.many2one('gamification.badge', string='Badge', required=True),
        'comment': fields.text('Comment'),

        'badge_name': fields.related('badge_id', 'name', type="char", string="Badge Name"),
        'create_date': fields.datetime('Created', readonly=True),
        'create_uid':  fields.many2one('res.users', 'Creator', readonly=True),
    }

    _order = "create_date desc"


class gamification_badge(osv.Model):
    """Badge object that users can send and receive"""

    _name = 'gamification.badge'
    _description = 'Gamification badge'
    _inherit = ['mail.thread']

    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image)
        return result

    def _get_global_count(self, cr, uid, ids, name, args, context=None):
        """Return the number of time this badge has been granted"""
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = len(self.pool.get('gamification.badge.user').search(
                cr, uid, [('badge_id', '=', obj.id)], context=context))
            result[obj.id] = len(obj.owner_ids)
        return result

    def _get_unique_global_list(self, cr, uid, ids, name, args, context=None):
        """Return the list of unique res.users ids having received this badge"""
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            res = self.pool.get('gamification.badge.user').read_group(
                                   cr, uid, domain=[('badge_id', '=', obj.id)],
                                   fields=['badge_id', 'user_id'],
                                   groupby=['user_id'], context=context)
            result[obj.id] = [badge_user['user_id'][0] for badge_user in res]
        return result

    def _get_unique_global_count(self, cr, uid, ids, name, args, context=None):
        """Return the number of time this badge has been granted to individual users"""
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            res = self.pool.get('gamification.badge.user').read_group(
                                   cr, uid, domain=[('badge_id', '=', obj.id)],
                                   fields=['badge_id', 'user_id'],
                                   groupby=['user_id'], context=context)
            result[obj.id] = len(res)
        return result

    def _get_month_count(self, cr, uid, ids, name, args, context=None):
        """Return the number of time this badge has been granted this month"""
        result = dict.fromkeys(ids, False)
        first_month_day = date.today().replace(day=1).isoformat()
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = len(self.pool.get('gamification.badge.user').search(
                cr, uid, [('badge_id', '=', obj.id),
                          ('create_date', '>=', first_month_day)], context=context))
        return result

    def _get_global_my_count(self, cr, uid, ids, name, args, context=None):
        """Return the number of time this badge has been granted to the current user"""
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = len(self.pool.get('gamification.badge.user').search(
                    cr, uid, [('badge_id', '=', obj.id), ('user_id', '=', uid)],
                    context=context))
        return result

    def _get_month_my_count(self, cr, uid, ids, name, args, context=None):
        """Return the number of time this badge has been granted to the current user this month"""
        result = dict.fromkeys(ids, False)
        first_month_day = date.today().replace(day=1).isoformat()
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = len(self.pool.get('gamification.badge.user').search(
                cr, uid, [('badge_id', '=', obj.id), ('user_id', '=', uid),
                          ('create_date', '>=', first_month_day)], context=context))
        return result

    def _get_month_my_sent(self, cr, uid, ids, name, args, context=None):
        """Return the number of time this badge has been granted to the current user this month"""
        result = dict.fromkeys(ids, False)
        first_month_day = date.today().replace(day=1).isoformat()
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = len(self.pool.get('gamification.badge.user').search(
                cr, uid, [('badge_id', '=', obj.id), ('create_uid', '=', uid),
                          ('create_date', '>=', first_month_day)], context=context))
        return result

    def _remaining_sending_calc(self, cr, uid, ids, name, args, context=None):
        """Computes the number of badges remaining the user can send

        0 if not allowed or no remaining
        integer if limited sending
        -1 if infinite (should not be displayed)
        """
        result = dict.fromkeys(ids, False)
        for badge in self.browse(cr, uid, ids, context=context):
            if self.can_grant_badge(cr, uid, uid, badge.id, context) != 1:
                result[badge.id] = 0
            elif not badge.rule_max:
                result[badge.id] = -1
            else:
                result[badge.id] = badge.rule_max_number - badge.stat_my_monthly_sending

        return result

    _columns = {
        'name': fields.char('Badge', required=True, translate=True),
        'description': fields.text('Description'),
        'image': fields.binary("Image",
            help="This field holds the image used for the badge, limited to 256x256"),
        # image_select: selection with a on_change to fill image with predefined picts
        'rule_auth': fields.selection([
                ('everyone', 'Everyone'),
                ('users', 'A selected list of users'),
                ('having', 'People having some badges'),
                ('nobody', 'No one, assigned through challenges'),
            ],
            string="Allowed to Grant",
            help="Who can grant this badge",
            required=True),
        'rule_auth_user_ids': fields.many2many('res.users', 'rel_badge_auth_users',
            string='Authorized Users',
            help="Only these people can give this badge"),
        'rule_auth_badge_ids': fields.many2many('gamification.badge',
            'rel_badge_badge', 'badge1_id', 'badge2_id',
            string='Required Badges',
            help="Only the people having these badges can give this badge"),

        'rule_max': fields.boolean('Monthly Limited Sending',
            help="Check to set a monthly limit per person of sending this badge"),
        'rule_max_number': fields.integer('Limitation Number',
            help="The maximum number of time this badge can be sent per month per person."),
        'stat_my_monthly_sending': fields.function(_get_month_my_sent,
            type="integer",
            string='My Monthly Sending Total',
            help="The number of time the current user has sent this badge this month."),
        'remaining_sending': fields.function(_remaining_sending_calc, type='integer',
            string='Remaining Sending Allowed', help="If a maxium is set"),

        'plan_ids': fields.one2many('gamification.goal.plan', 'reward_id',
            string="Reward for Challenges"),

        'compute_code': fields.char('Compute Code',
            help="The name of the python method that will be executed to verify if a user can receive this badge."),
        'goal_type_ids': fields.many2many('gamification.goal.type',
            string='Goals Linked',
            help="The users that have succeeded theses goals will receive automatically the badge."),

        'owner_ids': fields.one2many('gamification.badge.user', 'badge_id',
            string='Owners', help='The list of instances of this badge granted to users'),
        'unique_owner_ids': fields.function(_get_unique_global_list,
            string='Unique Owners',
            help="The list of unique users having received this badge.",
            type="many2many", relation="res.users"),

        'stat_count': fields.function(_get_global_count, string='Total',
            type="integer",
            help="The number of time this badge has been received."),
        'stat_count_distinct': fields.function(_get_unique_global_count,
            type="integer",
            string='Number of users',
            help="The number of time this badge has been received by individual users."),
        'stat_this_month': fields.function(_get_month_count,
            type="integer",
            string='Monthly total',
            help="The number of time this badge has been received this month."),
        'stat_my': fields.function(_get_global_my_count, string='My Total',
            type="integer",
            help="The number of time the current user has received this badge."),
        'stat_my_this_month': fields.function(_get_month_my_count,
            type="integer",
            string='My Monthly Total',
            help="The number of time the current user has received this badge this month."),
    }

    _defaults = {
        'stat_count': 0,
        'stat_count_distinct': 0,
        'stat_this_month': 0,
        'rule_auth': 'everyone',
        'compute_code': "self.nobody(cr, uid, context)"
    }

    def send_badge(self, cr, uid, badge_id, badge_user_ids, user_from=None, context=None):
        """Send a notification to a user for receiving a badge

        Does NOT verify constrains on badge granting.
        The users are added to the owner_ids (create badge_user if needed)
        The stats counters are incremented
        :param badge_id: id of the badge to deserve
        :param badge_user_ids: list(int) of badge users that will receive the badge
        :param user_from: res.users object that has sent the badge
        """
        badge = self.browse(cr, uid, badge_id, context=context)
        template_env = TemplateHelper()

        res = None
        for badge_user in self.pool.get('gamification.badge.user').browse(cr, uid, badge_user_ids, context=context):
            values = {'badge_user': badge_user}

            if user_from:
                values['user_from'] = user_from
            else:
                values['user_from'] = False
            body_html = template_env.get_template('badge_received.mako').render(values)
            context['badge_user'] = badge_user

            res = self.message_post(cr, uid, badge.id,
                                    body=body_html,
                                    type='comment',
                                    subtype='mt_comment',
                                    context=context)

        return res

    def check_granting(self, cr, uid, user_from_id, badge_id, context=None):
        """Check the user can grant a badge and raise the appropriate exception
        if not"""
        context = context or {}
        status_code = self.can_grant_badge(cr, uid, user_from_id, badge_id, context)
        if status_code == 1:
            return True
        elif status_code == 2:
            raise osv.except_osv(_('Warning!'), _('This badge can not be sent by users.'))
        elif status_code == 3:
            raise osv.except_osv(_('Warning!'), _('You are not in the user allowed list.'))
        elif status_code == 4:
            raise osv.except_osv(_('Warning!'), _('You do not have the required badges.'))
        elif status_code == 5:
            raise osv.except_osv(_('Warning!'), _('You have already sent this badge too many time this month.'))
        else:
            _logger.exception("Unknown badge status code: %d" % int(status_code))
        return False

    def can_grant_badge(self, cr, uid, user_from_id, badge_id, context=None):
        """Check if a user can grant a badge to another user

        :param user_from_id: the id of the res.users trying to send the badge
        :param badge_id: the granted badge id
        :return: integer representing the permission.
            1: can grant
            2: nobody can send
            3: user not in the allowed list
            4: don't have the required badges
            5: user's monthly limit reached
        """
        context = context or {}
        badge = self.browse(cr, uid, badge_id, context=context)

        if badge.rule_auth == 'nobody':
            return 2

        elif badge.rule_auth == 'users':
            if user_from_id not in [user.id for user in badge.rule_auth_user_ids]:
                return 3

        elif badge.rule_auth == 'having':
            badge_users = self.pool.get('gamification.badge.user').search(
                cr, uid, [('user_id', '=', user_from_id)], context=context)

            if len(badge_users) == 0:
                # the user_from has no badges
                return 4

            owners = [owner.id for owner in badge.owner_ids]
            granted = False
            for badge_user in badge_users:
                if badge_user in owners:
                    granted = True
                    break
            if not granted:
                return 4

        # else badge.rule_auth == 'everyone' -> no check

        if badge.rule_max and badge.stat_my_monthly_sending >= badge.rule_max_number:
            # sent the maximum number of time this month
            return 5

        return 1


class grant_badge_wizard(osv.TransientModel):
    _name = 'gamification.badge.user.wizard'
    _columns = {
        'user_id': fields.many2one("res.users", string='User', required=True),
        'badge_id': fields.many2one("gamification.badge", string='Badge',  required=True),
        'comment': fields.text('Comment'),
    }

    def action_grant_badge(self, cr, uid, ids, context=None):
        """Wizard action for sending a badge to a chosen user"""
        if context is None:
            context = {}

        badge_obj = self.pool.get('gamification.badge')
        badge_user_obj = self.pool.get('gamification.badge.user')

        for wiz in self.browse(cr, uid, ids, context=context):
            if uid == wiz.user_id.id:
                raise osv.except_osv(_('Warning!'), _('You can not send a badge to yourself'))

            if badge_obj.check_granting(cr, uid,
                                         user_from_id=uid,
                                         badge_id=wiz.badge_id.id,
                                         context=context):
                values = {
                    'user_id': wiz.user_id.id,
                    'badge_id': wiz.badge_id.id,
                    'comment': wiz.comment,
                }
                badge_user = badge_user_obj.create(cr, uid, values, context=context)

                user_from = self.pool.get('res.users').browse(cr, uid, uid, context=context)

                badge_obj.send_badge(cr, uid, wiz.badge_id.id, [badge_user], user_from=user_from, context=context)

        return {}
