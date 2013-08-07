# -*- coding: utf-8 -*-
import base64
import json
import logging
import urllib
import cStringIO

from PIL import Image, ImageOps

import openerp
from openerp.addons.web import http
from openerp.addons.web.controllers.main import manifest_list
from openerp.addons.web.http import request
import werkzeug
import werkzeug.exceptions
import werkzeug.wrappers

logger = logging.getLogger(__name__)

class Website(openerp.addons.web.controllers.main.Home):
    @http.route('/', type='http', auth="admin")
    def index(self, **kw):
        return self.page("website.homepage")

    @http.route('/admin', type='http', auth="none")
    def admin(self, *args, **kw):
        return super(Website, self).index(*args, **kw)

    @http.route('/pagenew/<path:path>', type='http', auth="admin")
    def pagenew(self, path):
        imd = request.registry['ir.model.data']
        view = request.registry['ir.ui.view']
        view_model, view_id = imd.get_object_reference(request.cr, request.uid, 'website', 'default_page')
        newview_id = view.copy(request.cr, request.uid, view_id)
        newview = view.browse(request.cr, request.uid, newview_id, context={})
        newview.write({
            'arch': newview.arch.replace("website.default_page", path),
            'name': "page/%s" % path
        })
        if '.' in path:
            module, idname = path.split('.')
        else:
            module = False
            idname = path
        imd.create(request.cr, request.uid, {
            'name': idname,
            'module': module,
            'model': 'ir.ui.view',
            'res_id': newview_id,
            'noupdate': True
        })
        return werkzeug.utils.redirect("/page/%s" % path)

    @http.route('/page/<path:path>', type='http', auth="admin")
    def page(self, path):
        website = request.registry.get("website")
        values = website.get_rendering_context({
            'path': path
        })
        try:
            html = website.render(path, values)
        except ValueError:
            html = website.render('website.404', values)
        return html

    @http.route('/website/attach', type='http', auth='admin') # FIXME: auth
    def attach(self, CKEditorFuncNum, CKEditor, langCode, upload):
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
            window.parent.CKEDITOR.tools.callFunction(%d, %s, %s);
        </script>""" % (int(CKEditorFuncNum), json.dumps(url), json.dumps(message))

    @http.route('/website/attachment/<int:id>', type='http', auth="admin")
    def attachment(self, id):
        # FIXME: can't use Binary.image because auth=user and website attachments need to be public
        attachment = request.registry['ir.attachment'].browse(
            request.cr, request.uid, id, request.context)

        buf = cStringIO.StringIO(base64.decodestring(attachment.datas))

        image = Image.open(buf)
        image.thumbnail((1024, 768), Image.ANTIALIAS)

        response = werkzeug.wrappers.Response(status=200, mimetype={
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'GIF': 'image/gif',
        }[image.format])
        image.save(response.stream, image.format)

        return response

# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
