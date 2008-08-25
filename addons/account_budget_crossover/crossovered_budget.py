# -*- encoding: utf-8 -*-
from osv import osv,fields
import tools
import netsvc
from mx import DateTime
import time
import datetime


def strToDate(dt):
        dt_date=datetime.date(int(dt[0:4]),int(dt[5:7]),int(dt[8:10]))
        return dt_date

class crossovered_budget(osv.osv):
    _name = "crossovered.budget"
    _description = "Crossovered Budget"

    _columns = {
        'name': fields.char('Name', size=50, required=True,states={'done':[('readonly',True)]}),
        'code': fields.char('Code', size=20, required=True,states={'done':[('readonly',True)]}),
        'creating_user_id': fields.many2one('res.users','Responsible User'),
        'validating_user_id': fields.many2one('res.users','Validate User', readonly=True),
        'date_from': fields.date('Start Date',required=True,states={'done':[('readonly',True)]}),
        'date_to': fields.date('End Date',required=True,states={'done':[('readonly',True)]}),
        'state' : fields.selection([('draft','Draft'),('confirm','Confirmed'),('validate','Validated'),('done','Done'),('cancel', 'Cancelled')], 'State', select=True, required=True, readonly=True),
        'crossovered_budget_line': fields.one2many('crossovered.budget.lines', 'crossovered_budget_id', 'Budget Lines',states={'done':[('readonly',True)]} ),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'creating_user_id': lambda self,cr,uid,context: uid,
    }

#   def action_set_to_draft(self, cr, uid, ids, *args):
#       self.write(cr, uid, ids, {'state': 'draft'})
#       wf_service = netsvc.LocalService('workflow')
#       for id in ids:
#           wf_service.trg_create(uid, self._name, id, cr)
#       return True

    def budget_confirm(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'state':'confirm'
        })
        return True

    def budget_validate(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'state':'validate',
            'validating_user_id': uid,
        })
        return True

    def budget_cancel(self, cr, uid, ids, *args):

        self.write(cr, uid, ids, {
            'state':'cancel'
        })
        return True

    def budget_done(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'state':'done'
        })
        return True

crossovered_budget()

class crossovered_budget_lines(osv.osv):

    def _pra_amt(self, cr, uid, ids,name,args,context):
        res = {}
        for line in self.browse(cr, uid, ids):
            acc_ids = ','.join([str(x.id) for x in line.general_budget_id.account_ids])
            if not acc_ids:
                raise osv.except_osv('Error!',"The General Budget '" + str(line.general_budget_id.name) + "' has no Accounts!" )
            date_to = line.date_to
            date_from = line.date_from
            if context.has_key('wizard_date_from'):
                date_from = context['wizard_date_from']
            if context.has_key('wizard_date_to'):
                date_to = context['wizard_date_to']
            cr.execute("select sum(amount) from account_analytic_line where account_id=%d and (date between to_date('%s','yyyy-mm-dd') and to_date('%s','yyyy-mm-dd')) and general_account_id in (%s)"%(line.analytic_account_id.id,date_from,date_to,acc_ids))
            result=cr.fetchone()[0]
            if result==None:
                result=0.00
            res[line.id]=result
        return res

    def _theo_amt(self, cr, uid, ids,name,args,context):
        res = {}
        for line in self.browse(cr, uid, ids):
            today=datetime.datetime.today()
            date_to = today.strftime("%Y-%m-%d")
            date_from = line.date_from
            if context.has_key('wizard_date_from'):
                date_from = context['wizard_date_from']
            if context.has_key('wizard_date_to'):
                date_to = context['wizard_date_to']

            if line.paid_date:
                if strToDate(date_to)<=strToDate(line.paid_date):
                    theo_amt=0.00
                else:
                    theo_amt=line.planned_amount
            else:
                total=strToDate(line.date_to) - strToDate(line.date_from)
                elapsed = min(strToDate(line.date_to),strToDate(date_to)) - max(strToDate(line.date_from),strToDate(date_from))
                if strToDate(date_to) < strToDate(line.date_from):
                    elapsed = strToDate(date_to) - strToDate(date_to)

                theo_amt=float(elapsed.days/float(total.days))*line.planned_amount

            res[line.id]=theo_amt
        return res

    def _perc(self, cr, uid, ids,name,args,context):
        res = {}
        for line in self.browse(cr, uid, ids):
            if line.theoritical_amount<>0.00:
                res[line.id]=float(line.practical_amount / line.theoritical_amount)*100
            else:
                res[line.id]=0.00
        return res
    _name="crossovered.budget.lines"
    _description = "Crossovered Budget Lines"
    _columns = {
        'crossovered_budget_id': fields.many2one('crossovered.budget', 'Budget Ref', ondelete='cascade', select=True, required=True),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account Ref',required=True),
        'general_budget_id': fields.many2one('account.budget.post', 'Master Budget Ref',required=True),
        'date_from': fields.date('Start Date',required=True),
        'date_to': fields.date('End Date',required=True),
        'paid_date': fields.date('Paid Date'),
        'planned_amount':fields.float('Planned Amount',required=True),
        'practical_amount':fields.function(_pra_amt,method=True, string='Practical Amount',type='float'),
        'theoritical_amount':fields.function(_theo_amt,method=True, string='Theoritical Amount',type='float'),
        'percentage':fields.function(_perc,method=True, string='Percentage',type='float'),
    }
