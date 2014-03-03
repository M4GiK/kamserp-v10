# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenERP SA (<http://www.openerp.com>).
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

import werkzeug.urls

from openerp import tools
from openerp import SUPERUSER_ID
from openerp.addons.web import http

from openerp.tools.translate import _
from datetime import datetime, timedelta
from openerp.addons.web.http import request

from dateutil.relativedelta import relativedelta
from openerp.addons.website.controllers.main import Website as controllers

controllers = controllers()

class website_forum(http.Controller):
    @http.route(['/forum/', '/forum/page/<int:page>'], type='http', auth="public", website=True, multilang=True)
    def questions(self, page=1, **searches):
        cr, uid, context = request.cr, request.uid, request.context
        forum_obj = request.registry['website.forum.post']
        user_obj = request.registry['res.users']
        domain = [('parent_id', '=', False)]
        search = searches.get('search',False)
        type = searches.get('type',False)
        if not type:
            searches['type'] = 'all'
        if search:
            domain += ['|',
                ('name', 'ilike', search),
                ('content', 'ilike', search)]
        if type == 'unanswered':
            domain += [ ('child_ids', '=', False) ]
        #TODO: update domain to show followed questions of user
        if type == 'followed':
            user = user_obj.browse(cr, uid, uid, context=context)
            domain += [ ('id', 'in', [que.id for que in user.question_ids]) ]

        step = 10
        question_count = forum_obj.search(cr, uid, domain, count=True, context=context)
        pager = request.website.pager(url="/forum/", total=question_count, page=page, step=step, scope=10)

        obj_ids = forum_obj.search(cr, uid, domain, limit=step, offset=pager['offset'], context=context)
        question_ids = forum_obj.browse(cr, uid, obj_ids, context=context)

        #If dose not get any related question then redirect to ask question form.
        values = {
            'total_questions': question_count,
            'question_ids': question_ids,
            'pager': pager,
            'searches': searches,
        }

        return request.website.render("website_forum.index", values)

    @http.route(['/forum/<model("website.forum"):forum>/faq'], type='http', auth="public", website=True, multilang=True)
    def faq(self, forum, **post):
        values = { 'searches': {}, 'forum':forum }
        return request.website.render("website_forum.faq", values)

    @http.route(['/forum/ask'], type='http', auth="public", website=True, multilang=True)
    def question_ask(self, **post):
        values = {
            'searches': {}
        }
        return request.website.render("website_forum.ask_question", values)

    @http.route(['/forum/question/<model("website.forum.post"):question>/page/<page:page>'], type='http', auth="public", website=True, multilang=True)
    def question(self, question, page, **post):
        values = {
            'question': question,
            'main_object': question
        }
        return request.website.render(page, values)

    @http.route(['/forum/question/<model("website.forum.post"):question>'], type='http', auth="public", website=True, multilang=True)
    def open_question(self, question, **post):
        answer_done = False
        for answer in question.child_ids:
            if answer.create_uid.id == request.uid:
                answer_done = True
        values = {
            'question': question,
            'main_object': question,
            'searches': post,
            'answer_done': answer_done
        }
        return request.website.render("website_forum.post_description_full", values)

    @http.route(['/forum/user/<model("res.users"):user>'], type='http', auth="public", website=True, multilang=True)
    def open_user(self, user, **post):
        answers = {}
        for answer in user.answer_ids:
            answers[answer.parent_id] = True
        values = {
            'user': user,
            'main_object': user,
            'searches': post,
            'answers': answers.keys()
        }
        return request.website.render("website_forum.user_detail_full", values)

    @http.route('/forum/question/ask/', type='http', auth="user", multilang=True, methods=['POST'], website=True)
    def register_question(self, forum_id=1, **question):
        cr, uid, context = request.cr, request.uid, request.context
        create_context = dict(context)
        new_question_id = request.registry['website.forum.post'].create(
            request.cr, request.uid, {
                #'forum_id': forum_id,
                'name': question.get('question_name'),
                'content': question.get('question_content'),
                #'tags' : question.get('question_tags'),
                'state': 'active',
                'active': True,
            }, context=create_context)
        return werkzeug.utils.redirect("/forum/question/%s" % new_question_id)

    @http.route('/forum/question/postanswer/', type='http', auth="user", multilang=True, methods=['POST'], website=True)
    def post_answer(self, post_id, forum_id=1, **question):
        # TODO: set forum on user to True
        cr, uid, context = request.cr, request.uid, request.context
        request.registry['res.users'].write(cr, uid, uid, {'forum': True}, context=context)

        create_context = dict(context)
        new_question_id = request.registry['website.forum.post'].create(
            request.cr, request.uid, {
                #'forum_id': forum_id,
                'parent_id': post_id,
                'content': question.get('answer_content'),
                'state': 'active',
                'active': True,
            }, context=create_context)
        return werkzeug.utils.redirect("/forum/question/%s" % post_id)

    @http.route(['/forum/question/editanswer'], type='http', auth="user", website=True, multilang=True)
    def edit_answer(self, post_id, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        request.registry['res.users'].write(cr, uid, uid, {'forum': True}, context=context)
        post = request.registry['website.forum.post'].browse(cr, uid, int(post_id), context=context)
        for answer in post.child_ids:
            if answer.create_uid.id == request.uid:
                post_answer = answer
        values = {
            'post': post,
            'post_answer': post_answer,
            'searches': kwargs
        }
        return request.website.render("website_forum.edit_answer", values)

    @http.route('/forum/question/saveanswer/', type='http', auth="user", multilang=True, methods=['POST'], website=True)
    def save_edited_answer(self, forum_id=1, **post):
        cr, uid, context = request.cr, request.uid, request.context
        request.registry['res.users'].write(cr, uid, uid, {'forum': True}, context=context)
        answer_id = int(post.get('answer_id'))
        new_question_id = request.registry['website.forum.post'].write( cr, uid, [answer_id], {
                'content': post.get('answer_content'),
            }, context=context)
        return werkzeug.utils.redirect("/forum/question/%s" % post.get('post_id'))

    @http.route(['/forum/tag/<model("website.forum.tag"):tag>'], type='http', auth="public", website=True, multilang=True)
    def tag_questions(self, tag, page=1, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        step = 10
        pager = request.website.pager(url="/forum/", total=len(tag.post_ids), page=page, step=step, scope=10)

        values = {
            'question_ids': tag.post_ids,
            'pager': pager,
            'searches': kwargs
        }

        return request.website.render("website_forum.index", values)

    @http.route(['/forum/tags'], type='http', auth="public", website=True, multilang=True)
    def tags(self, page=1, **searches):
        cr, uid, context = request.cr, request.uid, request.context
        tag_obj = request.registry['website.forum.tag']
        obj_ids = tag_obj.search(cr, uid, [], limit=None, context=context)
        tags = tag_obj.browse(cr, uid, obj_ids, context=context)
        values = {
            'tags': tags,
            'searches': {}
        }
        return request.website.render("website_forum.tag", values)

    @http.route(['/forum/users', '/forum/users/page/<int:page>'], type='http', auth="public", website=True, multilang=True)
    def users(self, page=1, **searches):
        cr, uid, context = request.cr, request.uid, request.context
        user_obj = request.registry['res.users']

        step = 30
        tag_count = user_obj.search(cr, uid, [('forum','=',True)], count=True, context=context)
        pager = request.website.pager(url="/forum/users/", total=tag_count, page=page, step=step, scope=30)

        obj_ids = user_obj.search(cr, uid, [('forum','=',True)], limit=step, offset=pager['offset'], context=context)
        users = user_obj.browse(cr, uid, obj_ids, context=context)
        searches['users'] = 'True'

        values = {
            'users': users,
            'pager': pager,
            'searches': searches,
        }

        return request.website.render("website_forum.users", values)
