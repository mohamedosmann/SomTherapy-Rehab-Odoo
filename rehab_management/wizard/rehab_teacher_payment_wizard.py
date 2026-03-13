from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RehabTeacherPaymentWizard(models.TransientModel):
    _name = 'rehab.teacher.payment.wizard'
    _description = 'Teacher Salary Disbursement Wizard'

    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    teacher_ids = fields.Many2many('rehab.teacher', string='Teachers', default=lambda self: self.env['rehab.teacher'].search([('status', '=', 'active')]))

    def action_generate_bills(self):
        if not self.teacher_ids:
            raise UserError(_("Please select at least one teacher."))

        # Get settings or fallbacks
        ICP = self.env['ir.config_parameter'].sudo()
        journal_id = ICP.get_param('rehab_management.invoice_journal_id')
        expense_account_id = ICP.get_param('rehab_management.teacher_salary_account_id')
        payable_account_id = ICP.get_param('rehab_management.staff_payable_account_id')

        journal = self.env['account.journal'].browse(int(journal_id)) if journal_id else self.env.ref('rehab_management.journal_staff_expenses', raise_if_not_found=False)
        expense_account = self.env['account.account'].browse(int(expense_account_id)) if expense_account_id else self.env.ref('rehab_management.account_teacher_salaries', raise_if_not_found=False)
        payable_account = self.env['account.account'].browse(int(payable_account_id)) if payable_account_id else self.env.ref('rehab_management.account_staff_payable', raise_if_not_found=False)

        bills = self.env['account.move']
        errors = []
        for teacher in self.teacher_ids:
            if not teacher.partner_id:
                errors.append(_("Teacher %s has no linked partner.") % teacher.name)
                continue
            
            if teacher.salary_amount <= 0:
                continue

            try:
                bill_vals = {
                    'move_type': 'in_invoice',
                    'partner_id': teacher.partner_id.id,
                    'invoice_date': self.date,
                    'invoice_origin': _("Teacher Salary - %s") % self.date.strftime('%B %Y'),
                }
                if journal:
                    bill_vals['journal_id'] = journal.id
                    
                line_vals = {
                    'name': _("Monthly Salary - %s") % self.date.strftime('%B %Y'),
                    'quantity': 1.0,
                    'price_unit': teacher.salary_amount,
                }
                if expense_account:
                    line_vals['account_id'] = expense_account.id
                
                bill_vals['invoice_line_ids'] = [(0, 0, line_vals)]
                
                bill = self.env['account.move'].create(bill_vals)
                bills |= bill
            except Exception as e:
                errors.append(_("Failed for %s: %s") % (teacher.name, str(e)))

        if errors and not bills:
            raise UserError("\n".join(errors))
        
        return {
            'name': _('Generated Salary Bills'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', bills.ids)],
            'context': {'create': False},
        }
