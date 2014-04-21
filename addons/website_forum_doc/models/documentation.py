# -*- coding: utf-8 -*-

import openerp
from openerp.osv import osv, fields

class Documentation(osv.Model):
    _name = 'forum.documentation.toc'
    _description = 'Documentation ToC'
    _inherit = ['website.seo.metadata']
    _order = "parent_left"
    _parent_order = "sequence, name"
    _parent_store = True
    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'sequence': fields.integer('Sequence'),
        'display_name': fields.function(_name_get_fnc, type="char", string='Full Name'),
        'name': fields.char('Name', required=True, translate=True),
        'introduction': fields.html('Introduction', translate=True),
        'parent_id': fields.many2one('forum.documentation.toc', 'Parent Table Of Content'),
        'child_ids': fields.one2many('forum.documentation.toc', 'parent_id', 'Children Table Of Content'),
        'parent_left': fields.integer('Left Parent', select=True),
        'parent_right': fields.integer('Right Parent', select=True),
        'post_ids': fields.one2many('forum.post', 'documentation_toc_id', 'Posts'),
        'forum_id': fields.many2one('forum.forum', 'Forum', required=True),
    }
    _constraints = [
        (osv.osv._check_recursion, 'Error ! You cannot create recursive categories.', ['parent_id'])
    ]


class DocumentationStage(osv.Model):
    _name = 'forum.documentation.stage'
    _description = 'Post Stage'
    _order = 'sequence'
    _columns = {
        'sequence': fields.integer('Sequence'),
        'name': fields.char('Stage Name', required=True, translate=True),
    }


class Post(osv.Model):
    _inherit = 'forum.post'
    _columns = {
        'documentation_toc_id': fields.many2one('forum.documentation.toc', 'Documentation ToC'),
        'documentation_stage_id': fields.many2one('forum.documentation.stage', 'Documentation Stage'),
        'color': fields.integer('Color Index')
    }

