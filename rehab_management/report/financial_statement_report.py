from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FinancialStatementReport(models.AbstractModel):
    _name = 'report.rehab_management.report_financial_statement'
    _description = 'Financial Statement Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        form = {}
        if data and data.get('form'):
            form = data['form']
        elif docids:
            wizard = self.env['rehab.financial.report.wizard'].browse(docids)
            if wizard:
                wizard = wizard[0]
                form = {
                    'date_from': wizard.date_from.strftime('%Y-%m-%d') if wizard.date_from else '',
                    'date_to': wizard.date_to.strftime('%Y-%m-%d') if wizard.date_to else '',
                    'report_type': wizard.report_type,
                    'target_move': wizard.target_move,
                }
        
        if not form:
            raise UserError(_("No report parameters found. Please try opening the report from the menu again."))

        date_from = form.get('date_from')
        date_to = form.get('date_to')
        report_type = form.get('report_type')
        target_move = form.get('target_move', 'posted')

        lines = []
        if report_type == 'pl':
            lines = self._get_profit_loss_data(date_from, date_to, target_move)
        elif report_type == 'bs':
            lines = self._get_balance_sheet_data(date_to, target_move)
        elif report_type == 'tb':
            lines = self._get_trial_balance_data(date_from, date_to, target_move)
        elif report_type == 'cf':
            lines = self._get_cash_flow_data(date_from, date_to, target_move)
        elif report_type == 'summary':
            lines = self._get_executive_summary_data(date_from, date_to, target_move)
        elif report_type in ('aged_receivable', 'aged_payable'):
            lines = self._get_aged_balance_data(date_to, target_move, report_type)

        return {
            'doc_ids': docids,
            'doc_model': 'rehab.financial.report.wizard',
            'date_from': date_from,
            'date_to': date_to,
            'report_type': report_type,
            'lines': lines,
            'res_company': self.env.company,
        }

    def _get_profit_loss_data(self, date_from, date_to, target_move):
        """
        Logic for P&L:
        Revenue - COGS = Gross Profit
        Gross Profit - Expenses = Net Profit
        """
        domain = [('date', '>=', date_from), ('date', '<=', date_to), ('parent_state', '=', target_move), ('account_id.account_type', 'in', ('income', 'income_other', 'expense', 'expense_depreciation', 'expense_direct_cost'))]
        
        move_lines = self.env['account.move.line'].search(domain)
        
        income_total = -sum(move_lines.filtered(lambda l: l.account_id.account_type in ('income', 'income_other')).mapped('balance'))
        cogs_total = sum(move_lines.filtered(lambda l: l.account_id.account_type == 'expense_direct_cost').mapped('balance'))
        expense_total = sum(move_lines.filtered(lambda l: l.account_id.account_type in ('expense', 'expense_depreciation')).mapped('balance'))
        
        gross_profit = income_total - cogs_total
        net_profit = gross_profit - expense_total
        
        return [
            {'name': _('Total Revenue'), 'balance': income_total, 'notes': []},
            {'name': _('Cost of Revenue (COGS)'), 'balance': cogs_total, 'notes': []},
            {'name': _('Gross Profit'), 'balance': gross_profit, 'notes': []},
            {'name': _('Operating Expenses'), 'balance': expense_total, 'notes': []},
            {'name': _('Net Profit / (Loss)'), 'balance': net_profit, 'notes': []},
        ]

    def _get_balance_sheet_data(self, date_to, target_move):
        """
        Logic for Balance Sheet:
        Assets = Liabilities + Equity
        """
        domain = [('date', '<=', date_to), ('parent_state', '=', target_move)]
        move_lines = self.env['account.move.line'].search(domain)
        
        assets = sum(move_lines.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'asset_cash', 'asset_current', 'asset_non_current', 'asset_fixed', 'asset_prepayments')).mapped('balance'))
        liabilities = -sum(move_lines.filtered(lambda l: l.account_id.account_type in ('liability_payable', 'liability_current', 'liability_non_current')).mapped('balance'))
        equity = -sum(move_lines.filtered(lambda l: l.account_id.account_type == 'equity').mapped('balance'))
        
        # P&L effect on Retained Earnings (all income/expense till date_to)
        pl_net = -sum(move_lines.filtered(lambda l: l.account_id.account_type in ('income', 'income_other', 'expense', 'expense_depreciation', 'expense_direct_cost')).mapped('balance'))
        equity += pl_net

        return [
            {'name': _('Total Assets'), 'balance': assets, 'notes': []},
            {'name': _('Total Liabilities'), 'balance': liabilities, 'notes': []},
            {'name': _('Total Equity (incl. Retained Earnings)'), 'balance': equity, 'notes': []},
        ]

    def _get_trial_balance_data(self, date_from, date_to, target_move):
        """
        Logic for Trial Balance:
        Lists all accounts with their debit and credit totals.
        """
        accounts = self.env['account.account'].search([])
        res = []
        for account in accounts:
            domain = [('account_id', '=', account.id), ('date', '>=', date_from), ('date', '<=', date_to), ('parent_state', '=', target_move)]
            lines = self.env['account.move.line'].search(domain)
            debit = sum(lines.mapped('debit'))
            credit = sum(lines.mapped('credit'))
            if debit != 0 or credit != 0:
                res.append({
                    'code': account.code,
                    'name': account.name,
                    'debit': debit,
                    'credit': credit,
                    'balance': debit - credit
                })
        return res

    def _get_cash_flow_data(self, date_from, date_to, target_move):
        """
        Simplified Cash Flow (Indirect Method logic)
        """
        domain = [('account_id.account_type', '=', 'asset_cash'), ('date', '>=', date_from), ('date', '<=', date_to), ('parent_state', '=', target_move)]
        lines = self.env['account.move.line'].search(domain)
        
        cash_in = sum(lines.filtered(lambda l: l.debit > 0).mapped('debit'))
        cash_out = sum(lines.filtered(lambda l: l.credit > 0).mapped('credit'))
        
        return [
            {'name': _('Opening Cash Balance'), 'balance': 0.0, 'notes': [_("Placeholder for historical opening balance")]},
            {'name': _('Total Cash Inflow'), 'balance': cash_in, 'notes': []},
            {'name': _('Total Cash Outflow'), 'balance': -cash_out, 'notes': []},
            {'name': _('Net Increase/Decrease in Cash'), 'balance': cash_in - cash_out, 'notes': []},
        ]

    def _get_executive_summary_data(self, date_from, date_to, target_move):
        """
        Executive Summary combining key metrics
        """
        pl = self._get_profit_loss_data(date_from, date_to, target_move)
        bs = self._get_balance_sheet_data(date_to, target_move)
        
        return [
            {'name': _('Total Revenue (MTD/YTD)'), 'balance': pl[0]['balance'], 'notes': []},
            {'name': _('Net Profit'), 'balance': pl[4]['balance'], 'notes': []},
            {'name': _('Cash Position'), 'balance': bs[0]['balance'], 'notes': [_("Total Liquidity Assets")]},
        ]

    def _get_aged_balance_data(self, date_to, target_move, report_type):
        """
        Aging Logic:
        0-30, 31-60, 61-90, 90+ days
        """
        account_type = 'asset_receivable' if report_type == 'aged_receivable' else 'liability_payable'
        domain = [
            ('account_id.account_type', '=', account_type),
            ('date', '<=', date_to),
            ('parent_state', '=', target_move),
            ('reconciled', '=', False)
        ]
        move_lines = self.env['account.move.line'].search(domain)
        partners = move_lines.mapped('partner_id')
        
        res = []
        today = fields.Date.today()
        
        for partner in partners:
            p_lines = move_lines.filtered(lambda l: l.partner_id == partner)
            
            b_0_30 = 0.0
            b_31_60 = 0.0
            b_61_90 = 0.0
            b_90_plus = 0.0
            
            for line in p_lines:
                due_date = line.date_maturity or line.date
                days_overdue = (today - due_date).days
                
                amount = line.balance if account_type == 'asset_receivable' else -line.balance
                
                if days_overdue <= 30:
                    b_0_30 += amount
                elif days_overdue <= 60:
                    b_31_60 += amount
                elif days_overdue <= 90:
                    b_61_90 += amount
                else:
                    b_90_plus += amount
            
            total = b_0_30 + b_31_60 + b_61_90 + b_90_plus
            if total != 0:
                res.append({
                    'name': partner.name,
                    'balance': total,
                    'notes': [
                        _("0-30 days: %s") % b_0_30,
                        _("31-60 days: %s") % b_31_60,
                        _("61-90 days: %s") % b_61_90,
                        _("90+ days: %s") % b_90_plus
                    ]
                })
        return res
