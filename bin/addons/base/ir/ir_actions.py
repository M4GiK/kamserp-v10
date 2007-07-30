##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

from osv import fields,osv

class actions(osv.osv):
	_name = 'ir.actions.actions'
	_table = 'ir_actions'
	_columns = {
		'name': fields.char('Action Name', required=True, size=64),
		'type': fields.char('Action Type', required=True, size=32),
		'usage': fields.char('Action Usage', size=32)
	}
	_defaults = {
		'usage': lambda *a: False,
	}
actions()

class act_execute(osv.osv):
	_name = 'ir.actions.execute'
	_table = 'ir_act_execute'
	_sequence = 'ir_actions_id_seq'
	_columns = {
		'name': fields.char('name', size=64, required=True, translate=True),
		'type': fields.char('type', size=32, required=True),
		'func_name': fields.char('Function Name', size=64, required=True),
		'func_arg': fields.char('Function Argument', size=64),
		'usage': fields.char('Action Usage', size=32)
	}
act_execute()

class group(osv.osv):
	_name = 'ir.actions.group'
	_table = 'ir_act_group'
	_sequence = 'ir_actions_id_seq'
	_columns = {
		'name': fields.char('Group Name', size=64, required=True),
		'type': fields.char('Action Type', size=32, required=True),
		'exec_type': fields.char('Execution sequence', size=64, required=True),
		'usage': fields.char('Action Usage', size=32)
	}
group()

class report_custom(osv.osv):
	_name = 'ir.actions.report.custom'
	_table = 'ir_act_report_custom'
	_sequence = 'ir_actions_id_seq'
	_columns = {
		'name': fields.char('Report Name', size=64, required=True, translate=True),
		'type': fields.char('Report Type', size=32, required=True),
		'model':fields.char('Model', size=64, required=True),
		'report_id': fields.integer('Report Ref.', required=True),
		'usage': fields.char('Action Usage', size=32),
		'multi': fields.boolean('On multiple doc.', help="If set to true, the action will not be displayed on the right toolbar of a form views.")
	}
	_defaults = {
		'multi': lambda *a: False,
	}
report_custom()

class report_xml(osv.osv):
	_name = 'ir.actions.report.xml'
	_table = 'ir_act_report_xml'
	_sequence = 'ir_actions_id_seq'
	_columns = {
		'name': fields.char('Name', size=64, required=True, translate=True),
		'type': fields.char('Report Type', size=32, required=True),
		'model': fields.char('Model', size=64, required=True),
		'report_name': fields.char('Internal Name', size=64, required=True),
		'report_xsl': fields.char('XSL path', size=256),
		'report_xml': fields.char('XML path', size=256),
		'report_rml': fields.char('RML path', size=256, help="The .rml path of the file or NULL if the content is in report_rml_content"),
		'report_sxw_content': fields.binary('SXW content'),
		'report_rml_content': fields.binary('RML content'),
		'auto': fields.boolean('Automatic XSL:RML', required=True),
		'usage': fields.char('Action Usage', size=32),
		'header': fields.boolean('Add RML header', help="Add or not the coporate RML header"),
		'multi': fields.boolean('On multiple doc.', help="If set to true, the action will not be displayed on the right toolbar of a form views.")
	}
	_defaults = {
		'type': lambda *a: 'ir.actions.report.xml',
		'multi': lambda *a: False,
		'auto': lambda *a: True,
		'header': lambda *a: True,
		'report_sxw_content': lambda *a: False,
	}
	#
	# Untested function
	#
	def upload_report(self, cr, uid, report_id, file_sxw, context):
		import tiny_sxw2rml
		import StringIO
		pool = pooler.get_pool(cr.dbname)
		sxwval = StringIO.StringIO(base64.decodestring(file_sxw))
		fp = tools.file_open('normalized_oo2rml.xsl',subdir='addons/base_report_designer/wizard/tiny_sxw2rml')
		report = pool.get('ir.actions.report.xml').write(cr, uid, [report_id], {
			'report_sxw_content': base64.decodestring(file_sxw),
			'report_rml_content': str(tiny_sxw2rml.sxw2rml(sxwval, xsl=fp.read()))
		})
		return {}
report_xml()

class act_window(osv.osv):
	_name = 'ir.actions.act_window'
	_table = 'ir_act_window'
	_sequence = 'ir_actions_id_seq'

	def _views_get_fnc(self, cr, uid, ids, name, arg, context={}):
		res={}
		for act in self.browse(cr, uid, ids):
			res[act.id]=[(view.view_id.id, view.view_mode) for view in act.view_ids]
			if (not act.view_ids):
				modes = act.view_mode.split(',')
				find = False
				if act.view_id.id:
					res[act.id].append((act.view_id.id, act.view_id.type))
				for t in modes:
					if act.view_id and (t == act.view_id.type) and not find:
						find = True
						continue
					res[act.id].append((False, t))
		return res

	_columns = {
		'name': fields.char('Action Name', size=64, translate=True),
		'type': fields.char('Action Type', size=32, required=True),
		'view_id': fields.many2one('ir.ui.view', 'View Ref.', ondelete='cascade'),
		'domain': fields.char('Domain Value', size=250),
		'context': fields.char('Context Value', size=250),
		'res_model': fields.char('Model', size=64),
		'src_model': fields.char('Source model', size=64),
		'view_type': fields.selection((('tree','Tree'),('form','Form')),string='Type of view'),
		'view_mode': fields.char('Mode of view', size=250),
		'usage': fields.char('Action Usage', size=32),
		'view_ids': fields.one2many('ir.actions.act_window.view', 'act_window_id', 'Views'),
		'views': fields.function(_views_get_fnc, method=True, type='binary', string='Views'),
	}
	_defaults = {
		'type': lambda *a: 'ir.actions.act_window',
		'view_type': lambda *a: 'form',
		'view_mode': lambda *a: 'tree,form',
		'context': lambda *a: '{}'
	}
act_window()

class act_window_view(osv.osv):
	_name = 'ir.actions.act_window.view'
	_table = 'ir_act_window_view'
	_rec_name = 'view_id'
	_columns = {
		'sequence': fields.integer('Sequence'),
		'view_id': fields.many2one('ir.ui.view', 'View'),
		'view_mode': fields.selection((('tree', 'Tree'),('form', 'Form'),('graph', 'Graph')), string='Type of view', required=True),
		'act_window_id': fields.many2one('ir.actions.act_window', 'Action'),
		'multi': fields.boolean('On multiple doc.', help="If set to true, the action will not be displayed on the right toolbar of a form views.")
	}
	_defaults = {
		'multi': lambda *a: False,
	}
	_order = 'sequence'
act_window_view()

class act_wizard(osv.osv):
	_name = 'ir.actions.wizard'
	_table = 'ir_act_wizard'
	_sequence = 'ir_actions_id_seq'
	_columns = {
		'name': fields.char('Wizard info', size=64, required=True, translate=True),
		'type': fields.char('Action type', size=32, required=True),
		'wiz_name': fields.char('Wizard name', size=64, required=True),
		'multi': fields.boolean('Action on multiple doc.', help="If set to true, the wizard will not be displayed on the right toolbar of a form views.")
	}
	_defaults = {
		'type': lambda *a: 'ir.actions.wizard',
		'multi': lambda *a: False,
	}
act_wizard()