crossovered_budget_lines()

class account_budget_post(osv.osv):
    _name = 'account.budget.post'
    _inherit = 'account.budget.post'
    _columns = {
    'crossovered_budget_line': fields.one2many('crossovered.budget.lines', 'general_budget_id', 'Budget Lines'),
    }
account_budget_post()

class account_budget_post_dotation(osv.osv):
    _name = 'account.budget.post.dotation'
    _inherit = 'account.budget.post.dotation'

    def _tot_planned(self, cr, uid, ids,name,args,context):
        res={}
        for line in self.browse(cr, uid, ids):
            if line.period_id:
                obj_period=self.pool.get('account.period').browse(cr, uid,line.period_id.id)

                total_days=strToDate(obj_period.date_stop) - strToDate(obj_period.date_start)
                budget_id=line.post_id and line.post_id.id or False
                query="select id from crossovered_budget_lines where  general_budget_id= '"+ str(budget_id) + "' AND (date_from  >='"  +obj_period.date_start +"'  and date_from <= '"+obj_period.date_stop + "') OR (date_to  >='"  +obj_period.date_start +"'  and date_to <= '"+obj_period.date_stop + "') OR (date_from  <'"  +obj_period.date_start +"'  and date_to > '"+obj_period.date_stop + "')"
                cr.execute(query)
                res1=cr.fetchall()

                tot_planned=0.00
                for record in res1:
                    obj_lines = self.pool.get('crossovered.budget.lines').browse(cr, uid,record[0])
                    count_days = min(strToDate(obj_period.date_stop),strToDate(obj_lines.date_to)) - max(strToDate(obj_period.date_start), strToDate(obj_lines.date_from))
                    days_in_period = count_days.days +1
                    count_days = strToDate(obj_lines.date_to) - strToDate(obj_lines.date_from)
                    total_days_of_rec = count_days.days +1
                    tot_planned += obj_lines.planned_amount/total_days_of_rec* days_in_period
                res[line.id]=tot_planned
            else:
                res[line.id]=0.00
        return res

    _columns = {
    'tot_planned':fields.function(_tot_planned,method=True, string='Total Planned Amount',type='float',store=True),
    }

account_budget_post_dotation()

class account_analytic_account(osv.osv):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'

    _columns = {
    'crossovered_budget_line': fields.one2many('crossovered.budget.lines', 'analytic_account_id', 'Budget Lines'),
    }

account_analytic_account()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

