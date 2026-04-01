# -*- coding: utf-8 -*-
"""
Drill-down controller for Rehab Management financial reports.

Route  : POST /rehab_management/report/drilldown
Auth   : user
Input  : JSON { account_id, date_from, date_to, company_id }
Output : ir.actions.act_window — opens account.move.line in list view,
         filtered to the exact set of journal items that make up the
         clicked balance cell.  Each row in that list links to its
         parent account.move (invoice / bill / payment / entry).
"""

from odoo import http
from odoo.http import request
import json


class RehabDrilldownController(http.Controller):

    @http.route(
        '/rehab_management/report/drilldown',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def drilldown(self, account_id=None, date_from=None, date_to=None,
                  company_id=None, **kw):
        """
        Return an ir.actions.act_window that opens account.move.line
        filtered to the clicked cell.  The journal-items list view
        allows clicking any row to open its source document.
        """
        domain = [('parent_state', '=', 'posted')]

        if account_id:
            domain.append(('account_id', '=', int(account_id)))
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        if company_id:
            domain.append(('company_id', '=', int(company_id)))

        # Find the Odoo built-in list view for account.move.line so the
        # user sees the standard columns (journal, partner, debit, credit …)
        # and can still click a row to open the parent account.move form.
        MoveLine = request.env['account.move.line']
        list_view = request.env.ref(
            'account.view_move_line_tree',
            raise_if_not_found=False,
        )
        form_view = request.env.ref(
            'account.view_move_form',
            raise_if_not_found=False,
        )

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Journal Items',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'views': [
                (list_view.id if list_view else False, 'list'),
                (form_view.id if form_view else False, 'form'),
            ],
            'domain': domain,
            'context': {
                'search_default_posted': 1,
                # This context key makes clicking a row open the
                # *parent journal entry* (account.move) form, which
                # links to the source invoice / bill / payment.
                'form_view_ref': 'account.view_move_form',
            },
            'target': 'current',
        }
        return action
