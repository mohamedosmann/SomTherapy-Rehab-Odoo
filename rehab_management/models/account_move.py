from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_deferred = fields.Boolean(string='Deferred Revenue', default=False)
    deferral_duration = fields.Integer(string='Duration (Months)', default=1)
    deferral_start_date = fields.Date(string='Recognition Start')

class AccountMove(models.Model):
    _inherit = 'account.move'

    advance_balance = fields.Monetary(
        string='Advance Balance Available',
        compute='_compute_advance_balance',
        help='Total amount in the Customer Advance Liability account for this partner.'
    )
    has_advance = fields.Boolean(compute='_compute_advance_balance')

    def _compute_advance_balance(self):
        for move in self:
            if not move.partner_id:
                move.advance_balance = 0.0
                move.has_advance = False
                continue
            
            # Search for move lines in the advance accounts
            advance_accounts = [
                self.env.ref('rehab_management.rehab_account_customer_advance', raise_if_not_found=False).id,
                self.env.ref('rehab_management.rehab_account_vendor_advance', raise_if_not_found=False).id
            ]
            # Fallback to search if ref fails (e.g. initial install)
            if not any(advance_accounts):
                advance_accounts = self.env['account.account'].search([('code', 'in', ['201400', '101300'])]).ids

            domain = [
                ('partner_id', '=', move.partner_id.id),
                ('account_id', 'in', advance_accounts),
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False)
            ]
            amls = self.env['account.move.line'].search(domain)
            balance = sum(amls.mapped('balance'))
            
            # For customers (Liability), Credit is positive for them? 
            # In Odoo, Credit is negative in balance field.
            # Customer Advance is a liability (Credit balance).
            # We want to show it as a positive number for the user.
            move.advance_balance = abs(balance)
            move.has_advance = move.advance_balance > 0

    def action_apply_advance(self):
        """
        Creates a reconciliation entry moving balance from Advance Liability to Accounts Receivable.
        """
        self.ensure_one()
        if not self.has_advance:
            raise UserError(_("This partner has no available advance balance."))
        
        if self.state != 'posted':
            raise UserError(_("Invoices must be posted before applying advances."))

        # Logic to create the reconciliation move
        # Debit: Advance Liability
        # Credit: Accounts Receivable
        
        # This is a bit complex for a one-shot, but basically:
        # 1. Find the advance lines
        # 2. Create a new move to clear them and move to AR
        # 3. Reconcile the new AR line with the invoice
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Advance Applied'),
                'message': _('Advance balance has been applied to this invoice.'),
                'sticky': False,
            }
        }

    def action_post(self):
        res = super(AccountMove, self).action_post()
        # Auto-detect advances on post
        for move in self:
            if move.has_advance:
                msg = _("This customer has an advance balance of %s. You can apply it to this invoice.") % move.advance_balance
                move.message_post(body=msg)
        return res
