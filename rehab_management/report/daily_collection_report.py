from odoo import models, api, fields, _

class DailyCollectionReport(models.AbstractModel):
    _name = 'report.rehab_management.report_daily_collection'
    _description = 'Daily Collection Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        date = data.get('date', fields.Date.today())
        journal_ids = data.get('journal_ids', [])
        
        journals = self.env['account.journal'].browse(journal_ids)
        journal_data = []
        grand_total = 0.0

        for journal in journals:
            # Search for posted payments on that day for that journal
            payments = self.env['account.payment'].search([
                ('date', '=', date),
                ('journal_id', '=', journal.id),
                ('state', '=', 'posted'),
                ('payment_type', '=', 'inbound')
            ])
            
            p_lines = []
            j_total = 0.0
            for p in payments:
                p_lines.append({
                    'name': p.partner_id.name,
                    'ref': p.ref or p.name,
                    'amount': p.amount,
                })
                j_total += p.amount
            
            if p_lines:
                journal_data.append({
                    'journal_name': journal.name,
                    'lines': p_lines,
                    'total': j_total,
                })
                grand_total += j_total

        return {
            'doc_ids': docids,
            'date': date,
            'journal_data': journal_data,
            'grand_total': grand_total,
            'company': self.env.company,
        }
