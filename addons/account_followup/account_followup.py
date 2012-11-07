# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv
from datetime import date
import time

class followup(osv.osv):
    _name = 'account_followup.followup'
    _description = 'Account Follow-up'
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'description': fields.text('Description'),
        'followup_line': fields.one2many('account_followup.followup.line', 'followup_id', 'Follow-up'),
        'company_id': fields.many2one('res.company', 'Company', required=True),        
    }
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account_followup.followup', context=c),
    }
    
followup()

class followup_line(osv.osv):
    
    
    def _get_default_template(self, cr, uid, ids, context=None):
        res = False        
        templ = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_followup', 'email_template_account_followup_default')
        print templ
        res = templ[1]        
        return res
    
    _name = 'account_followup.followup.line'
    _description = 'Follow-up Criteria'
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of follow-up lines."),
        'delay': fields.integer('Days of delay'),
        'start': fields.selection([('days','Net Days'),('end_of_month','End of Month')], 'Type of Term', size=64, required=True),
        'followup_id': fields.many2one('account_followup.followup', 'Follow Ups', required=True, ondelete="cascade"),
        'description': fields.text('Printed Message', translate=True),
        'send_email':fields.boolean('Send email', help="When processing, it will send an email"),
        'send_letter':fields.boolean('Send letter', help="When processing, it will print a letter"),
        'phonecall':fields.boolean('Manual action'),
        'manual_action':fields.text('Action text'),
        'action_responsible':fields.many2one('res.users', 'Responsible', ondelete='set null'),
        'email_template_id':fields.many2one('email.template', 'Email template', ondelete='set null'), 
        'email_body':fields.related('email_template_id', 'body_html', type='text', string="Email Message", relation="email.template", translate="True"),
    }
    _order = 'delay'
    _sql_constraints = [('days_uniq', 'unique(delay)', 'Days of the follow-up levels must be different')] #ADD FOR multi-company!
    _defaults = {
        'start': 'days',
        'send_email': True,
        'send_letter': False,
        'description': """
        Dear %(partner_name)s,

Exception made if there was a mistake of ours, it seems that the following amount stays unpaid. Please, take appropriate measures in order to carry out this payment in the next 8 days.

Would your payment have been carried out after this mail was sent, please ignore this message. Do not hesitate to contact our accounting department at (+32).10.68.94.39.

Best Regards,
""",
    'email_template_id': _get_default_template,
    }
    
    
    
    
    def on_change_template(self, cr, uid, ids, template_id, context=None):
        #result = {}
        values = {}
        if template_id:
            template  = self.pool.get('email.template').browse(cr, uid, template_id, context=context)
            values = {
                'email_body':template.body_html,                      
                }
        return {'value': values}
            
    
    
    def _check_description(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.description:
                try:
                    line.description % {'partner_name': '', 'date':'', 'user_signature': '', 'company_name': ''}
                except:
                    return False
        return True

    _constraints = [
        (_check_description, 'Your description is invalid, use the right legend or %% if you want to use the percent character.', ['description']),
    ]

followup_line()

class account_move_line(osv.osv):
    
    
    def _get_result(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for aml in self.browse(cr, uid, ids, context): 
            res[aml.id] = aml.debit - aml.credit
        return res
    
    _inherit = 'account.move.line'
    _columns = {
        'followup_line_id': fields.many2one('account_followup.followup.line', 'Follow-up Level', ondelete='restrict'), #restrict deletion of the followup line
        'followup_date': fields.date('Latest Follow-up', select=True),
        'payment_commitment':fields.text('Commitment'),
        'payment_date':fields.date('Date'),
        #'payment_note':fields.text('Payment note'),
        'payment_next_action':fields.text('New action'),
        'result':fields.function(_get_result, type='float', method=True, string="Balance")
    }

account_move_line()




class res_partner(osv.osv):


    def _get_latest_followup_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for partner in self.browse(cr, uid, ids): 


            amls = partner.accountmoveline_ids
            #max(x.followup_date for x in accountmovelines)
            #latest_date = lambda a: date(2011, 1, 1)
            #for accountmoveline in accountmovelines:
            #    if (accountmoveline.followup_date != False) and (latest_date < accountmoveline.followup_date):
            #        latest_date = accountmoveline.followup_date
            #if accountmovelines:
            res[partner.id] = max([x.followup_date for x in amls]) if len(amls) else False
            #else:
            #    res[partner.id] = False

            #res[partner.id] = max(x.followup_date for x in accountmovelines) if len(accountmovelines) else False
        return res

   

    
    def _get_latest_followup_level_id(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for partner in self.browse(cr, uid, ids):
            amls = partner.accountmoveline_ids
            level_id = 0
            level_days = False  #TO BE IMPROVED with boolean checking first time or by using MAX
            latest_level = False            
            res[partner.id] = False
            for accountmoveline in amls:
                if (accountmoveline.followup_line_id != False) and (not level_days or level_days < accountmoveline.followup_line_id.delay): 
                # and (accountmoveline.debit > 0):   (accountmoveline.state != "draft") and
                #and  (accountmoveline.reconcile_id == None)
                    level_days = accountmoveline.followup_line_id.delay
                    latest_level = accountmoveline.followup_line_id.id
                    res[partner.id] = latest_level
            #res[partner.id] = max(x.followup_line_id.delay for x in amls) if len(amls) else False
        return res
    
    def _get_latest_followup_level_id_without_lit(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for partner in self.browse(cr, uid, ids):
            amls = partner.accountmoveline_ids
            level_id = 0
            level_days = False  #TO BE IMPROVED with boolean checking first time or by using MAX
            latest_level = False            
            res[partner.id] = False
            for accountmoveline in amls:
                if (not accountmoveline.blocked) and (accountmoveline.followup_line_id != False) and (not level_days or level_days < accountmoveline.followup_line_id.delay): 
                # and (accountmoveline.debit > 0):   (accountmoveline.state != "draft") and
                #and  (accountmoveline.reconcile_id == None)
                    level_days = accountmoveline.followup_line_id.delay
                    latest_level = accountmoveline.followup_line_id.id
                    res[partner.id] = latest_level
            #res[partner.id] = max(x.followup_line_id.delay for x in amls) if len(amls) else False
        return res

    def get_latest_followup_level(self):
        amls = self.accountmoveline_ids

    def _get_next_followup_level_id_optimized(self, cr, uid, ids, name, arg, context=None):
        #Apparently there is still an error in this function
        res = {}
        for partner in self.browse(cr, uid, ids):            
            latest_id = partner.latest_followup_level_id
            if latest_id:
                latest = latest_id
            else:
                latest = False
            delay = False
            newlevel = False
            if latest: #if latest exists                
                newlevel = latest.id
                old_delay = latest.delay
            else:
                old_delay = False
            fl_ar = self.pool.get('account_followup.followup.line').search(cr, uid, [('followup_id.company_id.id','=', partner.company_id.id)])
            for fl_obj in self.pool.get('account_followup.followup.line').browse(cr, uid, fl_ar):
                if not old_delay: 
                    if not delay or fl_obj.delay < delay: 
                        delay = fl_obj.delay
                        newlevel = fl_obj.id
                else:
                    if (not delay and (fl_obj.delay > old_delay)) or ((fl_obj.delay < delay) and (fl_obj.delay > old_delay)):
                        delay = fl_obj.delay
                        newlevel = fl_obj.id
            res[partner.id] = newlevel
            #Now search one level higher
        return res


    def _get_next_followup_level_id(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for partner in self.browse(cr, uid, ids):            
            latest_id = self._get_latest_followup_level_id(cr, uid, [partner.id], name, arg, context)[partner.id]
            if latest_id:
                latest = self.pool.get('account_followup.followup.line').browse(cr, uid, [latest_id], context)[0]
            else:
                latest = False

            delay = False
            newlevel = False
            if latest: #if latest exists                
                newlevel = latest.id
                old_delay = latest.delay
            else:
                old_delay = False
            fl_ar = self.pool.get('account_followup.followup.line').search(cr, uid, [('followup_id.company_id.id','=', partner.company_id.id)])
            
            for fl_obj in self.pool.get('account_followup.followup.line').browse(cr, uid, fl_ar):
                if not old_delay: 
                    if not delay or fl_obj.delay < delay: 
                        delay = fl_obj.delay
                        newlevel = fl_obj.id
                else:
                    if (not delay and (fl_obj.delay > old_delay)) or ((fl_obj.delay < delay) and (fl_obj.delay > old_delay)):
                        delay = fl_obj.delay
                        newlevel = fl_obj.id
            res[partner.id] = newlevel
            #Now search one level higher
        return res



    def _get_amount_overdue(self, cr, uid, ids, name, arg, context=None):
        ''' 
         Get the total amount in the account move lines that is overdue (passed due date)
        '''
        res={}
        for partner in self.browse(cr, uid, ids, context):
            res[partner.id] = 0.0
            for aml in partner.accountmoveline_ids:
                if ((not aml.date_maturity) and (aml.date <= fields.date.context_today(cr, uid, context))) or (aml.date_maturity <= fields.date.context_today(cr, uid, context)):
                     res[partner.id] = res[partner.id] + aml.debit - aml.credit  #or by using function field
        return res
    

    def do_partner_phonecall(self, cr, uid, partner_ids, context=None): 
        #partners = self.browse(cr, uid, partner_ids, context)
        #print partner_ids
        #print "Testing: " ,  fields.date.context_today(cr, uid, context)
#        partners = self.browse(cr, uid, partner_ids, context)
#        partners2 = filter(lambda x: x.payment_action_date == False and x.payment_next_action == "" , partners)
#        partners2_ids = [x.id for x in partners2]
#        self.write(cr, uid, partner2_ids, {'payment_next_action_date': fields.date.context_today(cr, uid, context),}, context)
        for partner in self.browse(cr, uid, partner_ids, context):
            if (not partner.payment_next_action_date) and (not partner.payment_next_action) and (not partner.payment_responsible_id) :
                self.write(cr, uid, [partner.id], {'payment_next_action_date': fields.date.context_today(cr, uid, context), 
                                            'payment_next_action': partner.latest_followup_level_id_without_lit.manual_action_note, 
                                            'payment_responsible_id': partner.latest_followup_level_id_without_lit.action_responsible.id})

    def do_partner_print(self, cr, uid, partner_ids, data, context=None):
        #data.update({'date': context['date']})
        if not partner_ids: 
            return {}
        data['partner_ids'] = partner_ids
        datas = {
             'ids': [],
             'model': 'account_followup.followup',
             'form': data
        }
        return {
            'type': 'ir.actions.report.xml', 
            'report_name': 'account_followup.followup.print', 
            'datas': datas, 
            }

    def do_partner_mail(self, cr, uid, partner_ids, context=None):
        #get the mail template to use
        #mail_template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_followup', 'email_template_account_followup')
        mtp = self.pool.get('email.template')
        #mtp.subject = "Invoices overdue"
        #user_obj = self.pool.get('res.users')
        #mtp.email_from = user_obj.browse(cr, uid, uid, context=context)
        for partner in self.browse(cr, uid, partner_ids, context):
            #Get max level of ids
            print partner.id
            if partner.latest_followup_level_id_without_lit and partner.latest_followup_level_id_without_lit.email_template_id.id != False :                
                #print "From latest followup level", partner.latest_followup_level_id.email_template_id.id
                #print partner.id, "done"
                mtp.send_mail(cr, uid, partner.latest_followup_level_id_without_lit.email_template_id.id, partner.id, context=context)
            else:
                pass
                #print "From mail template", mail_template_id.id
                #mtp.send_mail(cr, uid, mail_template_id.id, partner.id, context=context)

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids,  {'payment_next_action_date': False, 'payment_next_action':'', 'payment_responsible_id': False}, context)
    
    def do_button_print(self, cr, uid, ids, context=None):      
        self.message_post(cr, uid, [ids[0]], body="Printed overdue payments report", context=context)
        datas = {
             'ids': ids,
             'model': 'res.partner',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.overdue',
            'datas': datas,
            'nodestroy' : True
        }
        
    
    def do_button_mail(self, cr, uid, ids, context=None):
        self.do_partner_mail(cr, uid, ids, context)
        
        
    def _get_aml_storeids(self, cr, uid, ids, context=None):
        partnerlist = []
        for aml in self.pool.get("account.move.line").browse(cr, uid, ids, context):
            if aml.partner_id not in partnerlist: 
                partnerlist.append(aml.partner_id.id)
        return partnerlist
    

    _inherit = "res.partner"
    _columns = {
        'payment_responsible_id':fields.many2one('res.users', ondelete='set null', string='Responsible', help="Responsible for making sure the action happens."), 
        #'payment_followup_level_id':fields.many2one('account_followup.followup.line', 'Followup line'),
        'payment_note':fields.text('Payment note', help="Payment Note"), 
        'payment_next_action':fields.char('Next Action', 50, help="This is the next action to be taken by the user.  It will automatically be set when the action fields are empty and the partner gets a follow-up level that requires a manual action. "), #Just a note
        'payment_next_action_date':fields.date('Next Action Date', help="This is when further follow-up is needed.  The date will have been set to the current date if the action fields are empty and the partner gets a follow-up level that requires a manual action. "), # next action date
        'accountmoveline_ids':fields.one2many('account.move.line', 'partner_id', domain=['&', ('reconcile_id', '=', False), '&', 
            ('account_id.active','=', True), '&', ('account_id.type', '=', 'receivable'), ('state', '!=', 'draft')]), 
        'latest_followup_date':fields.function(_get_latest_followup_date, method=True, type='date', string="Latest Follow-up Date", store={'account.move.line': (_get_aml_storeids, ['followup_line_id', 'followup_date'], 20)}, help="Latest date that the follow-up level of the partner was changed" ), #
        'latest_followup_level_id':fields.function(_get_latest_followup_level_id, method=True, 
            type='many2one', relation='account_followup.followup.line', string="Latest Follow-up Level", store={'account.move.line': (_get_aml_storeids, ['followup_line_id', 'followup_date'], 20)}, help="The maximum follow-up level"), 
        'latest_followup_level_id_without_lit':fields.function(_get_latest_followup_level_id_without_lit, method=True, 
            type='many2one', relation='account_followup.followup.line', string="Latest Follow-up Level without litigation", help="The maximum follow-up level without taking into account the account move lines with litigation"), 
        'next_followup_level_id':fields.function(_get_next_followup_level_id, method=True, type='many2one', relation='account_followup.followup.line', string="Next Level", help="The next follow-up level to come when the customer still refuses to pay",  store={'account.move.line': (_get_aml_storeids, ['followup_line_id', 'followup_date'], 20)}),
        'payment_amount_overdue':fields.function(_get_amount_overdue, method=True, type='float', string="Amount Overdue", help="Amount Overdue: The amount the customer should already have paid"),
    }

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
