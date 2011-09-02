# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from osv import osv,fields
from osv.orm import except_orm
import pickle
from tools.translate import _

EXCLUDED_FIELDS = set((
    'report_sxw_content', 'report_rml_content', 'report_sxw', 'report_rml',
    'report_sxw_content_data', 'report_rml_content_data', 'search_view', ))

#: Possible slots to bind an action to with :meth:`~.set_action`
ACTION_SLOTS = [
                "client_action_multi",  # sidebar wizard action
                "client_print_multi",   # sidebar report printing button
                "client_action_relate", # sidebar related link
                "tree_but_open",        # double-click on item in tree view
                "tree_but_action",      # deprecated: same as tree_but_open
               ]


class ir_values(osv.osv):
    """Holds internal model-specific action bindings and user-defined default
       field values. definitions. This is a legacy internal model, mixing
       two different concepts, and will likely be updated or replaced in a
       future version by cleaner, separate models. You should not depend
       explicitly on it.

       The purpose of each ``ir.values`` entry depends on its type, defined
       by the ``key`` column:

        * 'default': user-defined default values, used when creating new
          records of this model:
        * 'action': binding of an action to a particular *action slot* of
          this model, making the action easily available in the user
          interface for this model.

       The ``key2`` column acts as a qualifier, further refining the type
       of the entry. The possible values are:

        * for 'default' entries: an optional condition restricting the
          cases where this particular default value will be applicable,
          or ``False`` for no condition
        * for 'action' entries: the ``key2`` qualifier is one of the available
          action slots, defining how this action can be invoked:

            * ``'client_print_multi'`` for report printing actions that will
              be available on views displaying items from this model
            * ``'client_action_multi'`` for assistants (wizards) actions
              that will be available in views displaying objects of this model
            * ``'client_action_relate'`` for links towards related documents
              that should be available in views displaying objects of this model
            * ``'tree_but_open'`` for actions that will be triggered when
              double-clicking an item from this model in a hierarchical tree view

       Each entry is specific to a model (``model`` column), and for ``'actions'``
       type, may even be made specific to a given record of that model when the
       ``res_id`` column contains a record ID (``False`` means it's global for
       all records).

       The content of the entry is defined by the ``value`` column, which may either
       contain an arbitrary value (for default values - when the ``object`` column
       is False), or a reference string defining the action that should be executed.

       .. rubric:: Usage: default values
       
       The ``'default'`` entries are usually defined manually by the
       users, and set by their UI clients calling :meth:`~.set_default`.
       These default values are then automatically used by the
       ORM every time a new record is about to be created, i.e. when
       :meth:`~openerp.osv.osv.osv.default_get`
       or :meth:`~openerp.osv.osv.osv.create` are called.

       .. rubric:: Usage: action bindings

       Business applications will usually bind their actions during
       installation, and OpenERP UI clients will apply them as defined,
       based on the list of actions included in the result of
       :meth:`~openerp.osv.osv.osv.fields_view_get`,
       or directly returned by explicit calls to :meth:`~.get_actions`.
    """
    _name = 'ir.values'

    def _value_unpickle(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for report in self.browse(cursor, user, ids, context=context):
            value = report[name[:-9]]
            if not report.object and value:
                try:
                    value = str(pickle.loads(value))
                except Exception:
                    pass
            res[report.id] = value
        return res

    def _value_pickle(self, cursor, user, id, name, value, arg, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        if self.CONCURRENCY_CHECK_FIELD in ctx:
            del ctx[self.CONCURRENCY_CHECK_FIELD]
        if not self.browse(cursor, user, id, context=context).object:
            value = pickle.dumps(value)
        self.write(cursor, user, id, {name[:-9]: value}, context=ctx)

    def onchange_object_id(self, cr, uid, ids, object_id, context=None):
        if not object_id: return {}
        act = self.pool.get('ir.model').browse(cr, uid, object_id, context=context)
        return {
                'value': {'model': act.model}
        }

    def onchange_action_id(self, cr, uid, ids, action_id, context=None):
        if not action_id: return {}
        act = self.pool.get('ir.actions.actions').browse(cr, uid, action_id, context=context)
        return {
                'value': {'value_unpickle': act.type+','+str(act.id)}
        }

    def onchange_key(self, cr, uid, ids, key, context=None):
        return {
                'value': {'object': key == 'action'}
        }

    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'model': fields.char('Model Name', size=128, select=True, required=True,
                             help="Model to which this entry applies"),

        # TODO: model_id and action_id should be read-write function fields
        'model_id': fields.many2one('ir.model', 'Model (change only)', size=128,
                                    help="Model to which this entry applies - "
                                         "helper field for setting a model, will "
                                         "automatically set the correct model name"),
        'action_id': fields.many2one('ir.actions.actions', 'Action (change only)',
                                     help="Action bound to this entry - "
                                         "helper field for binding an action, will "
                                         "automatically set the correct reference"),

        'value': fields.text('Value', help="Default value (pickled) or reference to an action"),
        'value_unpickle': fields.function(_value_unpickle, fnct_inv=_value_pickle,
                                          type='text',
                                          string='Default value or action reference'),
        'object': fields.boolean('No value serialization', help="Should be enabled when Type is Action"),
        'key': fields.selection([('action','Action'),('default','Default')],
                                'Type', size=128, select=True, required=True,
                                help="- Action: an action attached to one slot of the given model\n"
                                     "- Default: a default value for a model field"),
        'key2' : fields.char('Qualifier', size=128, select=True,
                             help="For actions, one of the possible action slots: \n"
                                  "  - client_action_multi\n"
                                  "  - client_print_multi\n"
                                  "  - client_action_relate\n"
                                  "  - tree_but_open\n"
                                  "For defaults, an optional condition"
                             ,),
        'res_id': fields.integer('Record ID', select=True,
                                 help="Database identifier of the record to which this applies. "
                                      "0 = for all records"),
        'user_id': fields.many2one('res.users', 'User', ondelete='cascade', select=True,
                                   help="If set, action binding only applies for this user."),
        'company_id': fields.many2one('res.company', 'Company', ondelete='cascade', select=True,
                                      help="If set, action binding only applies for this company")
    }
    _defaults = {
        'key': 'action',
        'key2': 'tree_but_open',
        'object': True,
    }

    def _auto_init(self, cr, context=None):
        super(ir_values, self)._auto_init(cr, context)
        cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = \'ir_values_key_model_key2_res_id_user_id_idx\'')
        if not cr.fetchone():
            cr.execute('CREATE INDEX ir_values_key_model_key2_res_id_user_id_idx ON ir_values (key, model, key2, res_id, user_id)')

    def set_default(self, cr, uid, model, field_name, value, for_all_users=True, company_id=False, condition=False):
        """Defines a default value for the given model and field_name. Any previous
           default will be replaced and lost in the process.

           :param string model: model name
           :param string field_name: field name to which the default applies
           :param value: the default field value to set
           :type value: any serializable Python value
           :param bool for_all_users: whether the default should apply to everybody or only
                                      the user calling the method
           :param int company_id: optional ID of the company to which the default should
                                  apply. If omitted, the default will be global. If True
                                  is passed, the current user's company will be used.
           :param string condition: optional condition specification that can be used to
                                    restrict the applicability of the default values
                                    (e.g. based on another field's value)
           :return: id of the newly created ir.values entry
        """
        if isinstance(value, unicode):
            value = value.encode('utf8')
        if company_id is True:
            # should be company-specific, need to get company id
            user = self.pool.get('res.users').browse(cr, uid, uid)
            company_id = user.company_id.id

        # remove existing defaults for the same scope
        search_criteria = [
            ('key', '=', 'default'),
            ('key2', '=', condition),
            ('model', '=', model),
            ('name', '=', field_name),
            ('user_id', '=', False if for_all_users else uid),
            ('company_id','=', company_id)
            ]
        self.unlink(cr, uid, self.search(cr, uid, search_criteria))

        return self.create(cr, uid, {
            'name': field_name,
            'value': pickle.dumps(value),
            'model': model,
            'object': False,
            'key': 'default',
            'key2': condition and condition[:200],
            'user_id': False if for_all_users else uid,
            'company_id': company_id,
        })

    def get_defaults(self, cr, uid, model, condition=False):
        """Returns any user-defined values registered for the given model.
           This is not field-specific, but an optional ``condition`` can be
           provided to query for default values that should be applied only
           when the given condition is met (usually another field's value).
           Defaults that have been set for the user herself will have higher
           priority that those that have been set for everyone
           (see :meth:`~.set_default`).

           :param string model: model name
           :param string condition: optional condition specification that can be used to
                                    restrict the applicability of the default values
                                    (e.g. based on another field's value)
           :return: list of default values tuples of the form ``(id, field_name, value)``
                    (``id`` is the ID of the default entry, usually irrelevant)
        """
        # use a direct SQL query for performance reasons,
        # this is called very often
        query = """SELECT v.id, v.name, v.value FROM ir_values v
                      LEFT JOIN res_users u ON (v.user_id = u.id)
                   WHERE v.key = %%s AND v.model = %%s
                      AND (v.user_id = %%s OR v.user_id IS NULL)
                      AND (u.company_id IS NULL OR
                           u.company_id =
                             (SELECT company_id from res_users where id = %%s)
                          )
                      %s
                   ORDER BY v.user_id, u.company_id"""
        query = query % ('AND v.key2 = %s' if condition else '')
        params = ('default', model, uid, uid)
        if condition:
            params += (condition,)
        cr.execute(query, params)

        # keep only the highest priority default for each field
        defaults = {}
        for row in cr.dictfetchall():
            defaults.setdefault(row['name'],
                (row['id'], row['name'], pickle.loads(row['value'].encode('utf-8'))))
        return defaults.values()

    def set_action(self, cr, uid, name, action_slot, model, action, res_id=False):
        """Binds an the given action to the given model's action slot - for later
           retrieval via :meth:`~.get_actions`. Any existing binding of the same action
           to the same slot is first removed, allowing an update of the action's name.
           See the class description for more details about the various action
           slots: :class:`~ir_values`.

           :param string name: action label, usually displayed by UI client
           :param string action_slot: the action slot to which the action should be
                                      bound to - one of ``client_action_multi``,
                                      ``client_print_multi``, ``client_action_relate``,
                                      ``tree_but_open``.
           :param string model: model name
           :param string action: action reference, in the form ``'model,id'``
           :param int res_id: optional record id - will bind the action only to a
                              specific record of the model, not all records.
           :return: id of the newly created ir.values entry
        """
        assert isinstance(action, basestring) and ',' in action, \
               'Action definition must be an action reference, e.g. "ir.actions.act_window,42"'
        assert action_slot in ACTION_SLOTS, \
               'Action slot (%s) must be one of: %r' % (action_slot, ACTION_SLOTS)

        # remove existing action definition of same slot and value
        search_criteria = [
            ('key', '=', 'action'),
            ('key2', '=', action_slot),
            ('model', '=', model),
            ('res_id', '=', res_id or 0), # int field -> NULL == 0
            ('value', '=', action),
            ]
        self.unlink(cr, uid, self.search(cr, uid, search_criteria))

        return self.create(cr, uid, {
            'key': 'action',
            'key2': action_slot,
            'object': True,
            'model': model,
            'res_id': res_id,
            'name': name,
            'value': action,
        })

    def get_actions(self, cr, uid, action_slot, model, res_id=False, context=None):
        """Retrieves the list of actions bound to the given model's action slot.
           See the class description for more details about the various action
           slots: :class:`~.ir_values`.

           :param string action_slot: the action slot to which the actions should be
                                      bound to - one of ``client_action_multi``,
                                      ``client_print_multi``, ``client_action_relate``,
                                      ``tree_but_open``.
           :param string model: model name
           :param int res_id: optional record id - will bind the action only to a
                              specific record of the model, not all records.
           :return: list of action tuples of the form ``(id, name, action_def)``,
                    where ``id`` is the ID of the default entry, ``name`` is the
                    action label, and ``action_def`` is a dict containing the
                    action definition as obtained by calling
                    :meth:`~openerp.osv.osv.osv.read` on the action record.
        """
        assert action_slot in ACTION_SLOTS, 'Illegal action slot value: %s' % action_slot
        # use a direct SQL query for performance reasons,
        # this is called very often
        query = """SELECT v.id, v.name, v.value FROM ir_values v
                   WHERE v.key = %s AND v.key2 = %s
                        AND v.model = %s
                        AND (v.res_id = %s
                             OR v.res_id IS NULL
                             OR v.res_id = 0)
                   ORDER BY v.id"""
        cr.execute(query, ('action', action_slot, model, res_id or None))
        results = {}
        for action in cr.dictfetchall():
            action_model,id = action['value'].split(',')
            fields = [
                    field
                    for field in self.pool.get(action_model)._all_columns
                    if field not in EXCLUDED_FIELDS]
            # FIXME: needs cleanup
            try:
                action_def = self.pool.get(action_model).read(cr, uid, int(id), fields, context)
                if action_def:
                    if action_model in ('ir.actions.report.xml','ir.actions.act_window',
                                        'ir.actions.wizard'):
                        groups = action_def.get('groups_id')
                        if groups:
                            cr.execute('SELECT 1 FROM res_groups_users_rel WHERE gid IN %s AND uid=%s',
                                       (tuple(groups), uid))
                            if not cr.fetchone():
                                if action['name'] == 'Menuitem':
                                    raise osv.except_osv('Error !',
                                                         'You do not have the permission to perform this operation !!!')
                                continue
                # keep only the first action registered for each action name
                results[action['name']] = (action['id'], action['name'], action_def)
            except except_orm, e:
                continue
        return results.values()

    def _map_legacy_model_list(self, model_list, map_fn, merge_results=False):
        """Apply map_fn to the various models passed, according to
           legacy way to specify models/records.
        """
        assert isinstance(model_list, (list, tuple)), \
            "model_list should be in the form [model,..] or [(model,res_id), ..]"
        results = []
        for model in model_list:
            res_id = False
            if isinstance(model, (list, tuple)):
                model, res_id = model
            result = map_fn(model, res_id)
            # some of the functions return one result at a time (tuple or id)
            # and some return a list of many of them - care for both
            if merge_results:
                results.extend(result)
            else:
                results.append(result)
        return results

    # Backards-compatibility adapter layer to retrofit into split API
    def set(self, cr, uid, key, key2, name, models, value, replace=True, isobject=False, meta=False, preserve_user=False, company=False):
        """Deprecated legacy method to set default values and bind actions to models' action slots.
           Now dispatches to the newer API methods according to the value of ``key``: :meth:`~.set_default`
           (``key=='default'``) or :meth:`~.set_action` (``key == 'action'``).

          :deprecated: As of v6.1, ``set_default()`` or ``set_action()`` should be used directly.
        """
        assert key in ['default', 'action'], "ir.values entry keys must be in ['default','action']"
        if key == 'default':
            def do_set(model,res_id):
                return self.set_default(cr, uid, model, field_name=name, value=value,
                                        for_all_users=(not preserve_user), company_id=company,
                                        condition=key2)
        elif key == 'action':
            def do_set(model,res_id):
                return self.set_action(cr, uid, name, action_slot=key2, model=model, action=value, res_id=res_id)
        return self._map_legacy_model_list(models, do_set)

    def get(self, cr, uid, key, key2, models, meta=False, context=None, res_id_req=False, without_user=True, key2_req=True):
        """Deprecated legacy method to get the list of default values or actions bound to models' action slots.
           Now dispatches to the newer API methods according to the value of ``key``: :meth:`~.get_defaults`
           (``key=='default'``) or :meth:`~.get_actions` (``key == 'action'``)

          :deprecated: As of v6.1, ``get_defaults()`` or ``get_actions()`` should be used directly.

        """
        assert key in ['default', 'action'], "ir.values entry keys must be in ['default','action']"
        if key == 'default':
            def do_get(model,res_id):
                return self.get_defaults(cr, uid, model, condition=key2)
        elif key == 'action':
            def do_get(model,res_id):
                return self.get_actions(cr, uid, action_slot=key2, model=model, res_id=res_id, context=context)
        return self._map_legacy_model_list(models, do_get, merge_results=True)
