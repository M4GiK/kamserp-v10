#!/usr/bin/python
# -*- encoding: utf-8 -*-

import re
import smtplib
import email, mimetypes
from email.Header import decode_header
from email.MIMEText import MIMEText
import xmlrpclib

email_re = re.compile(r"""
	([a-zA-Z][\w\.-]*[a-zA-Z0-9]     # username part
	@                                # mandatory @ sign
	[a-zA-Z0-9][\w\.-]*              # domain must start with a letter ... Ged> why do we include a 0-9 then?
	 \.
	 [a-z]{2,3}                      # TLD
	)
	""", re.VERBOSE)
project_re = re.compile(r"\[([0-9]+)\]", re.UNICODE)
command_re = re.compile("^Set-([a-z]+) *: *(.+)$", re.I + re.UNICODE)

priorities = {
	'1': '1 (Highest)',
	'2': '2 (High)',
	'3': '3 (Normal)',
	'4': '4 (Low)',
	'5': '5 (Lowest)',
}

class rpc_proxy(object):
	def __init__(self, uid, passwd, host='localhost', port=8069, path='object', dbname='terp'):
		self.rpc = xmlrpclib.ServerProxy('http://%s:%s/%s' % (host, port, path))
		self.user_id = uid
		self.passwd = passwd
		self.dbname = dbname
	
	def __call__(self, *request):
		print self.dbname, self.user_id, self.passwd
		return self.rpc.execute(self.dbname, self.user_id, self.passwd, *request)

