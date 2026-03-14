from odoo import models, fields

class PaymentMethod(models.Model):
    _inherit = 'payment.method'

    image = fields.Binary(required=False)
