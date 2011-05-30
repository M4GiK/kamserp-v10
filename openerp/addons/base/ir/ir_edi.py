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
import json
import hashlib
import time
import base64
import urllib2

def safe_unique_id(model, database_id):

    """Generate a unique string to represent a (model,database id) pair
    without being too long, without revealing the database id, and
    with a very low probability of collisions.
    """
    msg = "%s-%s-%s" % (model, time.time(), database_id)
    digest = hashlib.sha1(msg).digest()
    digest = ''.join(chr(ord(x) ^ ord(y)) for (x,y) in zip(digest[:9], digest[9:-2]))
    # finally, use the b64-encoded folded digest as ID part of the unique ID:
    digest = base64.urlsafe_b64encode(digest)
        
    return '%s' % (digest)

class ir_edi_document(osv.osv):
    _name = 'ir.edi.document'
    _description = 'ir_edi_document'
    _columns = {
                'name': fields.char('EDI token', size = 128),
                'document': fields.text()
                
    }
    
    
    
    def new_edi_token(self,cr,uid,ids,browse_records,database_id,context=None):
        
        """Generate new unique tokent value to uniquely identify each edi_document"""
        
        db_uuid = safe_unique_id(browse_records, database_id)
        edi_token = hashlib.sha256('%s-%s-%s' % (time.time(),db_uuid,time.time())).hexdigest()


        return edi_token
    
    def serialize(self,edi_list_of_dicts):
        
        """Serialize the list of dictionaries using json dumps method"""
        
        serialized_list = json.dumps(edi_list_of_dicts)
        return serialized_list
    
    def generate_edi(self,browse_record_list):
        
        """ Generate the list of dictionaries using edi_export method of edi class """
        
        edi = edi()
        edi_list = []
        for record in browse_record_list:
            edi_struct = edi.edi_export(record)
            edi_list.append(edi_struct)
        return self.serialize(edi_list)
    
    def get_document(self,cr,uid,ids,edi_token,context=None):
        
        """Get the edi document from database using given edi token """
        
        records = self.search(cr,uid,[('name','=',edi_token)],context=context)
        if records:
            doc_string = self.read(cr,uid,records,['document'],context=context)
        else:
            raise osv.except_osv(_('Error !'),
                _('Desired EDI Document does not Exist'))  
        
        return doc_string
    
    def load_edi(self,cr,uid,ids,edi_list_of_dicts,context=None):
        
        """loads the values from list of dictionaries to the corresponding OpenERP records
            using the edi_import method of edi class"""
        edi = edi()
        edi_list = []
        for record in edi_list_of_dicts:
            edi_record = edi.edi_import(record)
            
        
        return True
    
    def deserialize(self,edi_document_string):
        """ Deserialized the edi document string"""
        
        deserialize_string = json.loads(edi_document_string)
        return self.load_edi(deserialize_string)
    
    def export_doc(self, cr, uid, ids,browse_records,database_id,context=None):
        """the method handles the flow of the edi document generation and store it in 
            the database and return the edi_token of the particular document"""
        
        edi_document = {
                     'name': self.new_edi_token(browse_records,database_id),
                     'document': self.generate_edi(browse_records)
                    }
        
        unique_id = self.create(cr,uid,edi_document,context=context)
        return edi_document['name']
    
    def import_doc(self, cr, uid, ids, edi_document=None,edi_url=None,context=None):
        
        """the method handles the flow of importing particular edi document and 
            updates the database values on the basis of the edi document using 
            edi_loads method """
        
        if edi_document is not None:
            self.deserialize(edi_document)
        elif edi_url is not None:
            edi_document = urllib2.urlopen(edi_url).read()
            self.deserialize(edi_document)

        return True
    