class email_parser(object):
	def __init__(self, uid, password, section, email, email_default, dbname):
		print '* Email parser'
		self.rpc = rpc_proxy(uid, password, dbname=dbname)
		try:
			self.section_id = int(section)
		except:
			self.section_id = self.rpc('crm.case.section', 'search', [('code','=',section)])[0]
		print 'Section ID', self.section_id
		self.email = email
		self.email_default = email_default
		self.canal_id = False

	def email_get(self, email_from):
		res = email_re.search(email_from)
		return res and res.group(1)

	def partner_get(self, email):
		mail = self.email_get(email)
		adr_ids = self.rpc('res.partner.address', 'search', [('email', '=', mail)])
		if not adr_ids:
			return {}
		adr = self.rpc('res.partner.address', 'read', adr_ids, ['partner_id'])
		return {
			'partner_address_id': adr[0]['id'],
			'partner_id': adr[0]['partner_id'][0]
		}

	def _decode_header(self, s):
		from email.Header import decode_header
		s = decode_header(s)
		return ''.join(map(lambda x:x[0].decode(x[1] or 'ascii', 'replace'), s))

	def msg_new(self, msg):
		description = self.msg_body_get(msg)
		data = {
			'name': self._decode_header(msg['Subject']),
			'description': description,
			'section_id': self.section_id,
			'email_from': self._decode_header(msg['From']),
			'email_cc': self._decode_header(msg['Cc'] or ''),
			'canal_id': self.canal_id
		}
		data.update(self.partner_get(self._decode_header(msg['From'])))
		id = self.rpc('crm.case', 'create', data)
		return id

	def msg_body_get(self, msg):
		body = ''
		if msg.is_multipart():
			for part in msg.get_payload():
				if (part.get_content_maintype()=='text') and (part.get_content_subtype()=='plain'):
					body += part.get_payload(decode=1).decode(part.get_charsets()[0])
		else:
			body = msg.get_payload(decode=1).decode(msg.get_charsets()[0])
		return body

	def msg_user(self, msg, id):
		body = self.msg_body_get(msg)
		data = {
			'description': body,
			'email_last': body
		}

		# handle email body commands (ex: Set-State: Draft)
		actions = {}
		for line in body.split('\n'):
			res = command_re.match(line)
			if res:
				actions[res.group(1).lower()] = res.group(2).lower()

		act = 'case_close'
		if 'state' in actions:
			if actions['state'] in ['draft','close','cancel','open','pending']:
				act = 'case_' + actions['state']

		for k1,k2 in [('cost','planned_cost'),('revenue','planned_revenue'),('probability','probability')]:
			try:
				data[k2] = float(actions[k1])
			except:
				pass

		if 'priority' in actions:
			if actions['priority'] in ('1','2','3','4','5'):
				data['priority'] = actions['priority']

		if 'partner' in actions:
			data['email_from'] = actions['partner']

		if 'user' in actions:
			uids = self.rpc('res.users', 'name_search', actions['user'])
			if uids:
				data['user_id'] = uids[0][0]

		self.rpc('crm.case', act, [id])
		self.rpc('crm.case', 'write', [id], data)
		return id

	def msg_send(self, msg, emails, priority=None):
		if not len(emails):
			return False
		del msg['To']
		print '0'
		msg['To'] = emails[0]
		if len(emails)>1:
			if 'Cc' in msg:
				del msg['Cc']
			msg['Cc'] = ','.join(emails[1:])
		msg['Reply-To'] = msg['From'] + ',' + self.email
		if priority:
			msg['X-Priority'] = priorities.get(priority, '3 (Normal)')
		s = smtplib.SMTP()
		print '1'
		s.connect()
		print '2'
		s.sendmail(self.email, emails[0], msg.as_string())
		print '3'
		s.close()
		print '4'
		print 'Email Sent To', emails[0], emails[1:]
		return True

	def msg_partner(self, msg, id):
		body = self.msg_body_get(msg)
		act = 'case_open'
		self.rpc('crm.case', act, [id])
		body2 = '\n'.join(map(lambda l: '> '+l, (body or '').split('\n')))
		data = {
			'description': body2,
			'email_last': body,
		}
		self.rpc('crm.case', 'write', [id], data)
		return id

	def msg_test(self, msg, case_str):
		if not case_str:
			return (False, False)
		emails = self.rpc('crm.case', 'emails_get', int(case_str))
		return (int(case_str), emails)

	def parse(self, msg):
		try:
			case_str = project_re.search(msg.get('Subject', ''))
			(case_id, emails) = self.msg_test(msg, case_str and case_str.group(1))
			if case_id:
				if emails[0] and self.email_get(emails[0])==self.email_get(self._decode_header(msg['From'])):
					print 'From User', case_id
					self.msg_user(msg, case_id)
				else:
					print 'From Partner', case_id
					self.msg_partner(msg, case_id)
			else:
				case_id = self.msg_new(msg)
				msg['subject'] = '['+str(case_id)+'] '+self._decode_header(msg['subject'])
				print 'Case', case_id, 'created...'

			emails = self.rpc('crm.case', 'emails_get', case_id)
			priority = emails[3]
			em = [emails[0], emails[1]] + (emails[2] or '').split(',')
			emails = map(self.email_get, filter(None, em))

			mm = [self._decode_header(msg['From']), self._decode_header(msg['To'])]+self._decode_header(msg.get('Cc','')).split(',')
			msg_mails = map(self.email_get, filter(None, mm))

			emails = filter(lambda m: m and m not in msg_mails, emails)
			self.msg_send(msg, emails, priority)
		except:
			print 'Sending mail to default address', self.email_default
			if self.email_default:
				a = self._decode_header(msg['Subject'])
				del msg['Subject']
				msg['Subject'] = '[TinyERP-CaseError] ' + a
				self.msg_send(msg, self.email_default.split(','))
		return emails

if __name__ == '__main__':
	import sys, optparse
	parser = optparse.OptionParser(
		usage='usage: %prog [options]',
		version='%prog v1.0')

	group = optparse.OptionGroup(parser, "Note",
		"This program parse a mail from standard input and communicate "
		"with the Tiny ERP server for case management in the CRM module.")
	parser.add_option_group(group)

	parser.add_option("-u", "--user", dest="userid", help="ID of the user in Tiny ERP", default=3, type='int')
	parser.add_option("-p", "--password", dest="password", help="Password of the user in Tiny ERP", default='admin')
	parser.add_option("-e", "--email", dest="email", help="Email address used in the From field of outgoing messages")
	parser.add_option("-s", "--section", dest="section", help="ID or code of the case section", default="support")
	parser.add_option("-m", "--default", dest="default", help="Default eMail in case of any trouble.", default=None)
	parser.add_option("-d", "--dbname", dest="dbname", help="Database name (default: terp)", default='terp')

	(options, args) = parser.parse_args()
	parser = email_parser(options.userid, options.password, options.section, options.email, options.default, dbname=options.dbname)
	print 
	print '-.- ICI'
	msg_txt = email.message_from_file(sys.stdin)
	print 'Mail Sent to ', parser.parse(msg_txt)

