from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import json

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
                    'enable_comparison': wizard.enable_comparison,
                    'period_type': wizard.period_type,
                }
        
        if not form:
            raise UserError(_("No report parameters found. Please try opening the report from the menu again."))

        date_from = form.get('date_from')
        date_to = form.get('date_to')
        report_type = form.get('report_type')
        target_move = form.get('target_move', 'posted')
        enable_comparison = form.get('enable_comparison', False)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or ''
        if '142.93.121.232' in base_url and ':8069' not in base_url:
            base_url = base_url.replace('142.93.121.232', '142.93.121.232:8069')
        elif not base_url:
            base_url = 'http://142.93.121.232:8069'

        lines = []
        comparison_lines = []
        
        if report_type == 'pl':
            lines = self._get_profit_loss_data(date_from, date_to, target_move)
            if enable_comparison:
                d1 = fields.Date.from_string(date_from)
                d2 = fields.Date.from_string(date_to)
                delta = d2 - d1
                prev_date_to = d1 - datetime.timedelta(days=1)
                prev_date_from = prev_date_to - delta
                comparison_lines = self._get_profit_loss_data(prev_date_from.strftime('%Y-%m-%d'), prev_date_to.strftime('%Y-%m-%d'), target_move)

        elif report_type == 'bs':
            lines = self._get_balance_sheet_data(date_to, target_move)
            if enable_comparison:
                d2 = fields.Date.from_string(date_to)
                prev_date_to = d2 - datetime.timedelta(days=365) # Comparison with last year
                comparison_lines = self._get_balance_sheet_data(prev_date_to.strftime('%Y-%m-%d'), target_move)

        elif report_type == 'tb':
            lines = self._get_trial_balance_data(date_from, date_to, target_move)
        elif report_type == 'customer_ledger':
            lines = self._get_ledger_data('customer', date_from, date_to, target_move)
        elif report_type == 'vendor_ledger':
            lines = self._get_ledger_data('vendor', date_from, date_to, target_move)
        elif report_type == 'cf':
            lines = self._get_cash_flow_data(date_from, date_to, target_move)
        elif report_type in ('aged_receivable', 'aged_payable'):
            lines = self._get_aged_balance_data(date_to, target_move, report_type)

        return {
            'doc_ids': docids,
            'doc_model': 'rehab.financial.report.wizard',
            'date_from': date_from,
            'date_to': date_to,
            'report_type': report_type,
            'lines': lines,
            'comparison_lines': comparison_lines,
            'enable_comparison': enable_comparison,
            'res_company': self.env.company,
            'base_url': base_url,
        }

    def _get_profit_loss_data(self, date_from, date_to, target_move):
        """
        IFRS Profit & Loss with Full Transparency
        """
        domain = [('date', '>=', date_from), ('date', '<=', date_to), ('parent_state', '=', target_move)]
        move_lines = self.env['account.move.line'].search(domain)
        
        # 1. Total Revenue
        rev_lines = move_lines.filtered(lambda l: l.account_id.account_type in ('income', 'income_other'))
        income_total = -sum(rev_lines.mapped('balance'))

        # 2. COGS
        cogs_lines = move_lines.filtered(lambda l: l.account_id.account_type == 'expense_direct_cost')
        cogs_total = sum(cogs_lines.mapped('balance'))

        gross_profit = income_total - cogs_total

        # 3. Major Operating Categories (Grouped)
        categories = [
            {'name': _('Staff Expenses'), 'code_prefix': '6011', 'level': 2},
            {'name': _('Rent & Lease'), 'code_prefix': '6012', 'level': 2},
            {'name': _('Utilities'), 'code_prefix': '6013', 'level': 2},
            {'name': _('Office & Stationery'), 'code_prefix': '6014', 'level': 2},
            {'name': _('Maintenance & Repairs'), 'code_prefix': '6015', 'level': 2},
            {'name': _('Transport & Fuel'), 'code_prefix': '6016', 'level': 2},
        ]
        
        res = [
            {'name': _('Total Revenue'), 'balance': income_total, 'level': 1, 'domain': [('account_id.account_type', 'in', ('income', 'income_other')), ('date', '>=', date_from), ('date', '<=', date_to)]},
            {'name': _('Cost of Goods Sold (COGS)'), 'balance': cogs_total, 'level': 1, 'domain': [('account_id.account_type', '=', 'expense_direct_cost'), ('date', '>=', date_from), ('date', '<=', date_to)]},
            {'name': _('GROSS PROFIT'), 'balance': gross_profit, 'level': 0, 'is_total': True},
        ]

        total_operating_expenses = 0.0
        applied_prefixes = [c['code_prefix'] for c in categories]

        for cat in categories:
            prefix = str(cat['code_prefix'])
            cat_lines = move_lines.filtered(lambda l: prefix in l.account_id.code)
            bal = sum(cat_lines.mapped('balance'))
            if bal != 0:
                res.append({
                    'name': cat['name'],
                    'balance': bal,
                    'level': cat['level'],
                    'domain': [('account_id.code', 'like', prefix + '%'), ('date', '>=', date_from), ('date', '<=', date_to)]
                })
                total_operating_expenses += bal

        # 4. Detailed Expenses (LISTED BY CATEGORY/PRODUCT)
        # This groups entries by the "Expense Category" (Product) selected in the Expense module
        other_exp_lines = move_lines.filtered(
            lambda l: l.account_id.account_type in ('expense', 'expense_depreciation') and 
            not any(str(p) in l.account_id.code for p in applied_prefixes)
        )
        
        groups = {}
        for l in other_exp_lines:
            # Group by account and product to maintain drill-down accuracy
            key = (l.account_id.id, l.product_id.id if l.product_id else False)
            if key not in groups:
                # If product exists, it's the "Expense Category" the user is looking for
                name = l.product_id.name if l.product_id else l.account_id.name
                groups[key] = {
                    'name': name, 
                    'balance': 0.0, 
                    'account_id': l.account_id.id,
                    'product_id': l.product_id.id if l.product_id else False
                }
            groups[key]['balance'] += l.balance

        # Sort by name for a clean report
        sorted_groups = sorted(groups.values(), key=lambda x: x['name'])
        
        for group in sorted_groups:
            if group['balance'] != 0:
                domain = [('account_id', '=', group['account_id']), ('date', '>=', date_from), ('date', '<=', date_to)]
                if group['product_id']:
                    domain.append(('product_id', '=', group['product_id']))
                else:
                    domain.append(('product_id', '=', False))

                res.append({
                    'name': group['name'],
                    'balance': group['balance'],
                    'level': 2,
                    'domain': domain
                })
                total_operating_expenses += group['balance']
        
        net_profit = gross_profit - total_operating_expenses
        
        res.append({'name': _('TOTAL OPERATING EXPENSES'), 'balance': total_operating_expenses, 'level': 0, 'is_total': True})
        res.append({'name': _('NET PROFIT / (LOSS)'), 'balance': net_profit, 'level': 0, 'is_total': True, 'is_final': True})

        for r in res:
            r.update({'domain_str': json.dumps(r.get('domain', []))})
        return res

    def _get_balance_sheet_data(self, date_to, target_move):
        """
        Professional Balance Sheet Structure
        """
        domain = [('date', '<=', date_to), ('parent_state', '=', target_move)]
        move_lines = self.env['account.move.line'].search(domain)
        
        # Current Assets
        curr_asset_lines = move_lines.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'asset_cash', 'asset_current', 'asset_prepayments'))
        curr_assets = sum(curr_asset_lines.mapped('balance'))
        
        fixed_assets = sum(move_lines.filtered(lambda l: l.account_id.account_type == 'asset_fixed').mapped('balance'))
        total_assets = curr_assets + fixed_assets

        curr_liabilities = -sum(move_lines.filtered(lambda l: l.account_id.account_type in ('liability_payable', 'liability_current')).mapped('balance'))
        long_liabilities = -sum(move_lines.filtered(lambda l: l.account_id.account_type == 'liability_non_current').mapped('balance'))
        total_liabilities = curr_liabilities + long_liabilities

        base_equity = -sum(move_lines.filtered(lambda l: l.account_id.account_type == 'equity').mapped('balance'))
        pl_net = -sum(move_lines.filtered(lambda l: l.account_id.account_type in ('income', 'income_other', 'expense', 'expense_depreciation', 'expense_direct_cost')).mapped('balance'))
        total_equity = base_equity + pl_net

        res = [
            {'name': _('Current Assets'), 'balance': curr_assets, 'level': 1, 'domain': [('account_id.account_type', 'in', ('asset_receivable', 'asset_cash', 'asset_current', 'asset_prepayments')), ('date', '<=', date_to)]},
            {'name': _('Fixed Assets'), 'balance': fixed_assets, 'level': 1, 'domain': [('account_id.account_type', '=', 'asset_fixed'), ('date', '<=', date_to)]},
            {'name': _('TOTAL ASSETS'), 'balance': total_assets, 'level': 0, 'is_total': True},
            
            {'name': _('Current Liabilities'), 'balance': curr_liabilities, 'level': 1, 'domain': [('account_id.account_type', 'in', ('liability_payable', 'liability_current')), ('date', '<=', date_to)]},
            {'name': _('Long-term Liabilities'), 'balance': long_liabilities, 'level': 1, 'domain': [('account_id.account_type', '=', 'liability_non_current'), ('date', '<=', date_to)]},
            {'name': _('TOTAL LIABILITIES'), 'balance': total_liabilities, 'level': 0, 'is_total': True},
            
            {'name': _('Owner Equity'), 'balance': base_equity, 'level': 1, 'domain': [('account_id.account_type', '=', 'equity'), ('date', '<=', date_to)]},
            {'name': _('Retained Earnings'), 'balance': pl_net, 'level': 1, 'domain': [('account_id.account_type', 'in', ('income', 'income_other', 'expense', 'expense_depreciation', 'expense_direct_cost')), ('date', '<=', date_to)]},
            {'name': _('TOTAL EQUITY'), 'balance': total_equity, 'level': 0, 'is_total': True},
            
            {'name': _('TOTAL LIABILITIES & EQUITY'), 'balance': total_liabilities + total_equity, 'level': 0, 'is_total': True, 'is_final': True},
        ]
        for r in res:
            r['domain_str'] = json.dumps(r.get('domain', []))
        return res

    def _get_ledger_data(self, ledger_type, date_from, date_to, target_move):
        account_type = 'asset_receivable' if ledger_type == 'customer' else 'liability_payable'
        domain = [('account_id.account_type', '=', account_type), ('date', '>=', date_from), ('date', '<=', date_to), ('parent_state', '=', target_move)]
        move_lines = self.env['account.move.line'].search(domain, order='date asc')
        partners = move_lines.mapped('partner_id')
        res = []
        for partner in partners:
            p_lines = move_lines.filtered(lambda l: l.partner_id == partner)
            txs = []
            rb = 0.0
            for l in p_lines:
                amt = l.balance if ledger_type == 'customer' else -l.balance
                rb += amt
                txs.append({
                    'date': l.date,
                    'ref': l.move_id.name,
                    'desc': l.name or '',
                    'debit': l.debit,
                    'credit': l.credit,
                    'balance': rb,
                    'domain_str': json.dumps([('id', '=', l.id)])
                })
            res.append({'name': partner.name or 'N/A', 'is_partner_header': True, 'transactions': txs, 'balance': rb})
        return res

    def _get_trial_balance_data(self, date_from, date_to, target_move):
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
                    'balance': debit - credit,
                    'domain_str': json.dumps([('account_id', '=', account.id), ('date', '>=', date_from), ('date', '<=', date_to)])
                })
        return res

    def _get_cash_flow_data(self, date_from, date_to, target_move):
        pl = self._get_profit_loss_data(date_from, date_to, target_move)
        net_income = pl[-1]['balance']
        cash_moves = self.env['account.move.line'].search([('account_id.account_type', '=', 'asset_cash'), ('date', '>=', date_from), ('date', '<=', date_to), ('parent_state', '=', target_move)])
        return [
            {'name': _('Net Income (Base)'), 'balance': net_income},
            {'name': _('Cash Inflow'), 'balance': sum(cash_moves.filtered(lambda l: l.debit > 0).mapped('debit'))},
            {'name': _('Cash Outflow'), 'balance': -sum(cash_moves.filtered(lambda l: l.credit > 0).mapped('credit'))},
            {'name': _('Net Cash Change'), 'balance': sum(cash_moves.mapped('balance'))},
        ]

    def _get_aged_balance_data(self, date_to, target_move, report_type):
        account_type = 'asset_receivable' if report_type == 'aged_receivable' else 'liability_payable'
        move_lines = self.env['account.move.line'].search([('account_id.account_type', '=', account_type), ('date', '<=', date_to), ('parent_state', '=', target_move), ('reconciled', '=', False)])
        res = []
        today = fields.Date.today()
        for partner in move_lines.mapped('partner_id'):
            p_lines = move_lines.filtered(lambda l: l.partner_id == partner)
            aging = {'0-30': 0.0, '31-60': 0.0, '61-90': 0.0, '90+': 0.0}
            for line in p_lines:
                days = (today - (line.date_maturity or line.date)).days
                amt = line.balance if account_type == 'asset_receivable' else -line.balance
                if days <= 30: aging['0-30'] += amt
                elif days <= 60: aging['31-60'] += amt
                elif days <= 90: aging['61-90'] += amt
                else: aging['90+'] += amt
            res.append({'name': partner.name, 'balance': sum(aging.values()), 'notes': [f"{k}: {v}" for k,v in aging.items()]})
        return res
