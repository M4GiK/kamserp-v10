# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import wizard
import pooler

period_form = '''<?xml version="1.0"?>
<form string="Select Date-Period">
    <field name="company_id"/>
    <field name="result_selection"/>
    <newline/>
    <field name="fiscalyear"/>
    <label colspan="2" string="(Keep empty for all open fiscal years)" align="0.0"/>
    <newline/>
    <separator string="Filters" colspan="4"/>
    <field name="state" required="True"/>
    <newline/>
    <group attrs="{'invisible':[('state','=','none')]}" colspan="4">
        <group attrs="{'invisible':[('state','=','byperiod')]}" colspan="4">
            <separator string="Date Filter" colspan="4"/>
            <field name="date1"/>
            <field name="date2"/>
        </group>
        <group attrs="{'invisible':[('state','=','bydate')]}" colspan="4">
            <separator string="Filter on Periods" colspan="4"/>
            <field name="periods" colspan="4" nolabel="1"/>
        </group>
    </group>
</form>'''

period_fields = {
    'company_id': {'string': 'Company', 'type': 'many2one', 'relation': 'res.company', 'required': True},
    'state':{
        'string':"Date/Period Filter",
        'type':'selection',
        'selection':[('bydate','By Date'),('byperiod','By Period'),('all','By Date and Period'),('none','No Filter')],
        'default': lambda *a:'none'
    },
    'fiscalyear': {
        'string':'Fiscal year', 'type': 'many2one', 'relation': 'account.fiscalyear',
        'default': lambda *a:False,
        'help': 'Keep empty for all open fiscal year'
    },
    'periods': {'string': 'Periods', 'type': 'many2many', 'relation': 'account.period', 'help': 'All periods if empty','states':{'none':[('readonly',True)],'bydate':[('readonly',True)]}},
    'result_selection':{
        'string':"Partner",
        'type':'selection',
        'selection':[('customer','Receivable Accounts'),('supplier','Payable Accounts'),('all','Receivable and Payable Accounts')],
        'required':True
    },
    'soldeinit':{'string':"Include initial balances",'type':'boolean'},
    'date1': {'string':'          Start date', 'type':'date', 'required':True,'default': lambda *a: time.strftime('%Y-01-01')},
    'date2': {'string':'End date', 'type':'date', 'required':True,'default': lambda *a: time.strftime('%Y-%m-%d')},
}

class wizard_report(wizard.interface):
    
    def _get_defaults(self,cr,uid,data,context):
        user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
           company_id = user.company_id.id
        else:
           company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
       
        fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
        periods_obj=pooler.get_pool(cr.dbname).get('account.period')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        data['form']['periods'] =periods_obj.search(cr, uid, [('fiscalyear_id','=',data['form']['fiscalyear'])])
        data['form']['company_id'] = company_id
        data['form']['soldeinit'] = True
        data['form']['fiscalyear'] = False
        data['form']['result_selection'] = 'all'
        return data['form']
    
    def _check_state(self, cr, uid, data, context):
      
        if data['form']['state'] == 'bydate'  :
           self._check_date(cr, uid, data, context)
        return data['form']
  
    def _check_date(self, cr, uid, data, context):
        
        sql = """
            SELECT f.id, f.date_start, f.date_stop FROM account_fiscalyear f  Where '%s' between f.date_start and f.date_stop """%(data['form']['date1'])
        cr.execute(sql)
        res = cr.dictfetchall()
        if res:
            if (data['form']['date2'] > res[0]['date_stop'] or data['form']['date2'] < res[0]['date_start']):
                raise  wizard.except_wizard('UserError','Date to must be set between ' + res[0]['date_start'] + " and " + res[0]['date_stop'])
            else:
                return 'report'
            
        else:
            raise wizard.except_wizard('UserError','Date not in a defined fiscal year')

    states = {
        'init': {
            'actions': [_get_defaults],
           'result': {'type':'form', 'arch':period_form, 'fields':period_fields, 'state':[('end','Cancel','gtk-cancel'),('report','Print','gtk-print')]}
        },
        
        'report': {
            'actions': [_check_state],
            'result': {'type':'print', 'report':'account.partner.balance', 'state':'end'}
        }
    }
wizard_report('account.partner.balance.report')
