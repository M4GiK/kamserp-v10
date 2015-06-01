# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from openerp.osv import osv
from openerp.report import report_sxw


class account_analytic_cost_ledger(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_analytic_cost_ledger, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'lines_g': self._lines_g,
            'lines_a': self._lines_a,
            'account_sum_debit': self._account_sum_debit,
            'account_sum_credit': self._account_sum_credit,
            'account_sum_balance': self._account_sum_balance,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'sum_balance': self._sum_balance,
        })
        self.children = {}      # a memo for the method _get_children

    def _get_children(self, accounts):
        """ return all children accounts of the given accounts
            :param accounts: list of browse records of 'account.analytic.account'
            :return: tuple of account ids
        """
        analytic_obj = self.pool.get('account.analytic.account')
        res = set()
        for account in accounts:
            if account.id not in self.children:
                self.children[account.id] = analytic_obj.search(self.cr, self.uid, [('parent_id', 'child_of', [account.id])])
            res.update(self.children[account.id])
        return tuple(res)

    def _lines_g(self, account, date1, date2):
        self.cr.execute("SELECT sum(aal.amount) AS balance, aa.code AS code, aa.name AS name, aa.id AS id \
                FROM account_account AS aa, account_analytic_line AS aal \
                WHERE (aal.account_id IN %s) AND (aal.date>=%s) AND (aal.date<=%s) AND (aal.general_account_id=aa.id) AND aa.active \
                GROUP BY aa.code, aa.name, aa.id ORDER BY aa.code", (self._get_children([account]), date1, date2))
        res = self.cr.dictfetchall()
        for r in res:
            r['debit'] = r['balance'] if r['balance'] > 0 else 0.0
            r['credit'] = -r['balance'] if r['balance'] < 0 else 0.0
        return res

    def _lines_a(self, general_account, account, date1, date2):
        self.cr.execute("SELECT aal.name AS name, aal.code AS code, aal.amount AS balance, aal.date AS date, aaj.code AS cj FROM account_analytic_line AS aal, account_analytic_journal AS aaj \
                WHERE (aal.general_account_id=%s) AND (aal.account_id IN %s) AND (aal.date>=%s) AND (aal.date<=%s) \
                AND (aal.journal_id=aaj.id) \
                ORDER BY aal.date, aaj.code, aal.code", (general_account['id'], self._get_children([account]), date1, date2))
        res = self.cr.dictfetchall()
        for r in res:
            r['debit'] = r['balance'] if r['balance'] > 0 else 0.0
            r['credit'] = -r['balance'] if r['balance'] < 0 else 0.0
        return res

    def _account_sum_debit(self, account, date1, date2):
        return self._sum_debit([account], date1, date2)

    def _account_sum_credit(self, account, date1, date2):
        return self._sum_credit([account], date1, date2)

    def _account_sum_balance(self, account, date1, date2):
        debit = self._account_sum_debit(account, date1, date2)
        credit = self._account_sum_credit(account, date1, date2)
        return (debit-credit)

    def _sum_debit(self, accounts, date1, date2):
        self.cr.execute("SELECT sum(amount) FROM account_analytic_line WHERE account_id IN %s AND date>=%s AND date<=%s AND amount>0",
            (self._get_children(accounts), date1, date2,))
        return self.cr.fetchone()[0] or 0.0

    def _sum_credit(self, accounts, date1, date2):
        self.cr.execute("SELECT -sum(amount) FROM account_analytic_line WHERE account_id IN %s AND date>=%s AND date<=%s AND amount<0",
            (self._get_children(accounts), date1, date2,))
        return self.cr.fetchone()[0] or 0.0

    def _sum_balance(self, accounts, date1, date2):
        debit = self._sum_debit(accounts, date1, date2)
        credit = self._sum_credit(accounts, date1, date2)
        return (debit-credit)


class report_analyticcostledger(osv.AbstractModel):
    _name = 'report.account.report_analyticcostledger'
    _inherit = 'report.abstract_report'
    _template = 'analytic.report_analyticcostledger'
    _wrapped_report_class = account_analytic_cost_ledger
