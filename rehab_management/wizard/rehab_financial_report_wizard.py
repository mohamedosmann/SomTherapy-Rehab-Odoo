from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RehabFinancialReportWizard(models.TransientModel):
    _name = 'rehab.financial.report.wizard'
    _description = 'Financial Report Wizard'

    date_from = fields.Date(string='Start Date', required=True, default=lambda self: fields.Date.today().replace(day=1, month=1))
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)
    report_type = fields.Selection([
        ('pl', 'Statement of Profit or Loss (IFRS)'),
        ('bs', 'Statement of Financial Position (Balance Sheet - IFRS)'),
        ('cf', 'Statement of Cash Flows (IFRS)'),
        ('tb', 'Trial Balance')
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

    def _get_report_data(self):
        return {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'report_type': self.report_type,
                'target_move': self.target_move,
            }
        }
