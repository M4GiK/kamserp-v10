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

from report.render.rml2pdf import utils
from lxml import etree
import copy


class odt2odt(object):
    def __init__(self, odt, localcontext):
        self.localcontext = localcontext
        self.etree = odt
        self._node = None


    def render(self):
        def process_text(node,new_node):
            if new_node.tag in ['story','tr','section']:
                new_node.attrib.clear()
            for child in utils._child_get(node, self):
                new_child = copy.deepcopy(child)
                new_child.text  = utils._process_text(self, child.text)
                new_node.append(new_child)
                if len(child):
                    for n in new_child:
                        new_child.remove(n)
                    process_text(child, new_child)
                else:
                    new_child.text  = utils._process_text(self, child.text)
        self._node = copy.deepcopy(self.etree)
        for n in self._node:
            self._node.remove(n)
        process_text(self.etree, self._node)
        return self._node

def parseNode(node, localcontext = {}):
    body = node.getchildren()[-1]
    elements = body.findall(localcontext['name_space']["text"]+"p")
    for pe in elements:
        e = pe.findall(localcontext['name_space']["text"]+"drop-down")
        for de in e:
            pp=de.getparent()
            for cnd in de.getchildren():
                if cnd.text:
                    pe.append(cnd)
                    pp.remove(de)
    r = odt2odt(node, localcontext)
    return r.render()

