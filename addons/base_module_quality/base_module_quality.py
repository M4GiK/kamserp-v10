# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

import netsvc
from osv import fields, osv

class quality_check(object):
    '''
        This Class provide...
    '''

    _score = 0.0
    _result = ""
    _result_details = ""

    def __init__(self, module_path=""):
        '''
        this method should do the test and fill the _score, _result and _result_details var
        '''
        raise 'Not Implemented'

    #~ def __get_result__(self, cr, uid, module_ids):
        #~ '''
        #~ '''
        #~ return _result

    #~ def __get_detailed_result__(self, cr, uid, module_ids):
        #~ '''
        #~ '''
        #~ return _result_details


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

