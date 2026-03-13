from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RehabDailyCollectionWizard(models.TransientModel):
    _name = 'rehab.daily.collection.wizard'
    _description = 'Daily Collection Report Wizard'

    date = fields.Date(string='Report Date', required=True, default=fields.Date.today)
    journal_ids = fields.Many2many('account.journal', string='Journals', 
                                    domain=[('type', 'in', ['bank', 'cash'])],
                                    default=lambda self: self.env['account.journal'].search([('type', 'in', ['bank', 'cash'])]))

    def action_generate_report(self):
        self.ensure_one()
        data = {
            'date': self.date,
            'journal_ids': self.journal_ids.ids,
        }
        return self.env.ref('rehab_management.action_report_daily_collection').report_action(self, data=data)
