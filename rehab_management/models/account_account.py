from odoo import models, fields

class AccountAccount(models.Model):
    _inherit = 'account.account'

    ifrs_note = fields.Text(string='IFRS Note/Disclosure')
    ifrs_category = fields.Selection([
        ('revenue', 'Revenue'),
        ('cost_of_sales', 'Cost of Sales'),
        ('other_income', 'Other Income'),
        ('dist_costs', 'Distribution Costs'),
        ('admin_exp', 'Administrative Expenses'),
        ('other_exp', 'Other Expenses'),
        ('finance_costs', 'Finance Costs'),
        ('income_tax', 'Income Tax'),
        ('current_asset', 'Current Asset'),
        ('non_current_asset', 'Non-Current Asset'),
        ('current_liab', 'Current Liability'),
        ('non_current_liab', 'Non-Current Liability'),
        ('equity', 'Equity')
    ], string='IFRS Category', help="Category for IFRS Financial Statement classification")
