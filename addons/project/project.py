# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2008 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id$
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

from lxml import etree
from mx import DateTime
from mx.DateTime import now
import time

from osv import fields, osv

class project(osv.osv):
    _name = "project.project"
    _description = "Project"

    def _calc_effective(self, cr, uid, ids, name, args, context):
        ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)])
        res_sum = {}
        if ids2:
            cr.execute('SELECT t.project_id, COALESCE(SUM(w.hours),0) \
                    FROM project_task t \
                        LEFT JOIN project_task_work w \
                            ON (w.task_id = t.id) \
                    WHERE t.project_id in (' + ','.join([str(x) for x in ids2]) + ') \
                        AND active \
                    GROUP BY project_id')
            for project_id, sum in cr.fetchall():
                res_sum[project_id] = sum
        res={}
        for id in ids:
            ids3 = self.search(cr, uid, [('parent_id', 'child_of', [id])])
            res.setdefault(id, 0.0)
            for idx in ids3:
                res[id] += res_sum.get(idx, 0.0)
        return res

    def _calc_planned(self, cr, uid, ids, name, args, context):
        ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)])
        res_sum = {}
        if ids2:
            cr.execute('SELECT project_id, COALESCE(SUM(total_hours),0) \
                    FROM project_task \
                    WHERE project_id IN (' + ','.join([str(x) for x in ids2]) + ') \
                        AND active \
                    GROUP BY project_id')
            for project_id, sum in cr.fetchall():
                res_sum[project_id] = sum
        res = {}
        for id in ids:
            ids3 = self.search(cr, uid, [('parent_id', 'child_of', [id])])
            res.setdefault(id, 0.0)
            for idx in ids3:
                res[id] += res_sum.get(idx, 0.0)
        return res

    def check_recursion(self, cursor, user, ids, parent=None):
        return super(project, self).check_recursion(cursor, user, ids,
                parent=parent)

    def onchange_partner_id(self, cr, uid, ids, part):
        if not part:
            return {'value':{'contact_id': False, 'pricelist_id': False}}
        addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['contact'])

        pricelist = self.pool.get('res.partner').browse(cr, uid, part).property_product_pricelist.id
        return {'value':{'contact_id': addr['contact'], 'pricelist_id': pricelist}}

    def _progress_rate(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res
        cr.execute('''SELECT
                project_id, sum(progress*total_hours), sum(total_hours) 
            FROM
                project_task 
            WHERE
                project_id in ('''+','.join(map(str,ids))+''') AND
                state<>'cancelled'
            GROUP BY
                project_id''')
        for id,prog,tot in cr.fetchall():
            if tot:
                res[id] = prog / tot
        return res

    def unlink(self, cr, uid, ids, *args, **kwargs):
        for proj in self.browse(cr, uid, ids):
            if proj.tasks:
                raise osv.except_osv(_('Operation Not Permited !'), _('You can not delete a project with tasks. I suggest you to desactivate it.'))
        return super(project, self).unlink(cr, uid, ids, *args, **kwargs)
    _columns = {
        'name': fields.char("Project Name", size=128, required=True),
        'active': fields.boolean('Active'),
        'category_id': fields.many2one('account.analytic.account','Analytic Account', help="Link this project to an analytic account if you need financial management on projects. It ables to connect projects with budgets, plannings, costs and revenues analysis, timesheet on projects, etc."),
        'priority': fields.integer('Sequence'),
        'manager': fields.many2one('res.users', 'Project Manager'),
        'warn_manager': fields.boolean('Warn Manager', help="If you check this field, the project manager will receive a request each time a task is completed by his team."),
        'members': fields.many2many('res.users', 'project_user_rel', 'project_id', 'uid', 'Project Members', help="Project's member. Not used in any computation, just for information purpose."),
        'tasks': fields.one2many('project.task', 'project_id', "Project tasks"),
        'parent_id': fields.many2one('project.project', 'Parent Project'),
        'child_id': fields.one2many('project.project', 'parent_id', 'Subproject'),
        'planned_hours': fields.function(_calc_planned, method=True, string='Planned hours', help="Sum of planned hours of all tasks related to this project."),
        'effective_hours': fields.function(_calc_effective, method=True, string='Hours spent', help="Sum of spent hours of all tasks related to this project."),
        'progress_rate': fields.function(_progress_rate, method=True, string='Progress', type='float', help="Percent of tasks closed according to the total of tasks todo."),
        'date_start': fields.date('Starting Date'),
        'date_end': fields.date('Expected End'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'contact_id': fields.many2one('res.partner.address', 'Contact'),
        'warn_customer': fields.boolean('Warn Partner', help="If you check this, the user will have a popup when closing a task that propose a message to send by email to the customer."),
        'warn_header': fields.text('Mail Header', help="Header added at the beginning of the email for the warning message sent to the customer when a task is closed."),
        'warn_footer': fields.text('Mail Footer', help="Footer added at the beginning of the email for the warning message sent to the customer when a task is closed."),
        'notes': fields.text('Notes', help="Internal description of the project."),
        'timesheet_id': fields.many2one('hr.timesheet.group', 'Working Time', help="Timetable working hours to adjust the gantt diagram report"),
        'state': fields.selection([('template', 'Template'), ('open', 'Open'), ('pending', 'Pending'), ('cancelled', 'Cancelled'), ('done', 'Done')], 'State', required=True, readonly=True),
     }

    _defaults = {
        'active': lambda *a: True,
        'manager': lambda object,cr,uid,context: uid,
        'priority': lambda *a: 1,
        'date_start': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'open'
    }

    _order = "priority"
    _constraints = [
        (check_recursion, 'Error ! You can not create recursive projects.', ['parent_id'])
    ]

    # toggle activity of projects, their sub projects and their tasks
    def set_template(self, cr, uid, ids, context={}):
        res = self.setActive(cr, uid, ids, value=False, context=context) 
        return res

    def set_done(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'done'}, context=context)
        return True

    def set_cancel(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'cancelled'}, context=context)
        return True

    def set_pending(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'pending'}, context=context)
        return True

    def set_open(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'open'}, context=context)
        return True

    def reset_project(self, cr, uid, ids, context={}):
        res = self.setActive(cr, uid, ids,value=True, context=context)
        return res

    def copy(self, cr, uid, id, default={},context={}):
        default = default or {}
        default['tasks'] = []
        default['child_id'] = []
        return super(project, self).copy(cr, uid, id, default, context)

    def duplicate_template(self, cr, uid, ids,context={}):
        for proj in self.browse(cr, uid, ids):
            parent_id=context.get('parent_id',False)
            new_id=self.pool.get('project.project').copy(cr, uid, proj.id,default={'name':proj.name+_(' (copy)'),'state':'open','parent_id':parent_id})
            cr.execute('select id from project_task where project_id=%d', (proj.id,))
            res = cr.fetchall()
            for (tasks_id,) in res:
                self.pool.get('project.task').copy(cr, uid, tasks_id,default={'project_id':new_id,'active':True}, context=context)
            cr.execute('select id from project_project where parent_id=%d', (proj.id,))
            res = cr.fetchall()
            project_ids = [x[0] for x in res]
            for child in project_ids:
                self.duplicate_template(cr, uid, [child],context={'parent_id':new_id}) 

        # TODO : Improve this to open the new project (using a wizard)

        cr.commit()
        raise osv.except_osv(_('Operation Done'), _('A new project has been created !\nWe suggest you to close this one and work on this new project.'))

    # set active value for a project, its sub projects and its tasks
    def setActive(self, cr, uid, ids, value=True, context={}):   
        for proj in self.browse(cr, uid, ids, context):            
            self.write(cr, uid, [proj.id], {'state': value and 'open' or 'template'}, context)
            cr.execute('select id from project_task where project_id=%d', (proj.id,))
            tasks_id = [x[0] for x in cr.fetchall()]
            if tasks_id:
                self.pool.get('project.task').write(cr, uid, tasks_id, {'active': value}, context)
            cr.execute('select id from project_project where parent_id=%d', (proj.id,))            
            project_ids = [x[0] for x in cr.fetchall()]            
            for child in project_ids:
                self.setActive(cr, uid, [child], value, context)     		
        return True
