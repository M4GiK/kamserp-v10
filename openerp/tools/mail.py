# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2012 OpenERP S.A. (<http://openerp.com>).
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

from lxml import etree
# try:
#     from lxml.html.soupparser import fromstring as parser_fromstring
# except ImportError:
#     from lxml.html import fromstring as parser_fromstring
import logging
import lxml.html
import openerp.pooler as pooler
import operator
import random
import re
import socket
import threading
import time

from openerp.loglevels import ustr

_logger = logging.getLogger(__name__)


def html_sanitize(src):
    if not src:
        return src
    src = ustr(src, errors='replace')
    root = lxml.html.fromstring(u"<div>%s</div>" % src)
    result = handle_element(root)
    res = []
    for element in children(result[0]):
        if isinstance(element, basestring):
            res.append(element)
        else:
            element.tail = ""
            res.append(lxml.html.tostring(element))
    return ''.join(res)

# FIXME: shouldn't this be a whitelist rather than a blacklist?!
to_remove = set(["script", "head", "meta", "title", "link", "img"])
to_unwrap = set(["html", "body"])

javascript_regex = re.compile(r"^\s*javascript\s*:.*$", re.IGNORECASE)

def handle_a(el, new):
    href = el.get("href", "#")
    if javascript_regex.search(href):
        href = "#"
    new.set("href", href)

special = {
    "a": handle_a,
}

def handle_element(element):
    if isinstance(element, basestring):
        return [element]
    if element.tag in to_remove:
        return []
    if element.tag in to_unwrap:
        return reduce(operator.add, [handle_element(x) for x in children(element)])
    result = lxml.html.fromstring("<%s />" % element.tag)
    for c in children(element):
        append_to(handle_element(c), result)
    if element.tag in special:
        special[element.tag](element, result)
    return [result]

def children(node):
    res = []
    if node.text is not None:
        res.append(node.text)
    for child_node in node.getchildren():
        res.append(child_node)
        if child_node.tail is not None:
            res.append(child_node.tail)
    return res

def append_to(elements, dest_node):
    for element in elements:
        if isinstance(element, basestring):
            children = dest_node.getchildren()
            if len(children) == 0:
                dest_node.text = element
            else:
                children[-1].tail = element
        else:
            dest_node.append(element)


#----------------------------------------------------------
# HTML Cleaner
#----------------------------------------------------------

def html_email_clean(html):
    """ html_email_clean: clean the html to display in the web client.
        - strip email quotes (remove blockquote nodes)
        - strip signatures (remove --\n{\n)Blahblah), by replacing <br> by
            \n to avoid ignoring signatures converted into html
    """
    modified_html = ''

    # 1. <br[ /]> -> \n, because otherwise the tree is obfuscated
    br_tags = re.compile(r'([<]\s*br\s*\/?[>])')
    idx = 0
    for item in re.finditer(br_tags, html):
        modified_html += html[idx:item.start()] + '__BR_TAG__'
        idx = item.end()
    modified_html += html[idx:]
    html = modified_html

    # 2. form a tree, handle (currently ?) pure-text by enclosing them in a pre
    root = lxml.html.fromstring(html)
    if not len(root) and root.text is None and root.tail is None:
        html = '<div>%s</div>' % html
        root = lxml.html.fromstring(html)

    # 3. remove blockquotes
    quotes = [el for el in root.iterchildren(tag='blockquote')]
    for node in quotes:
        node.getparent().remove(node)

    # 4. strip signatures
    signature = re.compile(r'([-]{2}[\s]?[\r\n]{1,2}[^\z]+)')
    for elem in root.getiterator():
        if elem.text:
            match = re.search(signature, elem.text)
            if match:
                elem.text = elem.text[:match.start()] + elem.text[match.end():]
        if elem.tail:
            match = re.search(signature, elem.tail)
            if match:
                elem.tail = elem.tail[:match.start()] + elem.tail[match.end():]

    # 5. \n back to <br/>
    html = etree.tostring(root, pretty_print=True)
    html = html.replace('__BR_TAG__', '<br />')

    # 6. Misc cleaning :
    # - ClEditor seems to love using <div><br /><div> -> replace with <br />
    modified_html = ''
    br_div_tags = re.compile(r'(<div>\s*<br\s*\/>\s*<\/div>)')
    idx = 0
    for item in re.finditer(br_div_tags, html):
        modified_html += html[idx:item.start()] + '<br />'
        idx = item.end()
    modified_html += html[idx:]
    html = modified_html

    return html


#----------------------------------------------------------
# Emails
#----------------------------------------------------------

email_re = re.compile(r"""
    ([a-zA-Z][\w\.-]*[a-zA-Z0-9]     # username part
    @                                # mandatory @ sign
    [a-zA-Z0-9][\w\.-]*              # domain must start with a letter ... Ged> why do we include a 0-9 then?
     \.
     [a-z]{2,3}                      # TLD
    )
    """, re.VERBOSE)
res_re = re.compile(r"\[([0-9]+)\]", re.UNICODE)
command_re = re.compile("^Set-([a-z]+) *: *(.+)$", re.I + re.UNICODE)

# Updated in 7.0 to match the model name as well
# Typical form of references is <timestamp-openerp-record_id-model_name@domain>
# group(1) = the record ID ; group(2) = the model (if any) ; group(3) = the domain
reference_re = re.compile("<.*-open(?:object|erp)-(\\d+)(?:-([\w.]+))?.*@(.*)>", re.UNICODE)

