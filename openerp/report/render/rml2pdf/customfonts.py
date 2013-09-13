# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 P. Christeas, Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2013 OpenERP SA. (http://www.openerp.com)
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

import logging
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase import ttfonts
import platform
from reportlab import rl_config

#.apidoc title: TTF Font Table

"""This module allows the mapping of some system-available TTF fonts to
the reportlab engine.

This file could be customized per distro (although most Linux/Unix ones)
should have the same filenames, only need the code below).

Due to an awful configuration that ships with reportlab at many Linux
and Ubuntu distros, we have to override the search path, too.
"""
supported_fonts = []
_logger = logging.getLogger(__name__)

CustomTTFonts = [ ('Helvetica',"DejaVu Sans", "DejaVuSans.ttf", 'normal'),
        ('Helvetica',"DejaVu Sans Bold", "DejaVuSans-Bold.ttf", 'bold'),
        ('Helvetica',"DejaVu Sans Oblique", "DejaVuSans-Oblique.ttf", 'italic'),
        ('Helvetica',"DejaVu Sans BoldOblique", "DejaVuSans-BoldOblique.ttf", 'bolditalic'),
        ('Times',"Liberation Serif", "LiberationSerif-Regular.ttf", 'normal'),
        ('Times',"Liberation Serif Bold", "LiberationSerif-Bold.ttf", 'bold'),
        ('Times',"Liberation Serif Italic", "LiberationSerif-Italic.ttf", 'italic'),
        ('Times',"Liberation Serif BoldItalic", "LiberationSerif-BoldItalic.ttf", 'bolditalic'),
        ('Times-Roman',"Liberation Serif", "LiberationSerif-Regular.ttf", 'normal'),
        ('Times-Roman',"Liberation Serif Bold", "LiberationSerif-Bold.ttf", 'bold'),
        ('Times-Roman',"Liberation Serif Italic", "LiberationSerif-Italic.ttf", 'italic'),
        ('Times-Roman',"Liberation Serif BoldItalic", "LiberationSerif-BoldItalic.ttf", 'bolditalic'),
        ('Courier',"FreeMono", "FreeMono.ttf", 'normal'),
        ('Courier',"FreeMono Bold", "FreeMonoBold.ttf", 'bold'),
        ('Courier',"FreeMono Oblique", "FreeMonoOblique.ttf", 'italic'),
        ('Courier',"FreeMono BoldOblique", "FreeMonoBoldOblique.ttf", 'bolditalic'),

        # Sun-ExtA can be downloaded from http://okuc.net/SunWb/
        ('Sun-ExtA',"Sun-ExtA", "Sun-ExtA.ttf", 'normal'),
]

TTFSearchPath_Linux = [
            '/usr/share/fonts/truetype', # SuSE
            '/usr/share/fonts/dejavu', '/usr/share/fonts/liberation', # Fedora, RHEL
            '/usr/share/fonts/truetype/*', # Ubuntu,
            '/usr/share/fonts/TTF/*', # at Mandriva/Mageia
            '/usr/share/fonts/TTF', # Arch Linux
            ]

TTFSearchPath_Windows = [
            'c:/winnt/fonts',
            'c:/windows/fonts'
            ]

TTFSearchPath_Darwin = [
            #mac os X - from
            #http://developer.apple.com/technotes/tn/tn2024.html
            '~/Library/Fonts',
            '/Library/Fonts',
            '/Network/Library/Fonts',
            '/System/Library/Fonts',
            ]

TTFSearchPathMap = {
    'Darwin': TTFSearchPath_Darwin,
    'Windows': TTFSearchPath_Windows,
    'Linux': TTFSearchPath_Linux,
}

def RegisterCustomFonts():
    searchpath = []
    local_platform = platform.system()
    if local_platform in TTFSearchPathMap:
        searchpath += TTFSearchPathMap[local_platform]
    # Append the original search path of reportlab (at the end)
    searchpath += rl_config.TTFSearchPath 
    addToPdfmetrics(searchpath)
    return True

def addToPdfmetrics(path):
    global supported_fonts
    for dirname in path:
        if os.path.exists(dirname):
            for filename in [x for x in os.listdir(dirname) if x.lower().endswith('.ttf')]:
                filepath = os.path.join(dirname, filename)
                try:
                    face = ttfonts.TTFontFace(filepath)
                    font_info = ttfonts.TTFontFile(filepath)
                    if (face.name,face.name) not in supported_fonts:
                        pdfmetrics.registerFont(ttfonts.TTFont(face.name, filepath, asciiReadable=0))
                        supported_fonts.append((face.name,face.name))
                        CustomTTFonts.append((font_info.familyName,font_info.name,filename,font_info.styleName.lower().replace(" ","")))
                    _logger.debug("Found font %s at %s", face.name, filename)
                except:
                    _logger.warning("Could not register Font %s",filename)
    return True
    
def SetCustomFonts(rmldoc):
    """ Map some font names to the corresponding TTF fonts

        The ttf font may not even have the same name, as in
        Times -> Liberation Serif.
        This function is called once per report, so it should
        avoid system-wide processing (cache it, instead).
    """
    global supported_fonts
    if not supported_fonts:
        RegisterCustomFonts()
    for name, font, filename, mode in CustomTTFonts:
        if os.path.isabs(filename) and os.path.exists(filename):
            rmldoc.setTTFontMapping(name, font, filename, mode)
    return True
#eof

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
