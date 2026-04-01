from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_deferred = fields.Boolean(string='Deferred Revenue', default=False)
    deferral_duration = fields.Integer(string='Duration (Months)', default=1)
    deferral_start_date = fields.Date(string='Recognition Start')
    
    # Rehab Specific
    rehab_id = fields.Many2one('rehab.student', string='Rehab Patient')
    rehab_program_id = fields.Many2one('rehab.student.type', string='Rehab Program')

class AccountMove(models.Model):
    _inherit = 'account.move'

    rehab_id = fields.Many2one('rehab.student', string='Rehab Patient')
    rehab_program_id = fields.Many2one('rehab.student.type', string='Rehab Program')

    @api.onchange('rehab_id')
    def _onchange_rehab_id(self):
        if self.rehab_id:
            self.rehab_program_id = self.rehab_id.type_id
            self.partner_id = self.rehab_id.partner_id

    def _prepare_move_line_vals(self, line, name, amount, currency_id, account_id):
        res = super()._prepare_move_line_vals(line, name, amount, currency_id, account_id)
        res.update({
            'rehab_id': self.rehab_id.id,
            'rehab_program_id': self.rehab_program_id.id,
        })
        return res

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
            
            # Search for move lines in the advance accounts safely
            advance_accounts_list = []
            for xml_id in ['rehab_management.rehab_account_customer_advance', 'rehab_management.rehab_account_vendor_advance']:
                acc = self.env.ref(xml_id, raise_if_not_found=False)
                if acc:
                    advance_accounts_list.append(acc.id)
            
            # Fallback to search if ref fails (e.g. initial install or manual deletion of XML ID)
            if not advance_accounts_list:
                advance_accounts_list = self.env['account.account'].search([('code', 'in', ['201400', '101300'])]).ids

            if not advance_accounts_list:
                move.advance_balance = 0.0
                move.has_advance = False
                continue

            domain = [
                ('partner_id', '=', move.partner_id.id),
                ('account_id', 'in', advance_accounts_list),
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
        Creates a reconciliation entry moving balance from Advance Liability to Accounts Receivable,
        then reconciles it with the invoice.
        """
        self.ensure_one()
        if not self.has_advance:
            raise UserError(_("This partner has no available advance balance."))
        
        if self.state != 'posted':
            raise UserError(_("Invoices must be posted before applying advances."))

        advance_accounts_list = []
        for xml_id in ['rehab_management.rehab_account_customer_advance', 'rehab_management.rehab_account_vendor_advance']:
            acc = self.env.ref(xml_id, raise_if_not_found=False)
            if acc:
                advance_accounts_list.append(acc.id)
        
        if not advance_accounts_list:
             advance_accounts_list = self.env['account.account'].search([('code', 'in', ['201400', '101300'])]).ids

        if not advance_accounts_list:
             raise UserError(_("Advance accounts could not be found. Please check your configuration."))

        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('account_id', 'in', advance_accounts_list),
            ('parent_state', '=', 'posted'),
            ('reconciled', '=', False)
        ]
        advance_lines = self.env['account.move.line'].search(domain)
        amount_to_apply = min(self.amount_residual, abs(sum(advance_lines.mapped('balance'))))

        if amount_to_apply <= 0:
            return True

        # Create Reclassification Move
        # Debit: Advance Liability
        # Credit: Accounts Receivable
        reclass_move = self.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.today(),
            'journal_id': self.journal_id.id, # Or a specific reclass journal
            'ref': _('Advance application for %s') % self.name,
            'line_ids': [
                (0, 0, {
                    'name': _('Advance application'),
                    'partner_id': self.partner_id.id,
                    'account_id': advance_lines[0].account_id.id,
                    'debit': amount_to_apply if self.move_type == 'out_invoice' else 0.0,
                    'credit': amount_to_apply if self.move_type == 'in_invoice' else 0.0,
                }),
                (0, 0, {
                    'name': _('Advance application'),
                    'partner_id': self.partner_id.id,
                    'account_id': self.partner_id.property_account_receivable_id.id if self.move_type == 'out_invoice' else self.partner_id.property_account_payable_id.id,
                    'debit': amount_to_apply if self.move_type == 'in_invoice' else 0.0,
                    'credit': amount_to_apply if self.move_type == 'out_invoice' else 0.0,
                }),
            ]
        })
        reclass_move.action_post()

        # Reconcile the new AR/AP line with the Invoice
        reclass_line = reclass_move.line_ids.filtered(lambda l: l.account_id.id in [self.partner_id.property_account_receivable_id.id, self.partner_id.property_account_payable_id.id])
        invoice_line = self.line_ids.filtered(lambda l: l.account_id.id in [self.partner_id.property_account_receivable_id.id, self.partner_id.property_account_payable_id.id])
        
        (reclass_line + invoice_line).reconcile()
        
        # Also reconcile with the original advance payment line
        (reclass_move.line_ids - reclass_line + advance_lines).reconcile()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Advance Applied'),
                'message': _('Successfully applied %s from advance balance.') % amount_to_apply,
                'sticky': False,
                'type': 'success',
            }
        }

    def action_post(self):
        res = super().action_post()
        # Auto-detect advances on post
        for move in self:
            if move.has_advance:
                msg = _("This customer has an advance balance of %s. You can apply it to this invoice.") % move.advance_balance
                move.message_post(body=msg)
        return res
