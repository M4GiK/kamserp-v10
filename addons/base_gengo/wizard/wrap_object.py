# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import orm, osv
import tools
from tools.translate import _
from mygengo import MyGengo
import re

REQUEST_LIMIT=10

LANG_MAPPING={
    'ar':'Arabic',
    'id':'Indonesian',
    'nl':'Dutch',
    'fr-ca':'French (Canada)',
    'pl':'Polish',
    'zh-tw':'Chinese (Traditional)',
    'sv':'Swedish',
    'ko':'Korean',
    'pt':'Portuguese (Europe)',
    'en':'English',
    'ja':'Japanese',
    'es':'Spanish (Spain)',
    'zh':'Chinese (Simplified)',
    'de':'German',
    'fr':'French',
    'ru':'Russian',
    'it':'Italian',
    'pt-br':'Portuguese (Brazil)',
}

LANG_CODE_MAPPING = {
    'ar_SA':'ar',
    'id_ID':'id',
    'nl_NL':'nl',
    'fr_CA':'fr-ca',
    'pl':'pl',
    'zh_TW':'zh-tw',
    'sv_SE':'sv',
    'ko_KR':'ko',
    'pt_PT':'pt',
    'en':'en',
    'ja_JP':'ja',
    'es_ES':'es',
    'zh_CN':'zh',
    'de_DE':'de',
    'fr_FR':'fr',
    'ru_RU':'ru',
    'it_IT':'it',
    'pt_BR':'pt-br'
}

class gengo_response(object):
    """ 
    """
    def __init__(self, jobs):
        response = jobs['response'] 
        job = []
        jobs_id=[]
        if isinstance(response, list):
            job = [ gengo_job(value) for value in response]
        else:
            job = [ gengo_job(value) for value in response.values()]
        jobs.update({'response': job})
        self._data = jobs

    def __getitem__(self, name):
        return self._data[name]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError, e:
            raise AttributeError(e)

class gengo_job(object):
    """ 
    """
    def __init__(self, job):
        self._data = job

    def __getitem__(self, name):
        return self._data[name]

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError, e:
            raise AttributeError(e)

class JobsMeta(orm.AbstractModel):
    
    _name="jobs.meta"
    
    def gengo_authentication(self,cr,uid,ids,context=None):
        ''' To Send Request and Get Response from Gengo User needs Public and Private
         key for that user need to signup to gengo and get public and private 
         key which is provided by gengo to authentic user '''
    
        gengo_parameter_pool=self.pool.get('res.users').browse(cr,uid,uid,context)
        try:
            gengo = MyGengo(
                public_key = gengo_parameter_pool.company_id.gengo_public_key.encode('ascii'),
                private_key = gengo_parameter_pool.company_id.gengo_private_key.encode('ascii'),
                sandbox = True,
            )
            return gengo
        except Exception, e:
            raise osv.except_osv(_('Warning !'), _(e))
             
    def pack_jobs_request(self, cr, uid, translation_term_id, context):
        jobs={}
        auto_approve = 0
        gengo_parameter_pool=self.pool.get('res.users').browse(cr, uid, uid, context)
        translation_pool =self.pool.get('ir.translation')
        
        if gengo_parameter_pool.company_id.gengo_auto_approve == True:
            auto_approve=1

        for key,value in LANG_CODE_MAPPING.items():
            if key == context['language_code']:
                for terms in translation_pool.read(cr, uid, translation_term_id, context=None):
#                    translation_pool.write(cr,uid,translation_term_id,{'state':'inprogress'})
                    if re.search(r"[a-z A-Z]",terms['src']):
                        job = {'type':'text',
                                'slug':'single::English to '+ LANG_MAPPING.get(value),
                                'tier':gengo_parameter_pool.company_id.gengo_tier,
                                'body_src':terms['src'],
                                'lc_src':'en',
                                'lc_tgt':value,     
                                'auto_approve': auto_approve,   
                                'comment':gengo_parameter_pool.company_id.gengo_comment ,
                                }
                        jobs.update({terms['id']: job})
                return {'jobs': jobs}
                
    def unpack_jobs_response(self, jobs):
        return gengo_response(jobs)
        
        