def html2plaintext(html, body_id=None, encoding='utf-8'):
    """ From an HTML text, convert the HTML to plain text.
    If @param body_id is provided then this is the tag where the
    body (not necessarily <body>) starts.
    """
    ## (c) Fry-IT, www.fry-it.com, 2007
    ## <peter@fry-it.com>
    ## download here: http://www.peterbe.com/plog/html2plaintext

    html = ustr(html)

    from lxml.etree import tostring, fromstring, HTMLParser
    tree = fromstring(html, parser=HTMLParser())

    if body_id is not None:
        source = tree.xpath('//*[@id=%s]'%(body_id,))
    else:
        source = tree.xpath('//body')
    if len(source):
        tree = source[0]

    url_index = []
    i = 0
    for link in tree.findall('.//a'):
        url = link.get('href')
        if url:
            i += 1
            link.tag = 'span'
            link.text = '%s [%s]' % (link.text, i)
            url_index.append(url)

    html = ustr(tostring(tree, encoding=encoding))

    html = html.replace('<strong>','*').replace('</strong>','*')
    html = html.replace('<b>','*').replace('</b>','*')
    html = html.replace('<h3>','*').replace('</h3>','*')
    html = html.replace('<h2>','**').replace('</h2>','**')
    html = html.replace('<h1>','**').replace('</h1>','**')
    html = html.replace('<em>','/').replace('</em>','/')
    html = html.replace('<tr>', '\n')
    html = html.replace('</p>', '\n')
    html = re.sub('<br\s*/?>', '\n', html)
    html = re.sub('<.*?>', ' ', html)
    html = html.replace(' ' * 2, ' ')

    # strip all lines
    html = '\n'.join([x.strip() for x in html.splitlines()])
    html = html.replace('\n' * 2, '\n')

    for i, url in enumerate(url_index):
        if i == 0:
            html += '\n\n'
        html += ustr('[%s] %s\n') % (i+1, url)

    return html

def generate_tracking_message_id(res_id):
    """Returns a string that can be used in the Message-ID RFC822 header field

       Used to track the replies related to a given object thanks to the "In-Reply-To"
       or "References" fields that Mail User Agents will set.
    """
    try:
        rnd = random.SystemRandom().random()
    except NotImplementedError:
        rnd = random.random()
    rndstr = ("%.15f" % rnd)[2:]
    return "<%.15f.%s-openerp-%s@%s>" % (time.time(), rndstr, res_id, socket.gethostname())

def email_send(email_from, email_to, subject, body, email_cc=None, email_bcc=None, reply_to=False,
               attachments=None, message_id=None, references=None, openobject_id=False, debug=False, subtype='plain', headers=None,
               smtp_server=None, smtp_port=None, ssl=False, smtp_user=None, smtp_password=None, cr=None, uid=None):
    """Low-level function for sending an email (deprecated).

    :deprecate: since OpenERP 6.1, please use ir.mail_server.send_email() instead.
    :param email_from: A string used to fill the `From` header, if falsy,
                       config['email_from'] is used instead.  Also used for
                       the `Reply-To` header if `reply_to` is not provided
    :param email_to: a sequence of addresses to send the mail to.
    """

    # If not cr, get cr from current thread database
    if not cr:
        db_name = getattr(threading.currentThread(), 'dbname', None)
        if db_name:
            cr = pooler.get_db_only(db_name).cursor()
        else:
            raise Exception("No database cursor found, please pass one explicitly")

    # Send Email
    try:
        mail_server_pool = pooler.get_pool(cr.dbname).get('ir.mail_server')
        res = False
        # Pack Message into MIME Object
        email_msg = mail_server_pool.build_email(email_from, email_to, subject, body, email_cc, email_bcc, reply_to,
                   attachments, message_id, references, openobject_id, subtype, headers=headers)

        res = mail_server_pool.send_email(cr, uid or 1, email_msg, mail_server_id=None,
                       smtp_server=smtp_server, smtp_port=smtp_port, smtp_user=smtp_user, smtp_password=smtp_password,
                       smtp_encryption=('ssl' if ssl else None), smtp_debug=debug)
    except Exception:
        _logger.exception("tools.email_send failed to deliver email")
        return False
    finally:
        cr.close()
    return res

def email_split(text):
    """ Return a list of the email addresses found in ``text`` """
    if not text:
        return []
    return re.findall(r'([^ ,<@]+@[^> ,]+)', text)

def append_content_to_html(html, content, plaintext=True):
    """Append extra content at the end of an HTML snippet, trying
       to locate the end of the HTML document (</body>, </html>, or
       EOF), and wrapping the provided content in a <pre/> block
       unless ``plaintext`` is False. A side-effect of this
       method is to coerce all HTML tags to lowercase in ``html``,
       and strip enclosing <html> or <body> tags in content if
       ``plaintext`` is False.

       :param str html: html tagsoup (doesn't have to be XHTML)
       :param str content: extra content to append
       :param bool plaintext: whether content is plaintext and should
           be wrapped in a <pre/> tag.
    """
    html = ustr(html)
    if plaintext:
        content = u'\n<pre>%s</pre>\n' % ustr(content)
    else:
        content = re.sub(r'(?i)(</?html.*>|</?body.*>|<!\W*DOCTYPE.*>)', '', content)
        content = u'\n%s\n' % ustr(content)
    # Force all tags to lowercase
    html = re.sub(r'(</?)\W*(\w+)([ >])',
        lambda m: '%s%s%s' % (m.group(1), m.group(2).lower(), m.group(3)), html)
    insert_location = html.find('</body>')
    if insert_location == -1:
        insert_location = html.find('</html>')
    if insert_location == -1:
        return '%s%s' % (html, content)
    return '%s%s%s' % (html[:insert_location], content, html[insert_location:])
