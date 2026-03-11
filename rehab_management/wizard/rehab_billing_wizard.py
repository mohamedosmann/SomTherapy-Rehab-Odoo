from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RehabBillingWizard(models.TransientModel):
    _name = 'rehab.billing.wizard'
    _description = 'Monthly Billing Wizard'

    billing_date = fields.Date(string='Billing Date', default=fields.Date.context_today, required=True)
    student_ids = fields.Many2many('rehab.student', string='Students', default=lambda self: self.env['rehab.student'].search([('status', '=', 'Active')]))

    def action_generate_invoices(self):
        if not self.student_ids:
            raise UserError(_("Please select at least one student."))

        invoices = self.env['account.move']
        for student in self.student_ids:
            if not student.partner_id:
                continue
            
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': student.partner_id.id,
                'invoice_date': self.billing_date,
                'invoice_origin': _("Monthly Billing - %s") % self.billing_date.strftime('%B %Y'),
                'invoice_line_ids': [(0, 0, {
                    'name': _("Monthly Rehab & Housing Fee - %s") % self.billing_date.strftime('%B %Y'),
                    'quantity': 1.0,
                    'price_unit': student.monthly_fee,
                })],
            }
            inv = self.env['account.move'].create(invoice_vals)
            student.last_billing_date = self.billing_date
            invoices |= inv

        return {
            'name': _('Generated Invoices'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', invoices.ids)],
            'context': {'create': False},
        }
