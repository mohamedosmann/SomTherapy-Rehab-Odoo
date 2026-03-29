from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RehabFinancialReportWizard(models.TransientModel):
    _name = 'rehab.financial.report.wizard'
    _description = 'Financial Report Wizard'

    date_from = fields.Date(string='Start Date', required=True, default=lambda self: fields.Date.today().replace(day=1, month=1))
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)
    report_type = fields.Selection([
        ('pl', 'Profit & Loss Statement'),
        ('bs', 'Balance Sheet (Financial Position)'),
        ('tb', 'Trial Balance'),
        ('aged_receivable', 'Aged Receivable (Customer Aging)'),
        ('aged_payable', 'Aged Payable (Vendor Aging)'),
        ('customer_ledger', 'Customer Ledger (Transactions)'),
        ('vendor_ledger', 'Vendor Ledger (Transactions)'),
        ('cf', 'Cash Flow Statement'),
        ('summary', 'Executive Summary'),
        ('tax', 'Tax Return'),
    ], string='Report Type', required=True, default='pl')
    
    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Range')
    ], string='Period Type', default='custom')

    enable_comparison = fields.Boolean(string='Compare with Previous Period', default=False)
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', required=True, default='posted')

    def action_generate_report(self):
        self.ensure_one()
        data = self._get_report_data()
        return self.env.ref('rehab_management.action_report_financial_statement_v2').report_action(self, data=data)

    def action_view_report_html(self):
        self.ensure_one()
        data = self._get_report_data()
        return self.env.ref('rehab_management.action_report_financial_statement_html_v2').report_action(self, data=data)

    def auto_open_report(self):
        """
        Called directly from menus to skip the wizard and show the report with default dates.
        """
        self.ensure_one()
        return self.action_view_report_html()

    @api.model
    def action_direct_open(self, report_type):
        """
        Creates a dummy wizard and returns the report action.
        """
        wizard = self.create({'report_type': report_type})
        return wizard.action_view_report_html()

    def _get_report_data(self):
        return {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_from': str(self.date_from) if self.date_from else '',
                'date_to': str(self.date_to) if self.date_to else '',
                'report_type': self.report_type,
                'target_move': self.target_move,
                'enable_comparison': self.enable_comparison,
                'period_type': self.period_type,
            }
        }
