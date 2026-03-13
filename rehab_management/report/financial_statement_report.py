from odoo import models, fields, api, _

class FinancialStatementReport(models.AbstractModel):
    _name = 'report.rehab_management.report_financial_statement'
    _description = 'Financial Statement Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        if data and data.get('form'):
            form = data.get('form')
        elif docids:
            wizard = self.env['rehab.financial.report.wizard'].browse(docids)
            form = {
                'date_from': wizard.date_from,
                'date_to': wizard.date_to,
                'report_type': wizard.report_type,
                'target_move': wizard.target_move,
            }
        else:
            form = {}

        date_from = form.get('date_from', fields.Date.today().replace(day=1, month=1))
        date_to = form.get('date_to', fields.Date.today())
        report_type = form.get('report_type', 'pl')
        target_move = form.get('target_move', 'posted')

        lines = self._get_lines(report_type, date_from, date_to, target_move)
        docs = self.env['rehab.financial.report.wizard'].browse(docids)
        company = self.env.company

        return {
            'doc_ids': docids,
            'doc_model': 'rehab.financial.report.wizard',
            'docs': docs,
            'data': data,
            'date_from': date_from,
            'date_to': date_to,
            'report_type': report_type,
            'lines': lines,
            'company': company,
            'res_company': company,
            'user': self.env.user,
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
                cat_domain = [('account_id.ifrs_category', '=', cat_code)] + domain
                balance = self._get_balance(cat_domain)
                
                # If no IFRS category, try to fallback to standard Odoo account types for major categories
                if balance == 0:
                    if cat_code == 'revenue':
                        balance = self._get_balance([('account_id.account_type', 'in', ('income', 'income_other'))] + domain)
                    elif cat_code == 'admin_exp':
                        balance = self._get_balance([('account_id.account_type', 'in', ('expense', 'expense_depreciation', 'expense_direct_cost'))] + domain)
                
                # Revenue/Income are Credit-based, Expenses are Debit-based
                if cat_code in ['revenue', 'other_income']:
                    balance = -balance 
                
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
                cat_domain = [('account_id.ifrs_category', '=', cat_code)] + domain
                balance = self._get_balance(cat_domain)
                
                # Fallbacks for BS
                if balance == 0:
                    if cat_code == 'current_asset':
                        balance = self._get_balance([('account_id.account_type', 'in', ('asset_receivable', 'asset_cash', 'asset_current'))] + domain)
                    elif cat_code == 'current_liab':
                        balance = self._get_balance([('account_id.account_type', 'in', ('liability_payable', 'liability_current'))] + domain)

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
        
        elif report_type == 'tb':
            # Trial Balance logic: show all accounts with debits/credits
            accounts = self.env['account.account'].search([])
            for account in accounts:
                acc_domain = [('account_id', '=', account.id)] + domain
                amls = self.env['account.move.line'].search(acc_domain)
                debit = sum(amls.mapped('debit'))
                credit = sum(amls.mapped('credit'))
                balance = debit - credit
                if debit != 0 or credit != 0:
                    lines.append({
                        'code': account.code,
                        'name': account.name,
                        'debit': debit,
                        'credit': credit,
                        'balance': balance,
                        'notes': []
                    })
        
        elif report_type == 'summary':
            # Executive Summary: High level KPIs
            # 1. Total Revenue
            revenue = -self._get_balance([('account_id.account_type', 'in', ('income', 'income_other'))] + domain + [('date', '>=', date_from)])
            lines.append({'name': 'Total Revenue (Period)', 'balance': revenue})
            
            # 2. Total Expenses
            expenses = self._get_balance([('account_id.account_type', 'in', ('expense', 'expense_depreciation', 'expense_direct_cost'))] + domain + [('date', '>=', date_from)])
            lines.append({'name': 'Total Expenses (Period)', 'balance': expenses})
            
            # 3. Net Profit
            lines.append({'name': 'Net Profit/Loss', 'balance': revenue - expenses})
            
            # 4. Cash Position
            cash = self._get_balance([('account_id.account_type', '=', 'asset_cash')] + domain)
            lines.append({'name': 'Current Cash Position', 'balance': cash})
            
            # 5. Accounts Receivable
            ar = self._get_balance([('account_id.account_type', '=', 'asset_receivable')] + domain)
            lines.append({'name': 'Total Unpaid Student Invoices (AR)', 'balance': ar})

        elif report_type == 'cf':
            # Simplified Cash Flow: Cash basis (simplified)
            # Cash at start of period
            domain_start = [('date', '<', date_from), ('account_id.account_type', '=', 'asset_cash')]
            if target_move == 'posted': domain_start.append(('parent_state', '=', 'posted'))
            cash_start = self._get_balance(domain_start)
            lines.append({'name': 'Cash at Beginning of Period', 'balance': cash_start})
            
            # Operating Activities (Simplified as Inflow - Outflow)
            cash_in = -self._get_balance([('account_id.account_type', 'in', ('income', 'income_other')), ('date', '>=', date_from), ('date', '<=', date_to)])
            cash_out = self._get_balance([('account_id.account_type', 'in', ('expense', 'expense_depreciation', 'expense_direct_cost')), ('date', '>=', date_from), ('date', '<=', date_to)])
            lines.append({'name': 'Estimated Cash Inflow from Operations', 'balance': cash_in})
            lines.append({'name': 'Estimated Cash Outflow from Operations', 'balance': cash_out})
            
            # Total Change
            lines.append({'name': 'Net Change in Cash', 'balance': cash_in - cash_out})
            lines.append({'name': 'Cash at End of Period', 'balance': cash_start + (cash_in - cash_out)})

        elif report_type == 'tax':
            # Simplified Tax Return
            tax_received = -self._get_balance([('account_id.account_type', '=', 'liability_current'), ('account_id.name', 'ilike', 'tax')] + domain)
            tax_paid = self._get_balance([('account_id.account_type', '=', 'asset_current'), ('account_id.name', 'ilike', 'tax')] + domain)
            lines.append({'name': 'Tax Received on Sales', 'balance': tax_received})
            lines.append({'name': 'Tax Paid on Purchases', 'balance': tax_paid})
            lines.append({'name': 'Net Tax Due/Refund', 'balance': tax_received - tax_paid})

        return lines
        
        return lines

    def _get_balance(self, domain):
        aml = self.env['account.move.line'].search(domain)
        return sum(aml.mapped('balance'))
