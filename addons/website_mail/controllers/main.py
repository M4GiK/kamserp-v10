# -*- coding: utf-8 -*-

import openerp
from datetime import datetime
from openerp.addons.web.http import request
from openerp.addons.website import website
import werkzeug
from openerp.tools.translate import _

_months = {1:_("January"), 2:_("February"), 3:_("March"), 4:_("April"), 5:_("May"), 6:_("June"), 7:_("July"), 8:_("August"), 9:_("September"), 10:_("October"), 11:_("November"), 12:_("December")}

class website_mail(website):

    @website.route(['/blog', '/blog/<int:mail_group_id>', '/blog/<int:mail_group_id>/<int:blog_id>'], type='http', auth="admin")
    def blog(self, cr, uid, mail_group_id=None, blog_id=None, **post):
        mail_group_obj = request.registry['mail.group']
        message_obj = request.registry['mail.message']

        values = {
            'res_company': request.registry['res.company'].browse(cr, uid, 1),
            'blog_ids': None,
            'blog_id': None,
        }

        values['nav_list'] = dict()
        message_ids = mail_group_obj.get_public_message_ids(cr, uid, domain=mail_group_id and [("res_id", "=", mail_group_id)] or [])
        if message_ids:
            values['blog_ids'] = message_obj.browse(cr, uid, message_ids)
            for blog in values['blog_ids']:
                date = datetime.strptime(blog.date, "%Y-%m-%d %H:%M:%S")
                if not values['nav_list'].get(date.year):
                    values['nav_list'][date.year] = {'name': date.year, 'months': {}}
                if not values['nav_list'][date.year]['months'].get(date.month):
                    values['nav_list'][date.year]['months'][date.month] = {'name': _months[date.month], 'blog_ids': []}
                values['nav_list'][date.year]['months'][date.month]['blog_ids'].append(blog)

        if blog_id:
            values['blog_id'] = message_obj.browse(cr, uid, blog_id)
            comment_ids = [child_id.id for child_id in values['blog_id'].child_ids]
            values['comments'] = message_obj.read(cr, uid, comment_ids, ['website_published', 'author_id', 'date', 'body'])

        html = self.render(cr, uid, "website_mail.index", values)
        return html

    @website.route(['/blog/publish'], type='http', auth="admin")
    def publish(self, cr, uid, **post):
        message_id = int(post['message_id'])
        message_obj = request.registry['mail.message']

        blog = message_obj.browse(cr, uid, message_id)
        message_obj.write(cr, uid, [message_id], {'website_published': not blog.website_published})
        blog = message_obj.browse(cr, uid, message_id)

        return blog.website_published and "1" or "0"

    @website.route(['/blog/<int:mail_group_id>/<int:blog_id>/post'], type='http', auth="admin")
    def blog_post(self, cr, uid, mail_group_id=None, blog_id=None, **post):
        url = request.httprequest.host_url
        if post.get('body'):
            request.session.body = post.get('body')
            if not self.isloggued():
                return '%s/admin#action=redirect&url=%s/blog/%s/%s/post' % (url, url, mail_group_id, blog_id)

        if 'body' in request.session and request.session.body:
            request.registry['mail.group'].message_post(cr, uid, mail_group_id,
                    body=request.session.body,
                    parent_id=blog_id,
                    website_published=blog_id and True or False,
                    context={'mail_create_nosubscribe': True},
                )
            request.session.body = False

        if post.get('body'):
            return '%s/blog/%s/%s' % (url, mail_group_id, blog_id)
        else:
            return werkzeug.utils.redirect("/blog/%s/%s" % (mail_group_id, blog_id))
