from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_advance = fields.Boolean(
        string='Is Advance Payment',
        help='If checked, this payment will be recorded as a liability/asset advance instead of a direct receivable/payable reduction.'
    )
    advance_account_id = fields.Many2one(
        'account.account',
        string='Advance Account',
        compute='_compute_advance_account',
        store=True,
        readonly=False
    )

    @api.depends('is_advance', 'payment_type', 'partner_id')
    def _compute_advance_account(self):
        for payment in self:
            if not payment.is_advance:
                payment.advance_account_id = False
                continue
            
            if payment.payment_type == 'inbound':
                # Customer Advance
                advance_acc = self.env.ref('rehab_management.rehab_account_customer_advance', raise_if_not_found=False)
                if not advance_acc:
                    advance_acc = self.env['account.account'].search([('code', '=', '201400')], limit=1)
                payment.advance_account_id = advance_acc
            else:
                # Vendor Advance
                advance_acc = self.env.ref('rehab_management.rehab_account_vendor_advance', raise_if_not_found=False)
                if not advance_acc:
                    advance_acc = self.env['account.account'].search([('code', '=', '101300')], limit=1)
                payment.advance_account_id = advance_acc

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        """
        Override to change the destination account when it's an advance payment.
        """
        res = super()._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
        
        if self.is_advance and self.advance_account_id:
            # Determine the original destination accounts to replace
            partner_accounts = []
            if self.partner_id:
                if self.partner_id.property_account_receivable_id:
                    partner_accounts.append(self.partner_id.property_account_receivable_id.id)
                if self.partner_id.property_account_payable_id:
                    partner_accounts.append(self.partner_id.property_account_payable_id.id)
            
            if not partner_accounts:
                # Fallback to standard codes if property fields are not set
                partner_accounts = self.env['account.account'].search([
                    ('account_type', 'in', ('asset_receivable', 'liability_payable'))
                ]).ids

            for line in res:
                # Replace partner account with the advance account
                if line.get('account_id') in partner_accounts:
                    line['account_id'] = self.advance_account_id.id
        return res

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            if payment.is_advance:
                payment.message_post(body=_("Advance Payment recorded to account: %s") % payment.advance_account_id.display_name)
        return res