ir_edi_document()

    
class edi(object):
    _name = 'edi'
    _description = 'edi document handler'
    
    """Mixin class for OSV objects that want be exposed as EDI documents.
       Classes that inherit from this mixin class should override the 
       ``edi_import()`` and ``edi_export()`` methods to implement their
       specific behavior, based on the primitives provided by this superclass."""
    
    
    def edi_metadata(self, cr, uid, ids, browse_rec_list, context=None):
        """Return a list representing the boilerplate EDI structure for
           exporting the record in the given browse_rec_list, including
           the metadata fields"""
        # generic implementation!
        data_object = self.pool.get('ir.model.data')
        
        if self.edi_document['__model'] is not None:
            model_ids = data_object.search(cr,uid,[('model','=',self.edi_document['__model'])],context=context)
            for data in data_object.browse(cr,uid,model_ids):
                self.edi_document['__module'] = data.module
                if data.name is not None:
                    self.edi_document['__id'] = context['active_id']+':'+data.name
                self.edi_document['__last_updata'] = context['__last_update'].values()[0]
            
        return True

    def edi_m2o(self, cr, uid, ids, browse_rec,model=None,context=None):
        """Return a list representing a M2O EDI value for
           the given browse_record."""
        # generic implementation!
        res = []
        data_object = self.pool.get('ir.model.data')
        uu_id = data_model.search(cr,uid,[('model','=',model)])
        for xml in data_model.browse(cr,uid,uu_id):
            if xml:
                xml_ID = xml.name
            else:
                xml_ID = None
        for data in browse_rec:
            if data.name is not None:
                if xml_ID is not None:
                    res.append(safe_unique_id(model,data.id)+':'+xml_ID)
                else:
                    res.append(safe_unique_id(model,data.id)+':'+model+'-'+safe_unique_id(model,data.id))
                res.append(data.name)
        return res

    def edi_o2m(self, cr, uid, ids, browse_rec_list, model=None, context=None):
        """Return a list representing a O2M EDI value for
           the browse_records from the given browse_record_list."""
        # generic implementation!
        res = []
        init_data = {}
        data_object = self.pool.get('ir.model.data')
        uu_id = data_model.search(cr,uid,[('model','=',model)])
        for xml in data_model.browse(cr,uid,uu_id):
            if xml:
                xml_ID = xml.name
            else:
                xml_ID = None
        data_model = self.pool.get(model)
        for record in browse_rec_list:
            if xml_ID is not None:
                init_data['__id'] = safe_unique_id(model,record.id)+':'+xml_ID
            else:
                init_data['__id'] = safe_unique_id(model,record.id)+':'+model+'-'+safe_unique_id(model,record.id)  
            init_data['__last_update'] =record.write_date
            init_data.update(datamodel.read(cr,uid,[record],[],context=context)[0])
            res.append(init_data)
        return res

    def edi_m2m(self, cr, uid, ids, browse_rec_list,model=None, context=None):
        """Return a list representing a M2M EDI value for
           the browse_records from the given browse_record_list."""
        # generic implementation!
        res = []
        init_data = []
        data_object = self.pool.get('ir.model.data')
        uu_id = data_model.search(cr,uid,[('model','=',model)])
        for xml in data_model.browse(cr,uid,uu_id):
            if xml:
                xml_ID = xml.name
            else:
                xml_ID = None
        data_model = self.pool.get(model)
        for record in browse_rec_list:
            if xml_ID is not None:
                init_data.append(safe_unique_id(model,record.id)+':'+xml_ID)
            else:
                init_data.append(safe_unique_id(model,record.id)+':'+model+'-'+safe_unique_id(model,record.id))
            if record.name is not None:
                init_data.append('name:'+record.name)
            res.append(init_data)    
        return res

    def edi_export(self, cr, uid, ids, edi_struct=None, context=None):
        """Returns a list of dicts representing an edi.document containing the
           browse_records with ``ids``, using the generic algorithm.
           :param edi_struct: if provided, edi_struct should be a dictionary
                              with a skeleton of the OSV fields to export as edi.
                              Basic fields can have any key as value, but o2m
                              values should have a sample skeleton dict as value.
                              For example, for a res.partner record:
                              edi_struct: {
                                   'name': True,
                                   'company_id': True,
                                   'address': {
                                       'name': True,
                                       'street': True,
                                   }
                              }
                              Any field not specified in the edi_struct will not
                              be included in the exported data.
        """
        # generic implementation!
        
        self.edi_document = {
                      
                      '__model':'',
                      '__module':'',
                      '__id':'',
                      '__last_update':'',
                      '__version':'',
                      '__attachments':'',
                      
                      }
        self.edi_document['__model'] = self._name
        
        
        fields_object = self.pool.get('ir.model.fields')
        model_object = self.pool.get(self.edi_document['__model'])
        edi_metadata(context=context)
        for field in self.edi_struct.keys():
            f_ids = fields_object.search(cr,uid,[('name','=',field),('model','=',self.edi_document['__model'])],context=context)
            for fname in fields_object.browse(cr,uid,f_ids):
                if fname.ttype == 'many2one':
                    
                    self.edi_document[field] = self.edi_m2o(edi_struct[field],fname.relation)
                elif fname.ttype == 'one2many':
                    self.edi_ducument[field] = self.edi_o2m(edi_struct[field],fname.relation)
                elif fname.ttype == 'many2many':        
                    self.edi_document[field] = self.edi_m2m(edi_struct[field],fname.relation)
                else:
                    self.edi_document[field] = model_object.read(cr,uid,[context['active_id']],[field],context=context)
        return self.edi_document
    def edi_import(self, cr, uid, edi_document, context=None):
    
        """Imports a list of dicts representing an edi.document, using the
           generic algorithm.
        """
        # generic implementation!
        for field in edi_document.keys():
            
        pass
