
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

import pooler
import time
from report import report_sxw

#from report.interface import report_int
#from reportlab.graphics.shapes import Drawing
#from reportlab.graphics.charts.barcharts import VerticalBarChart
#import reportlab.lib.colors as colors
#from reportlab.graphics.widgetbase import Widget, TypedPropertyCollection
#from reportlab.graphics.charts.textlabels import BarChartLabel
#from reportlab.graphics import renderPM
#from report.render import render
#from report.interface import report_int
from pychart import *
import StringIO
theme.use_color = 1
theme.default_font_family = "Helvetica-Bold"
theme.default_font_size = 18
theme.default_line_width = 1.0
import tools


parents = {
    'tr':1,
    'li':1,
    'story': 0,
    'section': 0
}

class accounting_report_indicator(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(accounting_report_indicator, self).__init__(cr, uid, name, context)
        self.ret_list = []
        self.localcontext.update({
            'time': time,
            'test': self.test1,
            'lines':self.lines,
            'getarray':self.getarray,
        })
        self.count=0
        self.list=[]
        self.header_name=self.header_val=[]

    def repeatIn(self, lst, name, nodes_parent=False,td=False,width=[],value=[],type=[]):
        self._node.data = ''
        node = self._find_parent(self._node, nodes_parent or parents)
        ns = node.nextSibling
#start
        if not name=='array':
            return super(accounting_report_indicator,self).repeatIn(lst, name, nodes_parent=False)

        value=['Data']
        value.extend(self.header_name)
        type=['string'].extend(['float']*len(self.header_name))
        width=[40]*(len(self.header_name)+1)

        if not lst:
            lst.append(1)
        for ns in node.childNodes :
            if ns and ns.nodeName!='#text' and ns.tagName=='blockTable' and td :
                width_str = ns._attrs['colWidths'].nodeValue
                ns.removeAttribute('colWidths')
                total_td = td * len(value)

                if not width:
                    for v in value:
                        width.append(30)
                for v in range(len(value)):
                    width_str +=',%d'%width[v]

                ns.setAttribute('colWidths',width_str)

                child_list =  ns.childNodes
                check=0
                for child in child_list:
                    if child.nodeName=='tr':
                        lc = child.childNodes[1]
#                        for t in range(td):
                        i=0
                        for v in value:
                            newnode = lc.cloneNode(1)
                            if check==1:
                                t1="[[ %s['%s'] ]]"%(name,v)
                            else:
                                t1="%s"%(v)
                            newnode.childNodes[1].lastChild.data = t1
                            child.appendChild(newnode)
                            newnode=False
                            i+=1
                        check=1

        return super(accounting_report_indicator,self).repeatIn(lst, name, nodes_parent=False)

    def lines(self,data):
        res={}
        result=[]
        ind_ids=self.pool.get('account.report.report').search(self.cr,self.uid,[])
        obj_inds=self.pool.get('account.report.report').browse(self.cr,self.uid,ind_ids)

#        def find_child(obj):
#            self.list.append(obj)
#            if obj.child_ids:
#                for child in obj.child_ids:
#                    find_child(child)
#            return True
#
#        find_child(obj_inds)

        for obj_ind in obj_inds:
            res = {
                'id':obj_ind.id,
                'name':obj_ind.name,
                'code':obj_ind.code,
                'expression':obj_ind.expression,
                'disp_graph':obj_ind.disp_graph,
                'note':obj_ind.note,
                'type':obj_ind.type,
                }
            result.append(res)
        return result

    def getarray(self,data,object):
        res={}
        result=[]
        self.test1(data,object,intercall=True)
        self.header_val=[str(x) for x in self.header_val]
        temp_dict=zip(self.header_name,self.header_val)
        res=dict(temp_dict)
        res['Data']='Value'
        result.append(res)
        return result


    def test1(self,data,object,intercall=False):

        obj_history=self.pool.get('account.report.history')

        if data['select_base']=='year':
            tuple_search=('fiscalyear_id','in',data['base_selection'][0][2])
            base='year'
        else:
            tuple_search=('period_id','in',data['base_selection'][0][2])
            base='period'

        history_ids=obj_history.search(self.cr,self.uid,[('name','=',object['id']),tuple_search])
        history_ids.sort()
        obj_his=obj_history.browse(self.cr,self.uid,history_ids)

        data_val=[]
        data_period=[]
        if base=='period':
            for item in obj_his:
                data_val.append(item.val)
                data_period.append(item.period_id.name)
        else:
            for i in data['base_selection'][0][2]:
                val_temp=[]
                data_period.append(self.pool.get('account.fiscalyear').browse(self.cr,self.uid,i).name)
                for item in obj_his:
                    if item.fiscalyear_id.id==i:
                        val_temp.append(item.val)
                data_val.append(sum(val_temp))

        self.header_name=data_period
        self.header_val=data_val

        if intercall:
            return True
        self.count +=1
#        drawing = Drawing(400, 300)
#        data = [
#                 tuple(data_val),
#                 ]
#        value_min=0.0
#        vmin=min(data_val)
#        vmax=max(data_val)
#
#        val_min=((vmin < 0.00 and vmin-2.00)  or 0.00)
#        # calculating maximum
#        val_max=(vmax/(pow(10,len(str(int(vmax)))-2))+1)*pow(10,len(str(int(vmax)))-2)
#        bc = VerticalBarChart()
#        bc.x = 50
#        bc.y = 50
#        bc.height = 245
#        bc.width = 300
#        bc.data = data
#        value_step=(abs(val_max)-abs(val_min))/5
#
#        bc.strokeColor = colors.black
#        bc.valueAxis.valueMin = val_min
#        bc.valueAxis.valueMax = val_max
#        bc.valueAxis.valueStep = value_step
#
#        bc.categoryAxis.labels.boxAnchor = 'ne'
#        bc.categoryAxis.labels.dx = 8
#
#        bc.categoryAxis.labels.dy = -2
#        bc.categoryAxis.labels.angle = 30
#        bc.categoryAxis.categoryNames = data_period
#        drawing.add(bc)
#        drawing.save(formats=['png'],fnRoot=path+str(self.count),title="helo")
#        renderPM.drawToFile(drawing1, 'example1.jpg','jpg')
        import os
        dirname ='Temp_images'
        path=os.path.join(tools.config['root_path'],dirname,"Image")

        if not os.path.isdir(tools.config['root_path']+ "/"+dirname + '/'):
            os.mkdir(tools.config['root_path'] +"/"+ dirname + '/')
            os.path.join(tools.config['root_path'],dirname,"/")
        can = canvas.init('Image'+str(self.count)+".png")
#        can.clip(0,0,600,400)

        data=zip(self.header_name,self.header_val)

        ar = area.T(size = (650,450),x_coord = category_coord.T(data, 0), y_range = (None, None),
            x_axis = axis.X(label="Period // Year",format="/a-30{}%s"),
            y_axis = axis.Y(label="Value"))

        ar.add_plot(bar_plot.T(data = data,width=15, data_label_format="/o/15{}%s",label = "Value",fill_style=fill_style.red))
        ar.draw()

        can.close()
        os.system('cp '+'Image'+str(self.count)+'.png ' +path+str(self.count)+'.png')
        os.system('rm '+'Image'+str(self.count)+'.png')
#        can.endclip()
        return path+str(self.count)+'.png'

report_sxw.report_sxw('report.print.indicators', 'account.report.history',
        'addons/account_report/report/print_indicator.rml',
        parser=accounting_report_indicator, header=False)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

