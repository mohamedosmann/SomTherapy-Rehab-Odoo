from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RehabFinancialReportWizard(models.TransientModel):
    _name = 'rehab.financial.report.wizard'
    _description = 'Financial Report Wizard'

    date_from = fields.Date(string='Start Date', required=True, default=lambda self: fields.Date.today().replace(day=1, month=1))
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)
    report_type = fields.Selection([
        ('pl', 'Statement of Profit or Loss (IFRS)'),
        ('bs', 'Statement of Financial Position (Balance Sheet)'),
        ('cf', 'Statement of Cash Flows'),
        ('summary', 'Executive Summary'),
        ('tax', 'Tax Return (VAT/Sales Tax)'),
        ('tb', 'Trial Balance'),
        ('aged_receivable', 'Aged Receivable (Customer Aging)'),
        ('aged_payable', 'Aged Payable (Vendor Aging)')
    ], string='Report Type', required=True, default='pl')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')
    ], string='Target Moves', required=True, default='posted')

    def action_generate_report(self):
        self.ensure_one()
        data = self._get_report_data()
        return self.env.ref('rehab_management.action_report_financial_statement').report_action(self, data=data)

    def action_view_report_html(self):
        self.ensure_one()
        data = self._get_report_data()
        return self.env.ref('rehab_management.action_report_financial_statement_html').report_action(self, data=data)

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