project()

class project_task_type(osv.osv):
    _name = 'project.task.type'
    _description = 'Project task type'
    _columns = {
        'name': fields.char('Type', required=True, size=64, translate=True),
        'description': fields.text('Description'),
    }
project_task_type()

class task(osv.osv):
    _name = "project.task"
    _description = "Task"
    _date_name = "date_start"
    def _str_get(self, task, level=0, border='***', context={}):
        return border+' '+(task.user_id and task.user_id.name.upper() or '')+(level and (': L'+str(level)) or '')+(' - %.1fh / %.1fh'%(task.effective_hours or 0.0,task.planned_hours))+' '+border+'\n'+ \
            border[0]+' '+(task.name or '')+'\n'+ \
            (task.description or '')+'\n\n'

    def _history_get(self, cr, uid, ids, name, args, context={}):
        result = {}
        for task in self.browse(cr, uid, ids, context=context):
            result[task.id] = self._str_get(task, border='===')
            t2 = task.parent_id
            level = 0
            while t2:
                level -= 1
                result[task.id] = self._str_get(t2, level) + result[task.id]
                t2 = t2.parent_id
            t3 = map(lambda x: (x,1), task.child_ids)
            while t3:
                t2 = t3.pop(0)
                result[task.id] = result[task.id] + self._str_get(t2[0], t2[1])
                t3 += map(lambda x: (x,t2[1]+1), t2[0].child_ids)
        return result

