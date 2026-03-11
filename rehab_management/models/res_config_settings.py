from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rehab_fee_product_id = fields.Many2one(
        'product.product',
        string="Monthly Fee Product",
        domain=[('type', 'in', ('service', 'consu'))],
        config_parameter='rehab_management.fee_product_id',
        help="Default product used for Monthly Student Billing."
    )
    
    rehab_fine_product_id = fields.Many2one(
        'product.product',
        string="Discipline Fine Product",
        domain=[('type', 'in', ('service', 'consu'))],
        config_parameter='rehab_management.fine_product_id',
        help="Default product used when invoicing disciplinary fines."
    )
    
    rehab_invoice_journal_id = fields.Many2one(
        'account.journal',
        string="Invoice Journal",
        domain=[('type', '=', 'sale')],
        config_parameter='rehab_management.invoice_journal_id',
        help="Default journal used for generating student invoices."
    )
