from odoo import models, api, _

class FinancialStatementReport(models.AbstractModel):
    _name = 'report.rehab_management.report_financial_statement'
    _description = 'Financial Statement Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        form = data.get('form')
        date_from = form.get('date_from')
        date_to = form.get('date_to')
        report_type = form.get('report_type')
        target_move = form.get('target_move')

        lines = self._get_lines(report_type, date_from, date_to, target_move)

        return {
            'doc_ids': docids,
            'doc_model': 'rehab.financial.report.wizard',
            'data': data,
            'date_from': date_from,
            'date_to': date_to,
            'report_type': report_type,
            'lines': lines,
            'company': self.env.company,
        }

    def _get_lines(self, report_type, date_from, date_to, target_move):
        lines = []
        domain = [('date', '<=', date_to)]
        if target_move == 'posted':
            domain.append(('parent_state', '=', 'posted'))
        
        if report_type == 'pl':
            domain.append(('date', '>=', date_from))
            # Categories for P&L
            categories = [
                ('revenue', 'Revenue'),
                ('cost_of_sales', 'Cost of Sales'),
                ('other_income', 'Other Income'),
                ('dist_costs', 'Distribution Costs'),
                ('admin_exp', 'Administrative Expenses'),
                ('other_exp', 'Other Expenses'),
                ('finance_costs', 'Finance Costs'),
                ('income_tax', 'Income Tax')
            ]
            for cat_code, cat_name in categories:
                balance = self._get_balance([('account_id.ifrs_category', '=', cat_code)] + domain)
                # Revenue/Income are Credit-based, Expenses are Debit-based
                if cat_code in ['revenue', 'other_income']:
                    balance = -balance # Odoo stores Credit as negative
                
                notes = self.env['account.account'].search([('ifrs_category', '=', cat_code)]).mapped('ifrs_note')
                notes = [n for n in notes if n]
                
                lines.append({
                    'name': cat_name,
                    'balance': balance,
                    'is_total': False,
                    'notes': notes
                })
        
        elif report_type == 'bs':
            # Categories for Balance Sheet
            categories = [
                ('non_current_asset', 'Non-Current Assets'),
                ('current_asset', 'Current Assets'),
                ('equity', 'Equity'),
                ('non_current_liab', 'Non-Current Liabilities'),
                ('current_liab', 'Current Liabilities')
            ]
            for cat_code, cat_name in categories:
                balance = self._get_balance([('account_id.ifrs_category', '=', cat_code)] + domain)
                if cat_code in ['equity', 'non_current_liab', 'current_liab']:
                    balance = -balance
                
                notes = self.env['account.account'].search([('ifrs_category', '=', cat_code)]).mapped('ifrs_note')
                notes = [n for n in notes if n]

                lines.append({
                    'name': cat_name,
                    'balance': balance,
                    'is_total': False,
                    'notes': notes
                })
        
        return lines

    def _get_balance(self, domain):
        aml = self.env['account.move.line'].search(domain)
        return sum(aml.mapped('balance'))