# Compute: effective_hours, total_hours, progress
    def _hours_get(self, cr, uid, ids, field_names, args, context):
        task_set = ','.join(map(str, ids))
        cr.execute(("SELECT task_id, COALESCE(SUM(hours),0) FROM project_task_work WHERE task_id in (%s) GROUP BY task_id") % (task_set,))
        hours = dict(cr.fetchall())
        res = {}
        for task in self.browse(cr, uid, ids, context=context):
            res[task.id] = {}
            res[task.id]['effective_hours'] = hours.get(task.id, 0.0)
            res[task.id]['total_hours'] = task.remaining_hours + hours.get(task.id, 0.0)
            if (task.remaining_hours + hours.get(task.id, 0.0)):
                res[task.id]['progress'] = min(100.0 * hours.get(task.id, 0.0) / res[task.id]['total_hours'], 100)
            else:
                res[task.id]['progress'] = 0.0
            res[task.id]['delay_hours'] = res[task.id]['total_hours'] - task.planned_hours
        return res

    def onchange_planned(self, cr, uid, ids, planned, effective):
        return {'value':{'remaining_hours': planned-effective}}

    #_sql_constraints = [
    #    ('remaining_hours', 'CHECK (remaining_hours>=0)', 'Please increase and review remaining hours ! It can not be smaller than 0.'),
    #]

    _columns = {
        'active': fields.boolean('Active'),
        'name': fields.char('Task summary', size=128, required=True),
        'description': fields.text('Description'),
        'priority' : fields.selection([('4','Very Low'), ('3','Low'), ('2','Medium'), ('1','Urgent'), ('0','Very urgent')], 'Importance'),
        'sequence': fields.integer('Sequence'),
        'type': fields.many2one('project.task.type', 'Type'),
        'state': fields.selection([('draft', 'Draft'),('open', 'Open'),('pending', 'Pending'), ('cancelled', 'Cancelled'), ('done', 'Done')], 'Status', readonly=True, required=True),
        'date_start': fields.datetime('Date Opened'),
        'date_deadline': fields.datetime('Deadline'),
        'date_close': fields.datetime('Date Closed', readonly=True),
        'project_id': fields.many2one('project.project', 'Project', ondelete='cascade'),
        'parent_id': fields.many2one('project.task', 'Parent Task'),
        'child_ids': fields.one2many('project.task', 'parent_id', 'Delegated Tasks'),
        'history': fields.function(_history_get, method=True, string="Task Details", type="text"),
        'notes': fields.text('Notes'),

        'planned_hours': fields.float('Planned Hours', readonly=True, states={'draft':[('readonly',False)]}, required=True, help='Estimated time to do the task, usually set by the project manager when the task is in draft state.'),
        'effective_hours': fields.function(_hours_get, method=True, string='Hours Spent', multi='hours', store=True, help="Computed using the sum of the task work done."),
        'remaining_hours': fields.float('Remaining Hours', digits=(16,2), help="Total remaining time, can be re-estimated periodically by the assignee of the task."),
        'total_hours': fields.function(_hours_get, method=True, string='Total Hours', multi='hours', store=True, help="Computed as: Time Spent + Remaining Time."),
        'progress': fields.function(_hours_get, method=True, string='Progress (%)', multi='hours', store=True, help="Computed as: Time Spent / Total Time."),
        'delay_hours': fields.function(_hours_get, method=True, string='Delay Hours', multi='hours', store=True, help="Computed as: Total Time - Estimated Time. It gives the difference of the time estimated by the project manager and the real time to close the task."),

        'user_id': fields.many2one('res.users', 'Assigned to'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'work_ids': fields.one2many('project.task.work', 'task_id', 'Work done', readonly=False, states={'draft':[('readonly',True)]}),
    }
    _defaults = {
        'user_id': lambda obj,cr,uid,context: uid,
        'state': lambda *a: 'draft',
        'priority': lambda *a: '2',
        'progress': lambda *a: 0,
        'sequence': lambda *a: 10,
        'active': lambda *a: True,
        'date_start': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _order = "sequence, priority, date_deadline, id"

    #
    # Override view according to the company definition
    #
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        tm = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.project_time_mode
        f = self.pool.get('res.company').fields_get(cr, uid, ['project_time_mode'], context)
        word = dict(f['project_time_mode']['selection'])[tm]

        res = super(task, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar)
        if tm=='hours':
            return res
        eview = etree.fromstring(res['arch'])
        def _check_rec(eview, tm):
            if eview.attrib.get('widget',False) == 'float_time':
                eview.set('widget','float')
            for child in eview:
                _check_rec(child, tm)
            return True
        _check_rec(eview, tm)
        res['arch'] = etree.tostring(eview)
        for f in res['fields']:
            if 'Hours' in res['fields'][f]['string']:
                res['fields'][f]['string'] = res['fields'][f]['string'].replace('Hours',word)
        return res

    def do_close(self, cr, uid, ids, *args):
        request = self.pool.get('res.request')
        tasks = self.browse(cr, uid, ids)
        for task in tasks:
            project = task.project_id
            if project:
                if project.warn_manager and project.manager and (project.manager.id != uid):
                    request.create(cr, uid, {
                        'name': "Task '%s' closed" % task.name,
                        'state': 'waiting',
                        'act_from': uid,
                        'act_to': project.manager.id,
                        'ref_partner_id': task.partner_id.id,
                        'ref_doc1': 'project.task,%d'% (task.id,),
                        'ref_doc2': 'project.project,%d'% (project.id,),
                    })
            self.write(cr, uid, [task.id], {'state': 'done', 'date_close':time.strftime('%Y-%m-%d %H:%M:%S'), 'remaining_hours': 0.0})
            if task.parent_id and task.parent_id.state in ('pending','draft'):
                self.do_reopen(cr, uid, [task.parent_id.id])
        return True

    def do_reopen(self, cr, uid, ids, *args):
        request = self.pool.get('res.request')
        tasks = self.browse(cr, uid, ids)
        for task in tasks:
            project = task.project_id
            if project and project.warn_manager and project.manager.id and (project.manager.id != uid):
                request.create(cr, uid, {
                    'name': "Task '%s' reopened" % task.name,
                    'state': 'waiting',
                    'act_from': uid,
                    'act_to': project.manager.id,
                    'ref_partner_id': task.partner_id.id,
                    'ref_doc1': 'project.task,%d' % task.id,
                    'ref_doc2': 'project.project,%d' % project.id,
                })

            self.write(cr, uid, [task.id], {'state': 'open'})
        return True

    def do_cancel(self, cr, uid, ids, *args):
        request = self.pool.get('res.request')
        tasks = self.browse(cr, uid, ids)
        for task in tasks:
            project = task.project_id
            if project.warn_manager and project.manager and (project.manager.id != uid):
                request.create(cr, uid, {
                    'name': "Task '%s' cancelled" % task.name,
                    'state': 'waiting',
                    'act_from': uid,
                    'act_to': project.manager.id,
                    'ref_partner_id': task.partner_id.id,
                    'ref_doc1': 'project.task,%d' % task.id,
                    'ref_doc2': 'project.project,%d' % project.id,
                })
            self.write(cr, uid, [task.id], {'state': 'cancelled', 'remaining_hours':0.0})
        return True

    def do_open(self, cr, uid, ids, *args):
        tasks= self.browse(cr,uid,ids)
        for t in tasks:
            self.write(cr, uid, [t.id], {'state': 'open'})
        return True

    def do_draft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        return True


    def do_pending(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'pending'})
        return True


task()

class project_work(osv.osv):
    _name = "project.task.work"
    _description = "Task Work"
    _columns = {
        'name': fields.char('Work summary', size=128),
        'date': fields.datetime('Date'),
        'task_id': fields.many2one('project.task', 'Task', ondelete='cascade', required=True),
        'hours': fields.float('Time Spent'),
        'user_id': fields.many2one('res.users', 'Done by', required=True),
    }
    _defaults = {
        'user_id': lambda obj,cr,uid,context: uid,
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S')
    }
    _order = "date desc"
    def create(self, cr, uid, vals, *args, **kwargs):
        if 'task_id' in vals:
            cr.execute('update project_task set remaining_hours=remaining_hours+%.2f where id=%d', (-vals.get('hours',0.0), vals['task_id']))
        return super(project_work,self).create(cr, uid, vals, *args, **kwargs)

    def write(self, cr, uid, ids,vals,context={}):
        for work in self.browse(cr, uid, ids, context):
            cr.execute('update project_task set remaining_hours=remaining_hours+%.2f+(%.2f) where id=%d', (-vals.get('hours',0.0), work.hours, work.task_id.id))
        return super(project_work,self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, *args, **kwargs):
        for work in self.browse(cr, uid, ids):
            cr.execute('update project_task set remaining_hours=remaining_hours+%.2f where id=%d', (work.hours, work.task_id.id))
        return super(project_work,self).unlink(cr, uid, ids,*args, **kwargs)
project_work()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

