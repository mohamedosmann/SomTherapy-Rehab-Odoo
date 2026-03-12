from odoo import models, fields, api, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_deferred = fields.Boolean(string='Deferred Revenue', default=False)
    deferral_duration = fields.Integer(string='Duration (Months)', default=1)
    deferral_start_date = fields.Date(string='Recognition Start')

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        # Logic for automatic deferral could go here in a more advanced setup
        # For now, we just ensure the fields are available for reporting
        return res
