

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
import os
import datetime
from lxml import etree
from time import strftime

import tools
import netsvc
from osv import osv
from osv import fields
from tools import to_xml
from tools.translate import _

class survey_question_wiz(osv.osv_memory):
    _name = 'survey.question.wiz'
    _columns = {
        'name': fields.integer('Number'),
    }
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False,submenu=False):
        """
        Fields View Get method :- generate the new view and display the survey pages of selected survey. 
       
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param view_id : view id of the current object.
        @param view_type : which type of view is create. like :- form, tree ,search etc...
        @param context: A standard dictionary for contextual values
        @return : Dictionary value for created view of particular survey pages.
        """
        
        result = super(survey_question_wiz, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar,submenu)
        
        surv_name_wiz = self.pool.get('survey.name.wiz')
        survey_obj = self.pool.get('survey')
        page_obj = self.pool.get('survey.page')
        que_obj = self.pool.get('survey.question')
        ans_obj = self.pool.get('survey.answer')
        sur_response_obj = self.pool.get('survey.response')
        que_col_head = self.pool.get('survey.question.column.heading')
        user_obj = self.pool.get('res.users')

        if view_type in ['form']:
            wiz_id = 0
            if not context.has_key('sur_name_id'):
                res_data = {
                    'survey_id' : context.get('survey_id', False),
                    'page_no' :-1,
                    'page':'next',
                    'transfer' :1,
                    'response':0
                }
                wiz_id = surv_name_wiz.create(cr, uid, res_data)
                #TODO: change to the browse, use read if only need to read few columns values
                sur_name_rec = surv_name_wiz.read(cr, uid, wiz_id, [])
                context.update({'sur_name_id' :wiz_id})
            else:
                sur_name_rec = surv_name_wiz.read(cr, uid, context.get('sur_name_id', False))

            if context.has_key('active_id'):
                context.pop('active_id')

            survey_id = context.get('survey_id', False)
            #TODO: change to the browse, use read if only need to read few columns values
            # this will fire select * from quary 
            sur_rec = survey_obj.read(cr, uid, survey_id, [])
            p_id = sur_rec['page_ids']
            total_pages = len(p_id)
            pre_button = False
            readonly = 0

            if context.has_key('response_id') and context.get('response_id', False) and int(context['response_id'][0]) > 0:
                readonly = 1

            if not sur_name_rec['page_no'] + 1 :
                surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'store_ans':{}})

            sur_name_read = surv_name_wiz.read(cr, uid, context.get('sur_name_id',False))
            page_number = int(sur_name_rec['page_no'])
            if sur_name_read['transfer'] or not sur_name_rec['page_no'] + 1:
                surv_name_wiz.write(cr, uid, [context.get('sur_name_id', False)], {'transfer':False})
                flag = False
                fields = {}
                if sur_name_read['page'] == "next" or sur_name_rec['page_no'] == -1:
                    if total_pages > sur_name_rec['page_no'] + 1:
                        if ((context.has_key('active') and not context.get('active', False)) or not context.has_key('active')) and not sur_name_rec['page_no'] + 1:
                            if sur_rec['state'] != "open" :
                                raise osv.except_osv(_('Warning !'),_("You can not give answer because of survey is not open for answer"))
                            cr.execute('select count(id) from survey_history where user_id=%s\
                                                    and survey_id=%s' % (uid,survey_id))
                            res = cr.fetchone()[0]
                            user_limit = survey_obj.read(cr, uid, survey_id, ['response_user'])['response_user']
                            if user_limit and res >= user_limit:
                                raise osv.except_osv(_('Warning !'),_("You can not give response for this survey more than %s times") % (user_limit))

                        if sur_rec['max_response_limit'] and sur_rec['max_response_limit'] <= sur_rec['tot_start_survey'] and not sur_name_rec['page_no'] + 1:
                            survey_obj.write(cr, uid, survey_id, {'state':'close', 'date_close':strftime("%Y-%m-%d %H:%M:%S")})

                        p_id = p_id[sur_name_rec['page_no'] + 1]
                        surv_name_wiz.write(cr, uid, [context.get('sur_name_id', False)], {'page_no' : sur_name_rec['page_no'] + 1})
                        flag = True
                        page_number += 1
                    if sur_name_rec['page_no'] > - 1:
                        pre_button = True
                else:
                    if sur_name_rec['page_no'] != 0:
                        p_id = p_id[sur_name_rec['page_no'] - 1]
                        surv_name_wiz.write(cr, uid, [context.get('sur_name_id', False)], {'page_no' : sur_name_rec['page_no'] - 1})
                        flag = True
                        page_number -= 1

                    if sur_name_rec['page_no'] > 1:
                        pre_button = True
                if flag:
                    pag_rec = page_obj.read(cr, uid, p_id)
                    xml_form = etree.Element('form', {'string': _(tools.ustr(pag_rec['title']))})
                    xml_group = etree.SubElement(xml_form, 'group', {'col': '1', 'colspan': '4'})
                    if context.has_key('response_id') and context.get('response_id', False)  and int(context.get('response_id',0)[0]) > 0:
                        xml_group = etree.SubElement(xml_form, 'group', {'col': '40', 'colspan': '4'})
                        record = sur_response_obj.browse(cr, uid, context['response_id'][context['response_no']])
                        etree.SubElement(xml_group, 'label', {'string': to_xml(tools.ustr('Answer Of :- ' + record.user_id.name + ',  Date :- ' + record.date_create.split('.')[0]  )), 'align':"0.0"})
                        etree.SubElement(xml_group, 'label', {'string': to_xml(tools.ustr(" Response :- " + str(context.get('response_no',0) + 1) +"/" + str(len(context.get('response_id',0))) )), 'align':"0.0"})
                        if context.get('response_no',0) > 0:
                            etree.SubElement(xml_group, 'button', {'colspan':"1",'icon':"gtk-go-back",'name':"action_forward_previous",'string': tools.ustr("Previous Answer"),'type':"object"})
                        if context.get('response_no',0) + 1 < len(context.get('response_id',0)):
                            etree.SubElement(xml_group, 'button', {'colspan':"1",'icon': "gtk-go-forward", 'name':"action_forward_next",'string': tools.ustr("Next Answer") ,'type':"object",'context' : tools.ustr(context)})

                    if wiz_id:
                        fields["wizardid_" + str(wiz_id)] = {'type':'char', 'size' : 255, 'string':"", 'views':{}}
                        etree.SubElement(xml_form, 'field', {'invisible':'1','name': "wizardid_" + str(wiz_id),'default':str(lambda *a: 0)})

                    if pag_rec['note']:
                        xml_group = etree.SubElement(xml_form, 'group', {'col': '1', 'colspan': '4'})
                        for que_test in pag_rec['note'].split('\n'):
                            etree.SubElement(xml_group, 'label', {'string': to_xml(tools.ustr(que_test)), 'align':"0.0"})
                    que_ids = pag_rec['question_ids']
                    qu_no = 0

                    for que in que_ids:
                        qu_no += 1
                        que_rec = que_obj.read(cr, uid, que)
                        descriptive_text = ""
                        separator_string = tools.ustr(qu_no) + "." + tools.ustr(que_rec['question'])
                        if ((context.has_key('active') and not context.get('active',False)) or not context.has_key('active')) and que_rec['is_require_answer']:
                            star = '*'
                        else:
                            star = ''
                        xml_group = etree.SubElement(xml_form, 'group', {'col': '2', 'colspan': '4'})

                        if context.has_key('active') and context.get('active',False) and context.has_key('edit'):
                            xml_group = etree.SubElement(xml_form, 'group', {'col': '1', 'colspan': '2'})
                            etree.SubElement(xml_group, 'separator', {'string': star+to_xml(separator_string), 'colspan': '3'})
                            xml_group1 = etree.SubElement(xml_form, 'group', {'col': '2', 'colspan': '2'})
                            context.update({'question_id' : tools.ustr(que),'page_number' : sur_name_rec['page_no'] , 'transfer' : sur_name_read['transfer'], 'page_id' : p_id})
                            etree.SubElement(xml_group1, 'button', {'string' :'','icon': "gtk-edit", 'type' :'object', 'name':"action_edit_question", 'context' : tools.ustr(context)})
                            etree.SubElement(xml_group1, 'button', {'string' :'','icon': "gtk-delete", 'type' :'object','name':"action_delete_question", 'context' : tools.ustr(context)})
                        else:
                            xml_group = etree.SubElement(xml_form, 'group', {'col': '1', 'colspan': '4'})
                            etree.SubElement(xml_group, 'separator', {'string': star+to_xml(separator_string), 'colspan': '4'})

                        ans_ids = ans_obj.read(cr, uid, que_rec['answer_choice_ids'], [])
                        xml_group = etree.SubElement(xml_form, 'group', {'col': '1', 'colspan': '4'})

                        if que_rec['type'] == 'multiple_choice_only_one_ans':
                            selection = []
                            for ans in ans_ids:
                                selection.append((tools.ustr(ans['id']), ans['answer']))
                            xml_group = etree.SubElement(xml_group, 'group', {'col': '2', 'colspan': '2'})
                            etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_selection"})
                            fields[tools.ustr(que) + "_selection"] = {'type':'selection', 'selection' :selection, 'string':"Answer"}

                        elif que_rec['type'] == 'multiple_choice_multiple_ans':
                            xml_group = etree.SubElement(xml_group, 'group', {'col': '4', 'colspan': '4'})
                            for ans in ans_ids:
                                etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_" + tools.ustr(ans['id'])})
                                fields[tools.ustr(que) + "_" + tools.ustr(ans['id'])] = {'type':'boolean', 'string':ans['answer']}

                        elif que_rec['type'] in ['matrix_of_choices_only_one_ans', 'rating_scale']:
                            if que_rec['comment_column']:
                                col = "4"
                                colspan = "4"
                            else:
                               col = "2"
                               colspan = "2"
                            xml_group = etree.SubElement(xml_group, 'group', {'col': tools.ustr(col), 'colspan': tools.ustr(colspan)})
                            for row in ans_ids:
                                etree.SubElement(xml_group, 'newline')
                                etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_selection_" + tools.ustr(row['id']),'string':to_xml(tools.ustr(row['answer']))})
                                selection = [('','')]
                                for col in que_col_head.read(cr, uid, que_rec['column_heading_ids']):
                                    selection.append((str(col['id']), col['title']))
                                fields[tools.ustr(que) + "_selection_" + tools.ustr(row['id'])] = {'type':'selection', 'selection' : selection, 'string': "Answer"}
                                if que_rec['comment_column']:
                                   fields[tools.ustr(que) + "_commentcolumn_"+tools.ustr(row['id']) + "_field"] = {'type':'char', 'size' : 255, 'string':tools.ustr(que_rec['column_name']), 'views':{}}
                                   etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_commentcolumn_"+tools.ustr(row['id'])+ "_field"})

                        elif que_rec['type'] == 'matrix_of_choices_only_multi_ans':
                            xml_group = etree.SubElement(xml_group, 'group', {'col': str(len(que_rec['column_heading_ids']) + 1), 'colspan': '4'})
                            etree.SubElement(xml_group, 'separator', {'string': '.','colspan': '1'})
                            for col in que_col_head.read(cr, uid, que_rec['column_heading_ids']):
                                etree.SubElement(xml_group, 'separator', {'string': tools.ustr(col['title']),'colspan': '1'})
                            for row in ans_ids:
                                etree.SubElement(xml_group, 'label', {'string': to_xml(tools.ustr(row['answer'])) +' :-', 'align': '0.0'})
                                for col in que_col_head.read(cr, uid, que_rec['column_heading_ids']):
                                    etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_" + tools.ustr(row['id']) + "_" + tools.ustr(col['id']), 'nolabel':"1"})
                                    fields[tools.ustr(que) + "_" + tools.ustr(row['id'])  + "_" + tools.ustr(col['id'])] = {'type':'boolean', 'string': col['title']}

                        elif que_rec['type'] == 'matrix_of_drop_down_menus':
                            xml_group = etree.SubElement(xml_group, 'group', {'col': str(len(que_rec['column_heading_ids']) + 1), 'colspan': '4'})
                            etree.SubElement(xml_group, 'separator', {'string': '.','colspan': '1'})
                            for col in que_col_head.read(cr, uid, que_rec['column_heading_ids']):
                                etree.SubElement(xml_group, 'separator', {'string': tools.ustr(col['title']),'colspan': '1'})
                            for row in ans_ids:
                                etree.SubElement(xml_group, 'label', {'string': to_xml(tools.ustr(row['answer']))+' :-', 'align': '0.0'})
                                for col in que_col_head.read(cr, uid, que_rec['column_heading_ids']):
                                    selection = []
                                    if col['menu_choice']:
                                        for item in col['menu_choice'].split('\n'):
                                            if item and not item.strip() == '': selection.append((item ,item))
                                    etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_" + tools.ustr(row['id']) + "_" + tools.ustr(col['id']),'nolabel':'1'})
                                    fields[tools.ustr(que) + "_" + tools.ustr(row['id'])  + "_" + tools.ustr(col['id'])] = {'type':'selection', 'string': col['title'], 'selection':selection}

                        elif que_rec['type'] == 'multiple_textboxes':
                            xml_group = etree.SubElement(xml_group, 'group', {'col': '4', 'colspan': '4'})
                            type = "char"
                            if que_rec['is_validation_require']:
                                if que_rec['validation_type'] in ['must_be_whole_number']:
                                    type = "integer"
                                elif que_rec['validation_type'] in ['must_be_decimal_number']:
                                    type = "float"
                                elif que_rec['validation_type'] in ['must_be_date']:
                                    type = "date"
                            for ans in ans_ids:
                                etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'width':"300",'colspan': '1','name': tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_multi"})
                                if type == "char" :
                                    fields[tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_multi"] = {'type':'char', 'size':255, 'string':ans['answer']}
                                else:
                                    fields[tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_multi"] = {'type': str(type), 'string':ans['answer']}

                        elif que_rec['type'] == 'numerical_textboxes':
                            xml_group = etree.SubElement(xml_group, 'group', {'col': '4', 'colspan': '4'})
                            for ans in ans_ids:
                                etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'width':"300",'colspan': '1','name': tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_numeric"})
                                fields[tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_numeric"] = {'type':'integer', 'string':ans['answer']}

                        elif que_rec['type'] == 'date':
                            xml_group = etree.SubElement(xml_group, 'group', {'col': '4', 'colspan': '4'})
                            for ans in ans_ids:
                                etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'width':"300",'colspan': '1','name': tools.ustr(que) + "_" + tools.ustr(ans['id'])})
                                fields[tools.ustr(que) + "_" + tools.ustr(ans['id'])] = {'type':'date', 'string':ans['answer']}

                        elif que_rec['type'] == 'date_and_time':
                            xml_group = etree.SubElement(xml_group, 'group', {'col': '4', 'colspan': '4'})
                            for ans in ans_ids:
                                etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'width':"300",'colspan': '1','name': tools.ustr(que) + "_" + tools.ustr(ans['id'])})
                                fields[tools.ustr(que) + "_" + tools.ustr(ans['id'])] = {'type':'datetime', 'string':ans['answer']}

                        elif que_rec['type'] == 'descriptive_text':
                            for que_test in que_rec['descriptive_text'].split('\n'):
                                etree.SubElement(xml_group, 'label', {'string': to_xml(tools.ustr(que_test)), 'align':"0.0"})

                        elif que_rec['type'] == 'single_textbox':
                            etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_single", 'nolabel':"1" ,'colspan':"4"})
                            fields[tools.ustr(que) + "_single"] = {'type':'char', 'size' : 255, 'string':"single_textbox", 'views':{}}

                        elif que_rec['type'] == 'comment':
                            etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_comment", 'nolabel':"1" ,'colspan':"4"})
                            fields[tools.ustr(que) + "_comment"] = {'type':'text', 'string':"Comment/Eassy Box", 'views':{}}

                        elif que_rec['type'] == 'table':
                            xml_group = etree.SubElement(xml_group, 'group', {'col': str(len(que_rec['column_heading_ids'])), 'colspan': '4'})
                            for col in que_col_head.read(cr, uid, que_rec['column_heading_ids']):
                                etree.SubElement(xml_group, 'separator', {'string': tools.ustr(col['title']),'colspan': '1'})
                            for row in range(0,que_rec['no_of_rows']):
                                for col in que_col_head.read(cr, uid, que_rec['column_heading_ids']):
                                    etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_table_" + tools.ustr(col['id']) +"_"+ tools.ustr(row), 'nolabel':"1"})
                                    fields[tools.ustr(que) + "_table_" + tools.ustr(col['id']) +"_"+ tools.ustr(row)] = {'type':'char','size':255,'views':{}}

                        elif que_rec['type'] == 'multiple_textboxes_diff_type':
                            xml_group = etree.SubElement(xml_group, 'group', {'col': '4', 'colspan': '4'})
                            for ans in ans_ids:
                                if ans['type'] == "email" :
                                    fields[tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_multi"] = {'type':'char', 'size':255, 'string':ans['answer']}
                                    etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'widget':'email','width':"300",'colspan': '1','name': tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_multi"})
                                else:
                                    etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'width':"300",'colspan': '1','name': tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_multi"})
                                    if ans['type'] == "char" :
                                        fields[tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_multi"] = {'type':'char', 'size':255, 'string':ans['answer']}
                                    elif ans['type'] in ['integer','float','date','datetime']:
                                        fields[tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_multi"] = {'type': str(ans['type']), 'string':ans['answer']}
                                    else:
                                        selection = []
                                        if ans['menu_choice']:
                                            for item in ans['menu_choice'].split('\n'):
                                                if item and not item.strip() == '': selection.append((item ,item))
                                        fields[tools.ustr(que) + "_" + tools.ustr(ans['id']) + "_multi"] = {'type':'selection', 'selection' : selection, 'string':ans['answer']}

                        if que_rec['type'] in ['multiple_choice_only_one_ans', 'multiple_choice_multiple_ans', 'matrix_of_choices_only_one_ans', 'matrix_of_choices_only_multi_ans', 'matrix_of_drop_down_menus', 'rating_scale'] and que_rec['is_comment_require']:
                            if que_rec['type'] in ['multiple_choice_only_one_ans', 'multiple_choice_multiple_ans'] and que_rec['comment_field_type'] in ['char','text'] and que_rec['make_comment_field']:
                                etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_otherfield", 'colspan':"4"})
                                fields[tools.ustr(que) + "_otherfield"] = {'type':'boolean', 'string':que_rec['comment_label'], 'views':{}}
                                if que_rec['comment_field_type'] == 'char':
                                    etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_other", 'nolabel':"1" ,'colspan':"4"})
                                    fields[tools.ustr(que) + "_other"] = {'type': 'char', 'string': '', 'size':255, 'views':{}}
                                elif que_rec['comment_field_type'] == 'text':
                                    etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_other", 'nolabel':"1" ,'colspan':"4"})
                                    fields[tools.ustr(que) + "_other"] = {'type': 'text', 'string': '', 'views':{}}
                            else:
                                if que_rec['comment_field_type'] == 'char':
                                    etree.SubElement(xml_group, 'label', {'string': to_xml(tools.ustr(que_rec['comment_label'])),'colspan':"4"})
                                    etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_other", 'nolabel':"1" ,'colspan':"4"})
                                    fields[tools.ustr(que) + "_other"] = {'type': 'char', 'string': '', 'size':255, 'views':{}}
                                elif que_rec['comment_field_type'] == 'text':
                                    etree.SubElement(xml_group, 'label', {'string': to_xml(tools.ustr(que_rec['comment_label'])),'colspan':"4"})
                                    etree.SubElement(xml_group, 'field', {'readonly' :str(readonly), 'name': tools.ustr(que) + "_other", 'nolabel':"1" ,'colspan':"4"})
                                    fields[tools.ustr(que) + "_other"] = {'type': 'text', 'string': '', 'views':{}}

                    etree.SubElement(xml_form, 'separator', {'colspan': '4'})
                    xml_group = etree.SubElement(xml_form, 'group', {'col': '6', 'colspan': '4'})
                    etree.SubElement(xml_group, 'field', {'name': 'progress_bar_' + tools.ustr(page_number) , 'widget':'progressbar'})
                    fields['progress_bar_' + tools.ustr(page_number)] = {'type':'float', 'string':"Progress", 'views':{}}
                    etree.SubElement(xml_group, 'label', {'string': tools.ustr(page_number+ 1) + "/" + tools.ustr(total_pages)})
                    etree.SubElement(xml_group, 'button', {'icon': "gtk-cancel", 'special': "cancel",'string':"Cancel"})

                    if pre_button:
                        etree.SubElement(xml_group, 'button', {'colspan':"1",'icon':"gtk-go-back",'name':"action_previous",'string':"Previous",'type':"object"})
                    but_string = "Next"
                    if int(page_number) + 1 == total_pages:
                        but_string = "Done"

                    if context.has_key('active') and context.get('active',False) and int(page_number) + 1 == total_pages and context.has_key('response_id') and context.has_key('response_no') and  context.get('response_no',0) + 1 == len(context.get('response_id',0)):
                        etree.SubElement(xml_group, 'button', {'icon': "gtk-go-forward", 'special' : 'cancel','string': tools.ustr("Done") ,'context' : tools.ustr(context)})
                    elif context.has_key('active') and context.get('active', False) and int(page_number) + 1 == total_pages and context.has_key('response_id'):
                        etree.SubElement(xml_group, 'button', {'icon': "gtk-go-forward", 'name':"action_forward_next",'string': tools.ustr("Next Answer") ,'type':"object",'context' : tools.ustr(context)})
                    elif context.has_key('active') and context.get('active',False) and int(page_number) + 1 == total_pages:
                        etree.SubElement(xml_group, 'button', {'icon': "gtk-go-forward", 'special': "cancel", 'string' : 'Done', 'context' : tools.ustr(context)})
                    else:
                        etree.SubElement(xml_group, 'button', {'icon': "gtk-go-forward", 'name':"action_next",'string': tools.ustr(but_string) ,'type':"object",'context' : tools.ustr(context)})

                    if context.has_key('active') and context.get('active',False) and context.has_key('edit'):
                        etree.SubElement(xml_form, 'separator', {'string' : '','colspan': '4'})
                        context.update({'page_id' : tools.ustr(p_id),'page_number' : sur_name_rec['page_no'] , 'transfer' : sur_name_read['transfer']})
                        xml_group3 = etree.SubElement(xml_form, 'group', {'col': '4', 'colspan': '4'})
                        etree.SubElement(xml_group3, 'button', {'string' :'Add Page','icon': "gtk-new", 'type' :'object','name':"action_new_page", 'context' : tools.ustr(context)})
                        etree.SubElement(xml_group3, 'button', {'string' :'Edit Page','icon': "gtk-edit", 'type' :'object','name':"action_edit_page", 'context' : tools.ustr(context)})
                        etree.SubElement(xml_group3, 'button', {'string' :'Delete Page','icon': "gtk-delete", 'type' :'object','name':"action_delete_page", 'context' : tools.ustr(context)})
                        etree.SubElement(xml_group3, 'button', {'string' :'Add Question','icon': "gtk-new", 'type' :'object','name':"action_new_question", 'context' : tools.ustr(context)})

                    root = xml_form.getroottree()
                    result['arch'] = etree.tostring(root)
                    result['fields'] = fields
                    result['context'] = context
                else:
                    survey_obj.write(cr, uid, survey_id, {'tot_comp_survey' : sur_rec['tot_comp_survey'] + 1})
                    sur_response_obj.write(cr, uid, [sur_name_read['response']], {'state' : 'done'})

                    if sur_rec['send_response']:
                        survey_data = survey_obj.browse(cr, uid, int(survey_id))
                        response_id = surv_name_wiz.read(cr,uid,context.get('sur_name_id',False))['response']
                        context.update({'response_id':response_id})
                        report = self.create_report(cr, uid, [int(survey_id)], 'report.survey.browse.response', survey_data.title,context)
                        attachments = []
                        file = open(tools.config['addons_path'] + '/survey/report/' + survey_data.title + ".pdf")
                        file_data = ""
                        while 1:
                            line = file.readline()
                            file_data += line
                            if not line:
                                break

                        attachments.append((survey_data.title + ".pdf",file_data))
                        file.close()
                        os.remove(tools.config['addons_path'] + '/survey/report/' + survey_data.title + ".pdf")
                        user_email = False
                        resp_email = False

                        if user_obj.browse(cr, uid, uid).address_id.id:
                            cr.execute("select email from res_partner_address where id =%d" % user_obj.browse(cr, uid, uid).address_id.id)
                            user_email = cr.fetchone()[0]
                        resp_id = survey_data.responsible_id.address_id

                        if resp_id:
                            cr.execute("select email from res_partner_address where id =%d" % resp_id.id)
                            resp_email = cr.fetchone()[0]
                        if user_email and resp_email:
                            mail = "Hello " + survey_data.responsible_id.name + ",\n\n " + str(user_obj.browse(cr, uid, uid).name) + " Give Response Of " + survey_data.title + " Survey.\n\n Thanks,"
                            tools.email_send(user_email, [resp_email], "Survey Response Of " + str(user_obj.browse(cr, uid, uid).name) , mail, attach = attachments)

                    xml_form = etree.Element('form', {'string': _('Complete Survey Response')})
                    etree.SubElement(xml_form, 'separator', {'string': 'Complete Survey', 'colspan': "4"})
                    etree.SubElement(xml_form, 'label', {'string': 'Thanks for your response'})
                    etree.SubElement(xml_form, 'newline')
                    etree.SubElement(xml_form, 'button', {'icon': "gtk-go-forward", 'special':"cancel",'string':"OK",'colspan':"2"})
                    root = xml_form.getroottree()
                    result['arch'] = etree.tostring(root)
                    result['fields'] = {}
                    result['context'] = context
        return result

    def create_report(self, cr, uid, res_ids, report_name=False, file_name=False, context=None):
        """
           If any user give answer of survey then last create report of this answer and if 'E-mail Notification on Response' set True in survey  then send mail on responsible person of this survey and attach survey answer report in pdf format.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param res_ids: List of survey answer IDs,
            @param report_name: name of the report,
            @param file_name: To give file name of the report,
            @param context: A standard dictionary for contextual values,
            @return : Dictionary value for created report with file name.
        """
        if not report_name or not res_ids:
            return (False, Exception('Report name and Resources ids are required !!!'))
        try:
            ret_file_name = tools.config['addons_path'] + '/survey/report/' + file_name + '.pdf'
            service = netsvc.LocalService(report_name);
            (result, format) = service.create(cr, uid, res_ids, {}, context)
            fp = open(ret_file_name, 'wb+');
            fp.write(result);
            fp.close();

        except Exception,e:
            print 'Exception in create report:',e
            return (False, str(e))

        return (True, ret_file_name)

    def default_get(self, cr, uid, fields_list, context=None):
        """
            Assign Default value in particular field. If Browse Answers wizard run then read the value into database and Assigne to a particular fields.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param fields_list: List of fields of current view,
            @param context: A standard dictionary for contextual values,
            @return : Dictionary value for fields list with value.
        """
        value = {}
        for field in fields_list:
            if field.split('_')[0] == 'progress':
                tot_page_id = self.pool.get('survey').browse(cr, uid, context.get('survey_id',False))
                tot_per = (float(100) * (int(field.split('_')[2]) + 1) / len(tot_page_id.page_ids))
                value[field] = tot_per
        response_obj = self.pool.get('survey.response')
        surv_name_wiz = self.pool.get('survey.name.wiz')
        
        if context.has_key('response_id') and context.get('response_id') and int(context['response_id'][0]) > 0:
            data = super(survey_question_wiz, self).default_get(cr, uid, fields_list, context)
            response_ans = response_obj.browse(cr, uid, context['response_id'][context['response_no']])
            fields_list.sort()

            for que in response_ans.question_ids:
                for field in fields_list:
                    if field.split('_')[0] != "progress" and field.split('_')[0] == str(que.question_id.id):
                        if que.response_answer_ids and len(field.split('_')) == 4 and field.split('_')[1] == "commentcolumn" and field.split('_')[3] == "field":
                            for ans in que.response_answer_ids:
                                if str(field.split('_')[2]) == str(ans.answer_id.id):
                                    value[field] = ans.comment_field

                        if que.response_table_ids and len(field.split('_')) == 4 and field.split('_')[1] == "table":
                            for ans in que.response_table_ids:
                                if str(field.split('_')[2]) == str(ans.column_id.id) and str(field.split('_')[3]) ==  str(ans.name):
                                    value[field] = ans.value

                        if que.comment and (field.split('_')[1] == "comment" or field.split('_')[1] == "other"):
                            value[field] = str(que.comment)

                        elif que.single_text and field.split('_')[1] == "single":
                            value[field] = str(que.single_text)

                        elif que.response_answer_ids and len(field.split('_')) == 3 and field.split('_')[1] == "selection":
                            for ans in que.response_answer_ids:
                                if str(field.split('_')[2]) == str( ans.answer_id.id):
                                    value[field] = str(ans.column_id.id)

                        elif que.response_answer_ids and len(field.split('_')) == 2 and field.split('_')[1] == "selection":
                            value[field] = str(que.response_answer_ids[0].answer_id.id)

                        elif que.response_answer_ids and len(field.split('_')) == 3 and field.split('_')[2] != "multi" and field.split('_')[2] != "numeric":
                            for ans in que.response_answer_ids:
                                if str(field.split('_')[1]) == str( ans.answer_id.id) and str(field.split('_')[2]) == str(ans.column_id.id):
                                    if ans.value_choice:
                                        value[field] = ans.value_choice
                                    else:
                                        value[field] = True

                        else:
                            for ans in que.response_answer_ids:
                                if str(field.split('_')[1]) == str( ans.answer_id.id):
                                    value[field] = ans.answer

        else:
            if not context.has_key('sur_name_id'):
                return value
            if context.has_key('active') and context.get('active',False):
                return value
            
            sur_name_read = surv_name_wiz.read(cr, uid, context.get('sur_name_id',False))
            ans_list = []
            for key,val in sur_name_read['store_ans'].items():
                for field in fields_list:
                    if field in list(val):
                        value[field] = val[field]

        return value

    def create(self, cr, uid, vals, context=None):
        """
            Create the Answer of survey and store in survey.response object, and if set validation of question then check the value of question if value is wrong then raise the exception.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param vals: Values,
            @param context: A standard dictionary for contextual values
            @return : True.
        """
        if context.has_key('active') and context.get('active',False):
            return True

        for key,val in vals.items():
            if key.split('_')[0] == "progress":
                vals.pop(key)
            if not context.has_key('sur_name_id') and key.split('_')[0] == "wizardid":
                context.update({'sur_name_id': int(key.split('_')[1])})
                vals.pop(key)

        click_state = True
        click_update = []
        surv_name_wiz = self.pool.get('survey.name.wiz')
        surv_all_resp_obj = self.pool.get('survey.response')
        surv_tbl_column_obj = self.pool.get('survey.tbl.column.heading')
        survey_obj = self.pool.get('survey')
        resp_obj = self.pool.get('survey.response.line')
        res_ans_obj = self.pool.get('survey.response.answer')
        que_obj = self.pool.get('survey.question')
        sur_name_read = surv_name_wiz.read(cr, uid, context.get('sur_name_id',False), [])
        response_id =  0

        if not sur_name_read['response']:
            response_id = surv_all_resp_obj.create(cr, uid, {'response_type':'link', 'user_id':uid, 'date_create':datetime.datetime.now(), 'survey_id' : context['survey_id']})
            surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'response' : tools.ustr(response_id)})
        else:
            response_id = int(sur_name_read['response'])

        if response_id not in surv_all_resp_obj.search(cr, uid, []):
            response_id = surv_all_resp_obj.create(cr, uid, {'response_type':'link', 'user_id':uid, 'date_create':datetime.datetime.now(), 'survey_id' : context.get('survey_id',False)})
            surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'response' : tools.ustr(response_id)})

        #click first time on next button then increemnet on total start suvey
        if not sur_name_read['store_ans']:
            his_id = self.pool.get('survey.history').create(cr, uid, {'user_id': uid, \
                                              'date': strftime('%Y-%m-%d %H:%M:%S'), 'survey_id': sur_name_read['survey_id']})
            sur_rec = survey_obj.read(cr, uid, sur_name_read['survey_id'])
            survey_obj.write(cr, uid, sur_name_read['survey_id'],  {'tot_start_survey' : sur_rec['tot_start_survey'] + 1})
            if context.has_key('cur_id'):
                if context.has_key('request') and context.get('request',False):
                    self.pool.get(context.get('object',False)).write(cr, uid, [int(context.get('cur_id',False))], {'response' : response_id})
                    self.pool.get(context.get('object',False)).survey_req_done(cr, uid, [int(context.get('cur_id'))], context)
                else:
                    self.pool.get(context.get('object',False)).write(cr, uid, [int(context.get('cur_id',False))], {'response' : response_id})

        for key,val in sur_name_read['store_ans'].items():
            for field in vals:
                if field.split('_')[0] == val['question_id']:
                    click_state = False
                    click_update.append(key)
                    break

        if click_state:
            que_li = []
            resp_id_list = []
            for key, val in vals.items():
                que_id = key.split('_')[0]
                if que_id not in que_li:
                    que_li.append(que_id)
                    que_rec = que_obj.read(cr, uid, [int(que_id)], [])[0]
                    res_data =  {
                        'question_id':que_id, 
                        'date_create':datetime.datetime.now(),
                        'state':'done',
                        'response_id' : response_id
                    }
                    resp_id = resp_obj.create(cr, uid, res_data)
                    resp_id_list.append(resp_id)
                    sur_name_read['store_ans'].update({resp_id:{'question_id':que_id}})
                    surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'store_ans':sur_name_read['store_ans']})
                    select_count = 0
                    numeric_sum = 0
                    selected_value = []
                    matrix_list = []
                    comment_field = False
                    comment_value = False
                    response_list = []

                    for key1, val1 in vals.items():
                        if val1 and key1.split('_')[1] == "table" and key1.split('_')[0] == que_id:
                            surv_tbl_column_obj.create(cr, uid, {'response_table_id' : resp_id,'column_id':key1.split('_')[2], 'name':key1.split('_')[3], 'value' : val1})
                            sur_name_read['store_ans'][resp_id].update({key1:val1})
                            select_count += 1

                        elif val1 and key1.split('_')[1] == "otherfield" and key1.split('_')[0] == que_id:
                            comment_field = True
                            sur_name_read['store_ans'][resp_id].update({key1:val1})
                            select_count += 1
                            surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'store_ans':sur_name_read['store_ans']})
                            continue

                        elif val1 and key1.split('_')[1] == "selection" and key1.split('_')[0] == que_id:
                            if len(key1.split('_')) > 2:
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':resp_id, 'answer_id':key1.split('_')[-1], 'column_id' : val1})
                                selected_value.append(val1)
                                response_list.append(str(ans_create_id) + "_" + str(key1.split('_')[-1]))
                            else:
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':resp_id, 'answer_id':val1})
                            sur_name_read['store_ans'][resp_id].update({key1:val1})
                            select_count += 1

                        elif key1.split('_')[1] == "other" and key1.split('_')[0] == que_id:
                            if not val1:
                                comment_value = True
                            else:
                                error = False
                                if que_rec['is_comment_require'] and que_rec['comment_valid_type'] == 'must_be_specific_length':
                                    if (not val1 and  que_rec['comment_minimum_no']) or len(val1) <  que_rec['comment_minimum_no'] or len(val1) > que_rec['comment_maximum_no']:
                                        error = True
                                elif que_rec['is_comment_require'] and  que_rec['comment_valid_type'] in ['must_be_whole_number', 'must_be_decimal_number', 'must_be_date']:
                                    error = False
                                    try:
                                        if que_rec['comment_valid_type'] == 'must_be_whole_number':
                                            value = int(val1)
                                            if value <  que_rec['comment_minimum_no'] or value > que_rec['comment_maximum_no']:
                                                error = True
                                        elif que_rec['comment_valid_type'] == 'must_be_decimal_number':
                                            value = float(val1)
                                            if value <  que_rec['comment_minimum_float'] or value > que_rec['comment_maximum_float']:
                                                error = True
                                        elif que_rec['comment_valid_type'] == 'must_be_date':
                                            value = datetime.datetime.strptime(val1, "%Y-%m-%d")
                                            if value <  datetime.datetime.strptime(que_rec['comment_minimum_date'], "%Y-%m-%d") or value >  datetime.datetime.strptime(que_rec['comment_maximum_date'], "%Y-%m-%d"):
                                                error = True
                                    except:
                                        error = True
                                elif que_rec['is_comment_require'] and  que_rec['comment_valid_type'] == 'must_be_email_address':
                                    import re
                                    if re.match("^[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", val1) == None:
                                            error = True
                                if error:
                                    for res in resp_id_list:
                                        sur_name_read['store_ans'].pop(res)
                                    raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "'  \n" + tools.ustr(que_rec['comment_valid_err_msg'])))

                                resp_obj.write(cr, uid, resp_id, {'comment':val1})
                                sur_name_read['store_ans'][resp_id].update({key1:val1})

                        elif val1 and key1.split('_')[1] == "comment" and key1.split('_')[0] == que_id:
                            resp_obj.write(cr, uid, resp_id, {'comment':val1})
                            sur_name_read['store_ans'][resp_id].update({key1:val1})
                            select_count += 1

                        elif val1 and key1.split('_')[0] == que_id and (key1.split('_')[1] == "single"  or (len(key1.split('_')) > 2 and key1.split('_')[2] == 'multi')):
                            error = False
                            if que_rec['is_validation_require'] and que_rec['validation_type'] == 'must_be_specific_length':
                                if (not val1 and  que_rec['validation_minimum_no']) or len(val1) <  que_rec['validation_minimum_no'] or len(val1) > que_rec['validation_maximum_no']:
                                    error = True
                            elif que_rec['is_validation_require'] and que_rec['validation_type'] in ['must_be_whole_number', 'must_be_decimal_number', 'must_be_date']:
                                error = False
                                try:
                                    if que_rec['validation_type'] == 'must_be_whole_number':
                                        value = int(val1)
                                        if value <  que_rec['validation_minimum_no'] or value > que_rec['validation_maximum_no']:
                                            error = True
                                    elif que_rec['validation_type'] == 'must_be_decimal_number':
                                        value = float(val1)
                                        if value <  que_rec['validation_minimum_float'] or value > que_rec['validation_maximum_float']:
                                            error = True
                                    elif que_rec['validation_type'] == 'must_be_date':
                                        value = datetime.datetime.strptime(val1, "%Y-%m-%d")
                                        if value <  datetime.datetime.strptime(que_rec['validation_minimum_date'], "%Y-%m-%d") or value >  datetime.datetime.strptime(que_rec['validation_maximum_date'], "%Y-%m-%d"):
                                            error = True
                                except:
                                    error = True
                            elif que_rec['is_validation_require'] and que_rec['validation_type'] == 'must_be_email_address':
                                import re
                                if re.match("^[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", val1) == None:
                                        error = True
                            if error:
                                for res in resp_id_list:
                                    sur_name_read['store_ans'].pop(res)
                                raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "'  \n" + tools.ustr(que_rec['validation_valid_err_msg'])))

                            if key1.split('_')[1] == "single" :
                                resp_obj.write(cr, uid, resp_id, {'single_text':val1})
                            else:
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':resp_id, 'answer_id':key1.split('_')[1], 'answer' : val1})

                            sur_name_read['store_ans'][resp_id].update({key1:val1})
                            select_count += 1

                        elif val1 and que_id == key1.split('_')[0] and len(key1.split('_')) > 2 and key1.split('_')[2] == 'numeric':
                            if not val1=="0":
                                try:
                                    numeric_sum += int(val1)
                                    ans_create_id = res_ans_obj.create(cr, uid, {'response_id':resp_id, 'answer_id':key1.split('_')[1], 'answer' : val1})
                                    sur_name_read['store_ans'][resp_id].update({key1:val1})
                                    select_count += 1
                                except:
                                    for res in resp_id_list:
                                        sur_name_read['store_ans'].pop(res)
                                    raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "' \nPlease enter an integer value " ))

                        elif val1 and que_id == key1.split('_')[0] and len(key1.split('_')) == 3:
                            if type(val1) == type('') or type(val1) == type(u''):
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':resp_id, 'answer_id':key1.split('_')[1], 'column_id' : key1.split('_')[2], 'value_choice' : val1})
                                sur_name_read['store_ans'][resp_id].update({key1:val1})
                            else:
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':resp_id, 'answer_id':key1.split('_')[1], 'column_id' : key1.split('_')[2]})
                                sur_name_read['store_ans'][resp_id].update({key1:True})

                            matrix_list.append(key1.split('_')[0] + '_' + key1.split('_')[1])
                            select_count += 1

                        elif val1 and que_id == key1.split('_')[0] and len(key1.split('_')) == 2:
                            ans_create_id = res_ans_obj.create(cr, uid, {'response_id':resp_id, 'answer_id':key1.split('_')[-1], 'answer' : val1})
                            sur_name_read['store_ans'][resp_id].update({key1:val1})
                            select_count += 1
                        surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'store_ans':sur_name_read['store_ans']})

                    for key,val in vals.items():
                        if val and key.split('_')[1] == "commentcolumn" and key.split('_')[0] == que_id:
                            for res_id in response_list:
                                if key.split('_')[2] in res_id.split('_')[1]:
                                    a = res_ans_obj.write(cr, uid, [res_id.split('_')[0]], {'comment_field':val})
                                    sur_name_read['store_ans'][resp_id].update({key:val})

                    if comment_field and comment_value:
                        for res in resp_id_list:
                            sur_name_read['store_ans'].pop(res)
                        raise osv.except_osv(_('Error re !'), _("'" + que_rec['question']  + "' " + tools.ustr(que_rec['make_comment_field_err_msg'])))

                    if que_rec['type'] == "rating_scale" and que_rec['rating_allow_one_column_require'] and len(selected_value) > len(list(set(selected_value))):
                        for res in resp_id_list:
                            sur_name_read['store_ans'].pop(res)
                        raise osv.except_osv(_('Error re !'), _("'" + que_rec['question'] + "\n you cannot select same answer more than one times'"))

                    if not select_count:
                        resp_obj.write(cr, uid, resp_id, {'state':'skip'})

                    if que_rec[also'numeric_required_sum'] and numeric_sum > que_rec['numeric_required_sum']:
                        for res in resp_id_list:
                            sur_name_read['store_ans'].pop(res)
                        raise osv.except_osv(_('Error re !'), _("'" + que_rec['question'] + "' " + tools.ustr(que_rec['numeric_required_sum_err_msg'])))

                    if que_rec['type'] in ['multiple_textboxes_diff_type', 'multiple_choice_multiple_ans','matrix_of_choices_only_one_ans','matrix_of_choices_only_multi_ans','matrix_of_drop_down_menus','rating_scale','multiple_textboxes','numerical_textboxes','date','date_and_time'] and que_rec['is_require_answer']:
                        if matrix_list:
                            if (que_rec['required_type'] == 'all' and len(list(set(matrix_list))) < len(que_rec['answer_choice_ids'])) or \
                            (que_rec['required_type'] == 'at least' and len(list(set(matrix_list))) < que_rec['req_ans']) or \
                            (que_rec['required_type'] == 'at most' and len(list(set(matrix_list))) > que_rec['req_ans']) or \
                            (que_rec['required_type'] == 'exactly' and len(list(set(matrix_list))) != que_rec['req_ans']) or \
                            (que_rec['required_type'] == 'a range' and (len(list(set(matrix_list))) < que_rec['minimum_req_ans'] or len(list(set(matrix_list))) > que_rec['maximum_req_ans'])):
                                for res in resp_id_list:
                                    sur_name_read['store_ans'].pop(res)
                                raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "' " + tools.ustr(que_rec['req_error_msg'])))

                        elif (que_rec['required_type'] == 'all' and select_count < len(que_rec['answer_choice_ids'])) or \
                            (que_rec['required_type'] == 'at least' and select_count < que_rec['req_ans']) or \
                            (que_rec['required_type'] == 'at most' and select_count > que_rec['req_ans']) or \
                            (que_rec['required_type'] == 'exactly' and select_count != que_rec['req_ans']) or \
                            (que_rec['required_type'] == 'a range' and (select_count < que_rec['minimum_req_ans'] or select_count > que_rec['maximum_req_ans'])):
                            for res in resp_id_list:
                                sur_name_read['store_ans'].pop(res)
                            raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "' " + tools.ustr(que_rec['req_error_msg'])))

                    if que_rec['type'] in ['multiple_choice_only_one_ans','single_textbox','comment'] and  que_rec['is_require_answer'] and select_count <= 0:
                        for res in resp_id_list:
                            sur_name_read['store_ans'].pop(res)
                        raise osv.except_osv(_('Error re !'), _("'" + que_rec['question'] + "' " + tools.ustr(que_rec['req_error_msg'])))

        else:
            resp_id_list = []
            for update in click_update:
                que_rec = que_obj.read(cr, uid , [int(sur_name_read['store_ans'][update]['question_id'])], [])[0]
                res_ans_obj.unlink(cr, uid,res_ans_obj.search(cr, uid, [('response_id', '=', update)]))
                surv_tbl_column_obj.unlink(cr, uid,surv_tbl_column_obj.search(cr, uid, [('response_table_id', '=', update)]))
                resp_id_list.append(update)
                sur_name_read['store_ans'].update({update:{'question_id':sur_name_read['store_ans'][update]['question_id']}})
                surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'store_ans':sur_name_read['store_ans']})
                select_count = 0
                numeric_sum = 0
                selected_value = []
                matrix_list = []
                comment_field = False
                comment_value = False
                response_list = []

                for key, val in vals.items():
                    ans_id_len = key.split('_')
                    if ans_id_len[0] == sur_name_read['store_ans'][update]['question_id']:
                        if val and key.split('_')[1] == "table":
                            surv_tbl_column_obj.create(cr, uid, {'response_table_id' : update,'column_id':key.split('_')[2], 'name':key.split('_')[3], 'value' : val})
                            sur_name_read['store_ans'][update].update({key:val})
                            resp_obj.write(cr, uid, update, {'state': 'done'})

                        elif val and key.split('_')[1] == "otherfield" :
                            comment_field = True
                            sur_name_read['store_ans'][update].update({key:val})
                            select_count += 1
                            surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'store_ans':sur_name_read['store_ans']})
                            continue

                        elif val and key.split('_')[1] == "selection":
                            if len(key.split('_')) > 2:
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':update, 'answer_id':key.split('_')[-1], 'column_id' : val})
                                selected_value.append(val)
                                response_list.append(str(ans_create_id) + "_" + str(key.split('_')[-1]))
                            else:
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':update, 'answer_id': val})
                            resp_obj.write(cr, uid, update, {'state': 'done'})
                            sur_name_read['store_ans'][update].update({key:val})
                            select_count += 1

                        elif key.split('_')[1] == "other":
                            if not val:
                                comment_value = True
                            else:
                                error = False
                                if que_rec['is_comment_require'] and  que_rec['comment_valid_type'] == 'must_be_specific_length':
                                    if (not val and  que_rec['comment_minimum_no']) or len(val) <  que_rec['comment_minimum_no'] or len(val) > que_rec['comment_maximum_no']:
                                        error = True
                                elif que_rec['is_comment_require'] and  que_rec['comment_valid_type'] in ['must_be_whole_number', 'must_be_decimal_number', 'must_be_date']:
                                    try:
                                        if que_rec['comment_valid_type'] == 'must_be_whole_number':
                                            value = int(val)
                                            if value <  que_rec['comment_minimum_no'] or value > que_rec['comment_maximum_no']:
                                                error = True
                                        elif que_rec['comment_valid_type'] == 'must_be_decimal_number':
                                            value = float(val)
                                            if value <  que_rec['comment_minimum_float'] or value > que_rec['comment_maximum_float']:
                                                error = True
                                        elif que_rec['comment_valid_type'] == 'must_be_date':
                                            value = datetime.datetime.strptime(val, "%Y-%m-%d")
                                            if value <  datetime.datetime.strptime(que_rec['comment_minimum_date'], "%Y-%m-%d") or value >  datetime.datetime.strptime(que_rec['comment_maximum_date'], "%Y-%m-%d"):
                                                error = True
                                    except:
                                        error = True
                                elif que_rec['is_comment_require'] and  que_rec['comment_valid_type'] == 'must_be_email_address':
                                    import re
                                    if re.match("^[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", val) == None:
                                            error = True
                                if error:
                                    raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "'  \n" + tools.ustr(que_rec['comment_valid_err_msg'])))
                                resp_obj.write(cr, uid, update, {'comment':val,'state': 'done'})
                                sur_name_read['store_ans'][update].update({key:val})

                        elif val and key.split('_')[1] == "comment":
                            resp_obj.write(cr, uid, update, {'comment':val,'state': 'done'})
                            sur_name_read['store_ans'][update].update({key:val})
                            select_count += 1

                        elif val and (key.split('_')[1] == "single"  or (len(key.split('_')) > 2 and key.split('_')[2] == 'multi')):
                            error = False
                            if que_rec['is_validation_require'] and que_rec['validation_type'] == 'must_be_specific_length':
                                if (not val and  que_rec['validation_minimum_no']) or len(val) <  que_rec['validation_minimum_no'] or len(val) > que_rec['validation_maximum_no']:
                                    error = True
                            elif que_rec['is_validation_require'] and que_rec['validation_type'] in ['must_be_whole_number', 'must_be_decimal_number', 'must_be_date']:
                                error = False
                                try:
                                    if que_rec['validation_type'] == 'must_be_whole_number':
                                        value = int(val)
                                        if value <  que_rec['validation_minimum_no'] or value > que_rec['validation_maximum_no']:
                                            error = True
                                    elif que_rec['validation_type'] == 'must_be_decimal_number':
                                        value = float(val)
                                        if value <  que_rec['validation_minimum_float'] or value > que_rec['validation_maximum_float']:
                                            error = True
                                    elif que_rec['validation_type'] == 'must_be_date':
                                        value = datetime.datetime.strptime(val, "%Y-%m-%d")
                                        if value <  datetime.datetime.strptime(que_rec['validation_minimum_date'], "%Y-%m-%d") or value >  datetime.datetime.strptime(que_rec['validation_maximum_date'], "%Y-%m-%d"):
                                            error = True
                                except Exception ,e:
                                    error = True
                            elif que_rec['is_validation_require'] and  que_rec['validation_type'] == 'must_be_email_address':
                                import re
                                if re.match("^[a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", val) == None:
                                        error = True
                            if error:
                                raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "'  \n" + tools.ustr(que_rec['validation_valid_err_msg'])))
                            if key.split('_')[1] == "single" :
                                resp_obj.write(cr, uid, update, {'single_text':val,'state': 'done'})
                            else:
                                resp_obj.write(cr, uid, update, {'state': 'done'})
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':update, 'answer_id':ans_id_len[1], 'answer' : val})
                            sur_name_read['store_ans'][update].update({key:val})
                            select_count += 1

                        elif val and len(key.split('_')) > 2 and key.split('_')[2] == 'numeric':
                            if not val=="0":
                                try:
                                    numeric_sum += int(val)
                                    resp_obj.write(cr, uid, update, {'state': 'done'})
                                    ans_create_id = res_ans_obj.create(cr, uid, {'response_id':update, 'answer_id':ans_id_len[1], 'answer' : val})
                                    sur_name_read['store_ans'][update].update({key:val})
                                    select_count += 1
                                except:
                                    raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "' \n Please enter an integer value " ))

                        elif val and len(key.split('_')) == 3:
                            resp_obj.write(cr, uid, update, {'state': 'done'})
                            if type(val) == type('') or type(val) == type(u''):
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':update, 'answer_id':ans_id_len[1], 'column_id' : ans_id_len[2], 'value_choice' : val})
                                sur_name_read['store_ans'][update].update({key:val})
                            else:
                                ans_create_id = res_ans_obj.create(cr, uid, {'response_id':update, 'answer_id':ans_id_len[1], 'column_id' : ans_id_len[2]})
                                sur_name_read['store_ans'][update].update({key:True})
                            matrix_list.append(key.split('_')[0] + '_' + key.split('_')[1])
                            select_count += 1

                        elif val and len(key.split('_')) == 2:
                            resp_obj.write(cr, uid, update, {'state': 'done'})
                            ans_create_id = res_ans_obj.create(cr, uid, {'response_id':update, 'answer_id':ans_id_len[-1], 'answer' : val})
                            sur_name_read['store_ans'][update].update({key:val})
                            select_count += 1
                        surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'store_ans':sur_name_read['store_ans']})

                for key,val in vals.items():
                    if val and key.split('_')[1] == "commentcolumn" and key.split('_')[0] == sur_name_read['store_ans'][update]['question_id']:
                        for res_id in response_list:
                            if key.split('_')[2] in res_id.split('_')[1]:
                                a = res_ans_obj.write(cr, uid, [res_id.split('_')[0]], {'comment_field':val})
                                sur_name_read['store_ans'][update].update({key:val})

                if comment_field and comment_value:
                    raise osv.except_osv(_('Error re !'), _("'" + que_rec['question']  + "' " + tools.ustr(que_rec['make_comment_field_err_msg'])))

                if que_rec['type'] == "rating_scale" and que_rec['rating_allow_one_column_require'] and len(selected_value) > len(list(set(selected_value))):
                    raise osv.except_osv(_('Error re !'), _("'" + que_rec['question'] + "\n you cannot select same answer more than one times'"))

                if que_rec['numeric_required_sum'] and numeric_sum > que_rec['numeric_required_sum']:
                    raise osv.except_osv(_('Error re !'), _("'" + que_rec['question'] + "' " + tools.ustr(que_rec['numeric_required_sum_err_msg'])))

                if not select_count:
                    resp_obj.write(cr, uid, update, {'state': 'skip'})

                if que_rec['type'] in ['multiple_textboxes_diff_type','multiple_choice_multiple_ans','matrix_of_choices_only_one_ans','matrix_of_choices_only_multi_ans','matrix_of_drop_down_menus','rating_scale','multiple_textboxes','numerical_textboxes','date','date_and_time'] and que_rec['is_require_answer']:
                    if matrix_list:
                        if (que_rec['required_type'] == 'all' and len(list(set(matrix_list))) < len(que_rec['answer_choice_ids'])) or \
                        (que_rec['required_type'] == 'at least' and len(list(set(matrix_list))) < que_rec['req_ans']) or \
                        (que_rec['required_type'] == 'at most' and len(list(set(matrix_list))) > que_rec['req_ans']) or \
                        (que_rec['required_type'] == 'exactly' and len(list(set(matrix_list))) != que_rec['req_ans']) or \
                        (que_rec['required_type'] == 'a range' and (len(list(set(matrix_list))) < que_rec['minimum_req_ans'] or len(list(set(matrix_list))) > que_rec['maximum_req_ans'])):
                            raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "' " + tools.ustr(que_rec['req_error_msg'])))

                    elif (que_rec['required_type'] == 'all' and select_count < len(que_rec['answer_choice_ids'])) or \
                        (que_rec['required_type'] == 'at least' and select_count < que_rec['req_ans']) or \
                        (que_rec['required_type'] == 'at most' and select_count > que_rec['req_ans']) or \
                        (que_rec['required_type'] == 'exactly' and select_count != que_rec['req_ans']) or \
                        (que_rec['required_type'] == 'a range' and (select_count < que_rec['minimum_req_ans'] or select_count > que_rec['maximum_req_ans'])):
                            raise osv.except_osv(_('Error !'), _("'" + que_rec['question'] + "' " + tools.ustr(que_rec['req_error_msg'])))

                if que_rec['type'] in ['multiple_choice_only_one_ans','single_textbox','comment'] and  que_rec['is_require_answer'] and select_count <= 0:
                    raise osv.except_osv(_('Error re !'), _("'" + que_rec['question'] + "' " + tools.ustr(que_rec['req_error_msg'])))

        return True

    def action_new_question(self,cr, uid, ids, context):
        """
            New survey.Question form.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open new survey.Qestion form.
        """
        for key,val in context.items():
            if type(key) == type(True):
                context.pop(key)
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[('model','=','survey.question'),('name','=','survey_question_wizard_test')])
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'view_id': view_id,
                'context': context
                }

    def action_new_page(self, cr, uid, ids, context):
        """
            New survey.Page form.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open new survey.page form.
        """
        for key,val in context.items():
            if type(key) == type(True):
                context.pop(key)
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[('model','=','survey.page'),('name','=','survey_page_wizard_test')])
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.page',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'view_id': view_id,
                'context': context
                }

    def action_edit_page(self,cr, uid, ids, context):
        """
            Edit survey.page.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open Edit survey.page form.
        """
        for key,val in context.items():
            if type(key) == type(True):
                context.pop(key)
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[('model','=','survey.page'),('name','=','survey_page_wizard_test')])
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.page',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id' : int(context.get('page_id',0)),
                'view_id': view_id,
                'context': context
                }

    def action_delete_page(self,cr, uid, ids, context):
        """
            Delete survey.page.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open next survey.page form, but delete the selected page.
        """
        for key,val in context.items():
            if type(key) == type(True):
                context.pop(key)

        self.pool.get('survey.page').unlink(cr, uid, [context.get('page_id',False)])
        search_id = self.pool.get('ir.ui.view').search(cr,uid,[('model','=','survey.question.wiz'),('name','=','Survey Search')])
        surv_name_wiz = self.pool.get('survey.name.wiz')
        surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'transfer':True, 'page_no' : context.get('page_number',False) })
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'search_view_id':search_id[0],
                'context': context
                }

    def action_edit_question(self,cr, uid, ids, context):
        """
            Edit survey.question.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open Edit survey.question form.
        """
        for key,val in context.items():
            if type(key) == type(True):
                context.pop(key)
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[('model','=','survey.question'),('name','=','survey_question_wizard_test')])
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id' : int(context.get('question_id',0)),
                'view_id': view_id,
                'context': context
                }

    def action_delete_question(self,cr, uid, ids, context):
        """
            Edit survey.question.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open same survey.page form, but delete the selected survey.question in current survey.page.
        """
        for key,val in context.items():
            if type(key) == type(True):
                context.pop(key)

        que_obj = self.pool.get('survey.question')
        que_obj.unlink(cr, uid, [context.get('question_id',False)])
        search_id = self.pool.get('ir.ui.view').search(cr,uid,[('model','=','survey.question.wiz'),('name','=','Survey Search')])
        surv_name_wiz = self.pool.get('survey.name.wiz')
        surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'transfer':True, 'page_no' : context.get('page_number',0) })
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'search_view_id':search_id[0],
                'context': context
                }

    def action_forward_previous(self, cr, uid, ids, context=None):
        """
            Goes to previous Survey Answer.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open Previous Answer form.
        """
        search_obj = self.pool.get('ir.ui.view')
        surv_name_wiz = self.pool.get('survey.name.wiz')
        search_id = search_obj.search(cr,uid,[('model','=','survey.question.wiz'),('name','=','Survey Search')])
        wiz_id = surv_name_wiz.create(cr,uid, {'survey_id' : context.get('survey_id',False),'page_no' :-1,'page':'next','transfer' :1,'response':0})
        context.update({'sur_name_id' :wiz_id, 'response_no' : context.get('response_no',0) - 1})

        if context.get('response_no',0) + 1 > len(context.get('response_id',0)):
            return {}
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'search_view_id':search_id[0],
                'context': context
                }

    def action_forward_next(self, cr, uid, ids, context=None):
        """
            Goes to Next Survey Answer.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open Next Answer form.
        """
        search_obj = self.pool.get('ir.ui.view')
        surv_name_wiz = self.pool.get('survey.name.wiz')
        search_id = search_obj.search(cr,uid,[('model','=','survey.question.wiz'),('name','=','Survey Search')])
        wiz_id = surv_name_wiz.create(cr,uid, {'survey_id' : context.get('survey_id',False),'page_no' :-1,'page':'next','transfer' :1,'response':0})
        context.update({'sur_name_id' :wiz_id, 'response_no' : context.get('response_no',0) + 1})

        if context.get('response_no',0) + 1 > len(context.get('response_id',0)):
            return {}
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'search_view_id':search_id[0],
                'context': context
                }

    def action_next(self, cr, uid, ids, context=None):
        """
            Goes to Next page.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open Next survey.page form.
        """
        surv_name_wiz = self.pool.get('survey.name.wiz')
        search_obj = self.pool.get('ir.ui.view')
        search_id = search_obj.search(cr,uid,[('model','=','survey.question.wiz'),('name','=','Survey Search')])
        surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'transfer':True, 'page':'next'})
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'search_view_id':search_id[0],
                'context': context
                }

    def action_previous(self, cr, uid, ids, context=None):
        """
            Goes to previous page.
           
            @param self: The object pointer
            @param cr: the current row, from the database cursor,
            @param uid: the current user’s ID for security checks,
            @param ids: List of survey.question.wiz IDs
            @param context: A standard dictionary for contextual values
            @return : Dictionary value for Open Previous survey.page form.
        """
        surv_name_wiz = self.pool.get('survey.name.wiz')
        search_obj = self.pool.get('ir.ui.view')
        search_id = search_obj.search(cr,uid,[('model','=','survey.question.wiz'),('name','=','Survey Search')])
        surv_name_wiz.write(cr, uid, [context.get('sur_name_id',False)], {'transfer':True, 'page':'previous'})
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'search_view_id':search_id[0],
                'context': context
                }

survey_question_wiz()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
