from odoo import models, api, fields, _

class StudentStatementReport(models.AbstractModel):
    _name = 'report.rehab_management.report_student_statement'
    _description = 'Student Statement Report Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['rehab.student'].browse(docids)
        
        doc_data = []
        for student in docs:
            if not student.partner_id:
                continue
            
            # Fetch all move lines for this partner
            # We want invoices and payments
            domain = [
                ('partner_id', '=', student.partner_id.id),
                ('parent_state', '=', 'posted'),
                ('account_id.account_type', '=', 'asset_receivable')
            ]
            amls = self.env['account.move.line'].search(domain, order='date asc, id asc')
            
            lines = []
            running_balance = 0.0
            
            # Initial balance if needed (optional)
            
            for aml in amls:
                # Debit = Invoice amount, Credit = Payment amount
                running_balance += (aml.debit - aml.credit)
                
                lines.append({
                    'date': aml.date,
                    'ref': aml.move_id.name,
                    'label': aml.name or aml.move_id.ref or '',
                    'debit': aml.debit,
                    'credit': aml.credit,
                    'balance': running_balance,
                })
            
            doc_data.append({
                'student': student,
                'lines': lines,
                'final_balance': running_balance,
            })

        return {
            'doc_ids': docids,
            'doc_model': 'rehab.student',
            'docs': docs,
            'doc_data': doc_data,
            'company': self.env.company,
        }
