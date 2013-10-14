# -*- coding: utf-8 -*-
import base64
import cStringIO
import contextlib
import hashlib
import json
import logging
import os
import datetime
import re

from sys import maxint

import psycopg2
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
from PIL import Image

try:
    from slugify import slugify
except ImportError:
    def slugify(s, max_length=None):
        spaceless = re.sub(r'\s+', '-', s)
        specialless = re.sub(r'[^-_a-z0-9]', '', spaceless)
        return specialless[:max_length]

import openerp
from openerp.osv import fields
from openerp.addons.website.models import website
from openerp.addons.web import http
from openerp.addons.web.http import request

logger = logging.getLogger(__name__)


def auth_method_public():
    registry = openerp.modules.registry.RegistryManager.get(request.db)
    if not request.session.uid:
        request.uid = registry['website'].get_public_user().id
    else:
        request.uid = request.session.uid
http.auth_methods['public'] = auth_method_public

NOPE = object()
# PIL images have a type flag, but no MIME. Reverse type flag to MIME.
PIL_MIME_MAPPING = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'GIF': 'image/gif', }
# Completely arbitrary limits
MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT = IMAGE_LIMITS = (1024, 768)
class Website(openerp.addons.web.controllers.main.Home):
    @website.route('/', type='http', auth="public", multilang=True)
    def index(self, **kw):
        return self.page("website.homepage")

    @http.route('/admin', type='http', auth="none")
    def admin(self, *args, **kw):
        return super(Website, self).index(*args, **kw)

     # FIXME: auth, if /pagenew known anybody can create new empty page
    @website.route('/pagenew/<path:path>', type='http', auth="admin")
    def pagenew(self, path, noredirect=NOPE):
        module = 'website'
        # completely arbitrary max_length
        idname = slugify(path, max_length=50)

        request.cr.execute('SAVEPOINT pagenew')
        imd = request.registry['ir.model.data']
        view = request.registry['ir.ui.view']
        view_model, view_id = imd.get_object_reference(
            request.cr, request.uid, 'website', 'default_page')
        newview_id = view.copy(
            request.cr, request.uid, view_id, context=request.context)
        newview = view.browse(
            request.cr, request.uid, newview_id, context=request.context)
        newview.write({
            'arch': newview.arch.replace("website.default_page",
                                         "%s.%s" % (module, idname)),
            'name': path,
            'page': True,
        })
        # Fuck it, we're doing it live
        try:
            imd.create(request.cr, request.uid, {
                'name': idname,
                'module': module,
                'model': 'ir.ui.view',
                'res_id': newview_id,
                'noupdate': True
            }, context=request.context)
        except psycopg2.IntegrityError:
            logger.exception('Unable to create ir_model_data for page %s', path)
            request.cr.execute('ROLLBACK TO SAVEPOINT pagenew')
            return werkzeug.exceptions.InternalServerError()
        else:
            request.cr.execute('RELEASE SAVEPOINT pagenew')

        url = "/page/%s" % idname
        if noredirect is not NOPE:
            return werkzeug.wrappers.Response(url, mimetype='text/plain')
        return werkzeug.utils.redirect(url)

    @website.route('/website/theme_change', type='http', auth="admin")
    def theme_change(self, theme_id=False, **kwargs):
        imd = request.registry['ir.model.data']
        view = request.registry['ir.ui.view']

        view_model, view_option_id = imd.get_object_reference(
            request.cr, request.uid, 'website', 'theme')
        views = view.search(
            request.cr, request.uid, [('inherit_id', '=', view_option_id)],
            context=request.context)
        view.write(request.cr, request.uid, views, {'inherit_id': False},
                   context=request.context)

        if theme_id:
            module, xml_id = theme_id.split('.')
            view_model, view_id = imd.get_object_reference(
                request.cr, request.uid, module, xml_id)
            view.write(request.cr, request.uid, [view_id],
                       {'inherit_id': view_option_id}, context=request.context)

        return request.website.render('website.themes', {'theme_changed': True})

    @website.route(['/website/snippets'], type='json', auth="public")
    def snippets(self):
        return request.website.render('website.snippets')

    @website.route('/page/<path:path>', type='http', auth="public", multilang=True)
    def page(self, path, **kwargs):
        values = {
            'path': path,
        }
        try:
            module, xmlid = path.split('.', 1)
            IMD = request.registry.get("ir.model.data")
            obj = IMD.get_object_reference(request.cr, request.uid, module, xmlid)
            values['main_object'] = request.registry[obj[0]].browse(request.cr, request.uid, obj[1])
        except Exception:
            pass
        try:
            html = request.website.render(path, values)
        except ValueError:
            html = request.website.render('website.404', values)
        return html

    @website.route('/website/customize_template_toggle', type='json', auth='admin') # FIXME: auth
    def customize_template_set(self, view_id):
        view_obj = request.registry.get("ir.ui.view")
        view = view_obj.browse(request.cr, request.uid, int(view_id),
                               context=request.context)
        if view.inherit_id:
            value = False
        else:
            value = view.inherit_option_id and view.inherit_option_id.id or False
        view_obj.write(request.cr, request.uid, [view_id], {
            'inherit_id': value
        }, context=request.context)
        return True

    @website.route('/website/customize_template_get', type='json', auth='admin') # FIXME: auth
    def customize_template_get(self, xml_id, optional=True):
        imd = request.registry['ir.model.data']
        view_model, view_theme_id = imd.get_object_reference(
            request.cr, request.uid, 'website', 'theme')

        view = request.registry.get("ir.ui.view")
        views = view._views_get(request.cr, request.uid, xml_id, request.context)
        done = {}
        result = []
        for v in views:
            if v.inherit_option_id and v.inherit_option_id.id != view_theme_id or not optional:
                if v.inherit_option_id.id not in done:
                    result.append({
                        'name': v.inherit_option_id.name,
                        'id': v.id,
                        'header': True,
                        'active': False
                    })
                    done[v.inherit_option_id.id] = True
                result.append({
                    'name': v.name,
                    'id': v.id,
                    'header': False,
                    'active': (v.inherit_id.id == v.inherit_option_id.id) or (not optional and v.inherit_id.id)
                })
        return result

    @website.route('/website/get_view_translations', type='json', auth='admin')
    def get_view_translations(self, xml_id, lang=None):
        lang = lang or request.context.get('lang')
        views = self.customize_template_get(xml_id, optional=False)
        views_ids = [view.get('id') for view in views if view.get('active')]
        domain = [('type', '=', 'view'), ('res_id', 'in', views_ids), ('lang', '=', lang)]
        irt = request.registry.get('ir.translation')
        return irt.search_read(request.cr, request.uid, domain, ['id', 'res_id', 'value'], context=request.context)

    @website.route('/website/set_translations', type='json', auth='admin')
    def set_translations(self, data, lang):
        irt = request.registry.get('ir.translation')
        for view_id, trans in data.items():
            view_id = int(view_id)
            for t in trans:
                initial_content = t['initial_content'].strip()
                new_content = t['new_content'].strip()
                tid = t['translation_id']
                if not tid:
                    old_trans = irt.search_read(
                        request.cr, request.uid,
                        [
                            ('type', '=', 'view'),
                            ('res_id', '=', view_id),
                            ('lang', '=', lang),
                            ('src', '=', initial_content),
                        ])
                    if old_trans:
                        tid = old_trans[0]['id']
                if tid:
                    vals = {'value': new_content}
                    irt.write(request.cr, request.uid, [tid], vals)
                else:
                    new_trans = {
                        'name': 'website',
                        'res_id': view_id,
                        'lang': lang,
                        'type': 'view',
                        'source': initial_content,
                        'value': new_content,
                    }
                    irt.create(request.cr, request.uid, new_trans)
        irt._get_source.clear_cache(irt) # FIXME: find why ir.translation does not invalidate
        return True

    #  # FIXME: auth, anybody can upload an attachment if URL known/found
    @website.route('/website/attach', type='http', auth='admin')
    def attach(self, func, upload):
        req = request.httprequest
        if req.method != 'POST':
            return werkzeug.exceptions.MethodNotAllowed(valid_methods=['POST'])

        url = message = None
        try:
            attachment_id = request.registry['ir.attachment'].create(request.cr, request.uid, {
                'name': upload.filename,
                'datas': base64.encodestring(upload.read()),
                'datas_fname': upload.filename,
                'res_model': 'ir.ui.view',
            }, request.context)
            # FIXME: auth=user... no good.
            url = '/website/attachment/%d' % attachment_id
        except Exception, e:
            logger.exception("Failed to upload image to attachment")
            message = str(e)

        return """<script type='text/javascript'>
            window.parent['%s'](%s, %s);
        </script>""" % (func, json.dumps(url), json.dumps(message))

    @website.route(['/website/publish'], type='json', auth="public")
    def publish(self, id, object):
        _id = int(id)
        _object = request.registry[object]
        obj = _object.browse(request.cr, request.uid, _id)

        values = {}
        if 'website_published' in _object._all_columns:
            values['website_published'] = not obj.website_published
        if 'website_published_datetime' in _object._all_columns and values.get('website_published'):
            values['website_published_datetime'] = fields.datetime.now()
        _object.write(request.cr, request.uid, [_id],
                      values, context=request.context)

        obj = _object.browse(request.cr, request.uid, _id)
        return obj.website_published and True or False

    @website.route(['/website/kanban/'], type='http', auth="public")
    def kanban(self, **post):
        return request.website.kanban_col(**post)

    @website.route(['/robots.txt'], type='http', auth="public")
    def robots(self):
        return request.website.render('website.robots', {'url_root': request.httprequest.url_root})

    @website.route(['/sitemap.xml'], type='http', auth="public")
    def sitemap(self):
        return request.website.render('website.sitemap', {'pages': request.website.list_pages()})

