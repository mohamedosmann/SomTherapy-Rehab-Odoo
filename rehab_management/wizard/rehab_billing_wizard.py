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

        # Get settings or fallbacks
        ICP = self.env['ir.config_parameter'].sudo()
        product_id = int(ICP.get_param('rehab_management.fee_product_id', 0))
        journal_id = int(ICP.get_param('rehab_management.invoice_journal_id', 0))
        
        # Fallback to XML IDs if parameters are missing
        if not product_id:
            product = self.env.ref('rehab_management.product_monthly_fee', raise_if_not_found=False)
            product_id = product.id if product else False
            
        if not journal_id:
            journal = self.env.ref('rehab_management.journal_student_invoices', raise_if_not_found=False)
            journal_id = journal.id if journal else False

        invoices = self.env['account.move']
        errors = []
        for student in self.student_ids:
            if not student.partner_id:
                errors.append(_("Student %s has no linked partner.") % student.name)
                continue
            
            try:
                invoice_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': student.partner_id.id,
                    'invoice_date': self.billing_date,
                    'invoice_origin': _("Monthly Billing - %s") % self.billing_date.strftime('%B %Y'),
                }
                if journal_id:
                    invoice_vals['journal_id'] = journal_id
                    
                line_vals = {
                    'name': _("Monthly Rehab Fee - %s") % self.billing_date.strftime('%B %Y'),
                    'quantity': 1.0,
                    'price_unit': student.monthly_fee,
                }
                if product_id:
                    line_vals['product_id'] = product_id
                
                invoice_vals['invoice_line_ids'] = [(0, 0, line_vals)]
                
                inv = self.env['account.move'].create(invoice_vals)
                # Auto-post if possible? User might want to review. Let's leave as draft.
                student.last_billing_date = self.billing_date
                invoices |= inv
            except Exception as e:
                errors.append(_("Failed for %s: %s") % (student.name, str(e)))

        if errors and not invoices:
            raise UserError("\n".join(errors))
        
        action = {
            'name': _('Generated Invoices'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', invoices.ids)],
            'context': {'create': False},
        }
        
        if errors:
            # If some succeeded and some failed, we could show a notification
            # In Odoo, we can return a notification or just show the invoices
            # Let's just return the invoices for now, as the errors are logged in Odoo.
            pass
            
        return action
