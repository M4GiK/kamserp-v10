from base.controllers.main import View
import openerpweb

class Export(View):
    _cp_path = "/base_export/export"

    def fields_get(self, req, model):
        Model = req.session.model(model)
        fields = Model.fields_get(False, req.session.eval_context(req.context))
        return fields

    @openerpweb.jsonrequest
    def get_fields(self, req, model, prefix='', field_parent=None, name= ''):
        fields = self.fields_get(req, model)

        fields.update({'id': {'string': 'ID'}, '.id': {'string': 'Database ID'}})

        records = []
        for key, value in fields.items():
            record = {}

            id = prefix + (prefix and '/'or '') + key
            nm = name + (name and '/' or '') + value['string']
            record.update(id=id, string= nm, action='javascript: void(0)',
                          target=None, icon=None, children=[])
            records.append(record)

            if value.get('relation', False):
                ref = value.pop('relation')
                cfields = self.fields_get(req, ref)
                if (value['type'] == 'many2many'):
                    record['children'] = []
                    record['params'] = {'model': ref, 'prefix': id, 'name': nm}

                elif (value['type'] == 'many2one') or (value['type'] == 'many2many'):
                    cfields_order = cfields.keys()
                    cfields_order.sort(lambda x,y: -cmp(cfields[x].get('string', ''), cfields[y].get('string', '')))
                    children = []
                    for j, fld in enumerate(cfields_order):
                        cid = id + '/' + fld
                        cid = cid.replace(' ', '_')
                        children.append(cid)
                    record['children'] = children or []
                    record['params'] = {'model': ref, 'prefix': id, 'name': nm}

                else:
                    cfields_order = cfields.keys()
                    cfields_order.sort(lambda x,y: -cmp(cfields[x].get('string', ''), cfields[y].get('string', '')))
                    children = []
                    for j, fld in enumerate(cfields_order):
                        cid = id + '/' + fld
                        cid = cid.replace(' ', '_')
                        children.append(cid)
                    record['children'] = children or []
                    record['params'] = {'model': ref, 'prefix': id, 'name': nm}

        records.reverse()
        return records

    @openerpweb.jsonrequest
    def save_export_lists(self, req, name, model, field_list):
        result = {'resource':model, 'name':name, 'export_fields': []}
        for field in field_list:
            result['export_fields'].append((0, 0, {'name': field}))
        return req.session.model("ir.exports").create(result, req.session.eval_context(req.context))

    @openerpweb.jsonrequest
    def exist_export_lists(self, req, model):
        export_model = req.session.model("ir.exports")
        return export_model.read(export_model.search([('resource', '=', model)]), ['name'])

    @openerpweb.jsonrequest
    def delete_export(self, req, export_id):
        req.session.model("ir.exports").unlink(export_id, req.session.eval_context(req.context))
        return True
