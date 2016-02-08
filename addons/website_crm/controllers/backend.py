# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from math import floor
import time
import operator
import babel

from openerp.addons.website.controllers.backend import WebsiteBackend
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class WebsiteCrmBackend(WebsiteBackend):

    @http.route()
    def fetch_dashboard_data(self, date_from, date_to):

        results = super(WebsiteCrmBackend, self).fetch_dashboard_data(date_from, date_to)

        date_from = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
        date_to = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)

        lead_domain = [
            ('team_id.website_ids', '!=', False),
        ]

        lead_ids = request.env['crm.lead'].search(
            lead_domain + [
                ('create_date', '>=', date_from.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                ('create_date', '<=', date_to.strftime(DEFAULT_SERVER_DATE_FORMAT))],
            )

        leads = [{
            'create_date': datetime.strptime(lead.create_date, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT),
            'campaign_id': lead.campaign_id.name,
            'medium_id': lead.medium_id.name,
            'source_id': lead.source_id.name,
        } for lead in lead_ids]

        leads_graph = self._compute_lead_graph(date_from, date_to, lead_domain)
        previous_leads_graph = self._compute_lead_graph(date_from - timedelta(days=(date_to - date_from).days), date_from, lead_domain, previous=True)

        results['dashboards']['leads'] = {
            'graph': [
                {
                    'values': leads_graph,
                    'key': 'Leads',
                },
                {
                    'values': previous_leads_graph,
                    'key': 'Previous Leads',
                },
            ],
            'leads': leads,
        }

        return results

    def _compute_lead_graph(self, date_from, date_to, lead_domain, previous=False):

        days_between = (date_to - date_from).days
        date_list = [(date_from + timedelta(days=x)) for x in range(0, days_between + 1)]

        daily_leads = request.env['crm.lead'].read_group(
            domain=lead_domain + [
                ('create_date', '>=', date_from.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                ('create_date', '<=', date_to.strftime(DEFAULT_SERVER_DATE_FORMAT))],
            fields=['create_date'],
            groupby='create_date:day')

        daily_leads_dict = {l['create_date:day']: l['create_date_count'] for l in daily_leads}

        leads_graph = [{
            '0': d.strftime(DEFAULT_SERVER_DATE_FORMAT) if not previous else (d + timedelta(days=days_between)).strftime(DEFAULT_SERVER_DATE_FORMAT),
            # Respect read_group format in models.py
            '1': daily_leads_dict.get(babel.dates.format_date(d, format='dd MMM yyyy', locale=request.env.context.get('lang', 'en_US')), 0)
        } for d in date_list]

        return leads_graph