class Images(http.Controller):
    @website.route('/website/image', auth="public")
    def image(self, model, id, field):
        Model = request.registry[model]

        response = werkzeug.wrappers.Response()

        id = int(id)

        ids = Model.search(request.cr, request.uid,
                           [('id', '=', id)], context=request.context)\
            or Model.search(request.cr, openerp.SUPERUSER_ID,
                            [('id', '=', id), ('website_published', '=', True)], context=request.context)

        if not ids:
            # file_open may return a StringIO. StringIO can be closed but are
            # not context managers in Python 2 though that is fixed in 3
            with contextlib.closing(openerp.tools.misc.file_open(
                    os.path.join('web', 'static', 'src', 'img', 'placeholder.png'),
                    mode='rb')) as f:
                response.set_data(f.read())
                return response

        concurrency = '__last_update'
        [record] = Model.read(request.cr, openerp.SUPERUSER_ID, [id],
                              [concurrency, field], context=request.context)

        if concurrency in record:
            server_format = openerp.tools.misc.DEFAULT_SERVER_DATETIME_FORMAT
            try:
                response.last_modified = datetime.datetime.strptime(
                    record[concurrency], server_format + '.%f')
            except ValueError:
                # just in case we have a timestamp without microseconds
                response.last_modified = datetime.datetime.strptime(
                    record[concurrency], server_format)
        # FIXME: no field in record?
        if not field in record or not record[field]:
            return response

        response.set_etag(hashlib.sha1(record[field]).hexdigest())
        response.make_conditional(request.httprequest)

        # conditional request match
        if response.status_code == 304:
            return response

        return self.set_image_data(response, record[field].decode('base64'))

    # FIXME: auth
    # FIXME: delegate to image?
    @website.route('/website/attachment/<int:id>', auth='admin')
    def attachment(self, id):
        attachment = request.registry['ir.attachment'].browse(
            request.cr, request.uid, id, request.context)

        return self.set_image_data(
            werkzeug.wrappers.Response(),
            attachment.datas.decode('base64'),
            fit=IMAGE_LIMITS,)

    def set_image_data(self, response, data, fit=(maxint, maxint)):
        """ Sets an inferred mime type on the response object, and puts the
        provided image's data in it, possibly after resizing if requested

        Returns the response object after setting its mime and content, so
        the result of ``get_final_image`` can be returned directly.
        """
        buf = cStringIO.StringIO(data)

        # FIXME: unknown format or not an image
        image = Image.open(buf)
        response.mimetype = PIL_MIME_MAPPING[image.format]

        w, h = image.size
        max_w, max_h = fit

        if w < max_w and h < max_h:
            response.set_data(data)
            return response

        image.thumbnail(fit, Image.ANTIALIAS)
        image.save(response.stream, image.format)
        return response


# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
