from odoo import models, api, _

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    @api.model_create_multi
    def create(self, vals_list):
        journals = super().create(vals_list)
        for journal in journals:
            if journal.type in ('bank', 'cash'):
                journal._force_direct_posting_accounts()
        return journals

    def write(self, vals):
        res = super().write(vals)
        if 'default_account_id' in vals:
            for journal in self:
                if journal.type in ('bank', 'cash'):
                    journal._force_direct_posting_accounts()
        return res

    def _force_direct_posting_accounts(self):
        """
        Enforce direct posting by setting payment method line accounts 
        to the journal's default account.
        """
        self.ensure_one()
        if not self.default_account_id:
            return
            
        # Update inbound lines
        for line in self.inbound_payment_method_line_ids:
            if not line.payment_account_id or line.payment_account_id != self.default_account_id:
                line.payment_account_id = self.default_account_id
                
        # Update outbound lines
        for line in self.outbound_payment_method_line_ids:
            if not line.payment_account_id or line.payment_account_id != self.default_account_id:
                line.payment_account_id = self.default_account_id
