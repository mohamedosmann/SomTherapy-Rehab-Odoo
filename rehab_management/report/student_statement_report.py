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
            total_debit = 0.0
            total_credit = 0.0
            running_balance = 0.0
            
            for aml in amls:
                # Debit = Invoice amount, Credit = Payment amount
                total_debit += aml.debit
                total_credit += aml.credit
                running_balance += (aml.debit - aml.credit)
                
                # Descriptive label
                label = aml.name or ''
                if not label or label == '/':
                    label = aml.move_id.ref or aml.move_id.name
                
                lines.append({
                    'date': aml.date,
                    'ref': aml.move_id.name,
                    'label': label,
                    'type': _('Invoice') if aml.debit > 0 else _('Payment/Credit'),
                    'debit': aml.debit,
                    'credit': aml.credit,
                    'balance': running_balance,
                })
            
            doc_data.append({
                'student': student,
                'lines': lines,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'final_balance': running_balance,
            })

        return {
            'doc_ids': docids,
            'doc_model': 'rehab.student',
            'docs': docs,
            'doc_data': doc_data,
            'company': self.env.company,
        }
