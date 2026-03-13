from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RehabStaffPaymentWizard(models.TransientModel):
    _name = 'rehab.staff.payment.wizard'
    _description = 'Staff Salary Disbursement Wizard'

    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    staff_ids = fields.Many2many('rehab.staff', string='Staff Members', default=lambda self: self.env['rehab.staff'].search([('status', '=', 'active')]))

    def action_generate_bills(self):
        if not self.staff_ids:
            raise UserError(_("Please select at least one staff member."))

        # Get settings or fallbacks
        ICP = self.env['ir.config_parameter'].sudo()
        expense_account_id = ICP.get_param('rehab_management.staff_salary_account_id')
        payable_account_id = ICP.get_param('rehab_management.staff_payable_account_id')

        # Robust Journal Selection: must be a 'purchase' journal
        journal_id = int(ICP.get_param('rehab_management.staff_journal_id', 0))
        journal = self.env['account.journal'].browse(journal_id)
        
        if not journal.exists() or journal.type != 'purchase':
            # Fallback 1: Try XML ID
            journal = self.env.ref('rehab_management.journal_staff_expenses', raise_if_not_found=False)
            if not journal or journal.type != 'purchase':
                # Fallback 2: Search for ANY purchase journal
                journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)

        if not journal:
            raise UserError(_("No 'Purchase' journal found for staff salaries. Please create a Vendor Bills journal in Accounting settings."))

        expense_account = self.env['account.account'].browse(int(expense_account_id)) if expense_account_id else self.env.ref('rehab_management.account_staff_salaries', raise_if_not_found=False)
        payable_account = self.env['account.account'].browse(int(payable_account_id)) if payable_account_id else self.env.ref('rehab_management.account_staff_payable', raise_if_not_found=False)

        bills = self.env['account.move']
        errors = []
        for staff in self.staff_ids:
            if not staff.partner_id:
                errors.append(_("Staff %s has no linked partner.") % staff.name)
                continue
            
            if staff.salary_amount <= 0:
                continue

            try:
                bill_vals = {
                    'move_type': 'in_invoice',
                    'partner_id': staff.partner_id.id,
                    'invoice_date': self.date,
                    'invoice_origin': _("Staff Salary - %s") % self.date.strftime('%B %Y'),
                }
                if journal:
                    bill_vals['journal_id'] = journal.id
                    
                line_vals = {
                    'name': _("Monthly Salary (%s) - %s") % (staff.job_role, self.date.strftime('%B %Y')),
                    'quantity': 1.0,
                    'price_unit': staff.salary_amount,
                }
                if expense_account:
                    line_vals['account_id'] = expense_account.id
                
                bill_vals['invoice_line_ids'] = [(0, 0, line_vals)]
                
                bill = self.env['account.move'].create(bill_vals)
                bills |= bill
            except Exception as e:
                errors.append(_("Failed for %s: %s") % (staff.name, str(e)))

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
