from odoo import models, fields

class AccountAccount(models.Model):
    _inherit = 'account.account'

    ifrs_note = fields.Text(string='IFRS Note/Disclosure')
    ifrs_category = fields.Selection([
        ('asset', '1000 - Assets (Money You Own/Are Owed)'),
        ('liability', '2000 - Liabilities (Money You Owe)'),
        ('equity', '3000 - Equity (Owner Investment/Profit)'),
        ('income', '4000 - Income (Sales & Revenue)'),
        ('expense', '5000 - Expenses (Business Spending)')
    ], string='QuickBooks Category', help="Simplified category for non-accountants")
    
    qb_balance = fields.Monetary(string='Current Balance', compute='_compute_qb_balance')
    qb_debit = fields.Monetary(string='Debit Volume', compute='_compute_qb_balance')
    qb_credit = fields.Monetary(string='Credit Volume', compute='_compute_qb_balance')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    def _compute_qb_balance(self):
        for account in self:
            res = self.env['account.move.line'].read_group(
                [('account_id', '=', account.id), ('parent_state', '=', 'posted')],
                ['debit', 'credit', 'balance'],
                ['account_id']
            )
            if res:
                account.qb_debit = res[0]['debit']
                account.qb_credit = res[0]['credit']
                account.qb_balance = res[0]['balance']
            else:
                account.qb_debit = 0.0
                account.qb_credit = 0.0
                account.qb_balance = 0.0

    def _quickbooks_transform(self):
        """ Automatically renames and archives accounts to match QuickBooks UX """
        # 1. Plain English Renaming
        translations = {
            'Accounts Receivable': 'Money You Will Receive (Patients)',
            'Accounts Payable': 'Money You Owe (Suppliers)',
            'Cash': 'Physical Cash in Hand',
            'Bank': 'Bank Account Balance',
            'Liquidity': 'Cash & Bank',
            'Cogs': 'Direct Costs (Meals/Materials)',
            'Revenue': 'Income from Services',
            'Expense': 'Business Spending',
        }
        
        # 2. Archive list (unnecessary for non-accountants)
        to_archive_search = [
            'Cash Difference', 'Exchange Difference', 'Write-off', 
            'Interim', 'Suspense', 'Discount', 'Rounding'
        ]

        for acc in self.search([('company_id', '=', self.env.company.id)]):
            # Apply names
            for tech_name, plain_name in translations.items():
                if tech_name.lower() in acc.name.lower():
                    acc.name = plain_name
            
            # Apply Codes logic
            if not acc.code.startswith(('1','2','3','4','5')):
                if acc.account_type in ('asset_receivable', 'asset_cash', 'asset_current', 'asset_prepayments'):
                     acc.code = '1' + acc.code.lstrip('0')[:3]
                elif acc.account_type in ('liability_payable', 'liability_current', 'liability_non_current'):
                     acc.code = '2' + acc.code.lstrip('0')[:3]
                elif acc.account_type == 'equity':
                     acc.code = '3' + acc.code.lstrip('0')[:3]
                elif acc.account_type in ('income', 'income_other'):
                     acc.code = '4' + acc.code.lstrip('0')[:3]
                elif acc.account_type in ('expense', 'expense_depreciation', 'expense_direct_cost'):
                     acc.code = '5' + acc.code.lstrip('0')[:3]
            
            # Archive technical noise
            if any(term.lower() in acc.name.lower() for term in to_archive_search):
                acc.active = False
            
            # Auto-set the Natural Group
            if acc.code.startswith('1'): acc.ifrs_category = 'asset'
            elif acc.code.startswith('2'): acc.ifrs_category = 'liability'
            elif acc.code.startswith('3'): acc.ifrs_category = 'equity'
            elif acc.code.startswith('4'): acc.ifrs_category = 'income'
            elif acc.code.startswith('5'): acc.ifrs_category = 'expense'

    @api.model_create_multi
    def create(self, vals_list):
        # Auto-category assignment based on code
        for vals in vals_list:
            if 'code' in vals and not vals.get('ifrs_category'):
                code = vals['code']
                if code.startswith('1'): vals['ifrs_category'] = 'asset'
                elif code.startswith('2'): vals['ifrs_category'] = 'liability'
                elif code.startswith('3'): vals['ifrs_category'] = 'equity'
                elif code.startswith('4'): vals['ifrs_category'] = 'income'
                elif code.startswith('5'): vals['ifrs_category'] = 'expense'
        return super().create(vals_list)

    def action_quickbooks_transform(self):
        self._quickbooks_transform()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Chart of Accounts has been simplified and reorganized.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }
