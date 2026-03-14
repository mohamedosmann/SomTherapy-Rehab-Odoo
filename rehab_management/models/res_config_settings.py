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

    rehab_staff_salary_account_id = fields.Many2one(
        'account.account',
        string="Staff Salary Account",
        domain=[('account_type', '=', 'expense')],
        config_parameter='rehab_management.staff_salary_account_id',
        help="Expense account used for staff salaries."
    )

    rehab_staff_payable_account_id = fields.Many2one(
        'account.account',
        string="Staff Payable Account",
        domain=[('account_type', '=', 'liability_payable')],
        config_parameter='rehab_management.staff_payable_account_id',
        help="Liability account used for staff payroll/vendor bills."
    )

    rehab_staff_journal_id = fields.Many2one(
        'account.journal',
        string="Staff Expense Journal",
        domain=[('type', '=', 'purchase')],
        config_parameter='rehab_management.staff_journal_id',
        help="Default journal used for generating staff salary bills."
    )

    # Robust fix for Odoo 18 Owl error: "is_installed_sale" field is undefined
    is_installed_sale = fields.Boolean(string="Is Sales Installed?")
    
    # Fix for "days_to_purchase" and related fields often missing in base settings views
    days_to_purchase = fields.Float(string="Days to Purchase", config_parameter='purchase.days_to_purchase')
    is_installed_purchase = fields.Boolean(string="Is Purchase Installed?")

    # Sequence Configuration
    rehab_student_id_prefix = fields.Char(
        string="Student ID Prefix",
        default="STD-",
        help="Prefix used for Student IDs (e.g. STD-)"
    )
    
    rehab_staff_id_prefix = fields.Char(
        string="Staff ID Prefix",
        default="STAFF-",
        help="Prefix used for Staff IDs (e.g. STAFF-)"
    )

    def set_values(self):
        super().set_values()
        # Update the actual sequence records when settings are saved
        student_seq = self.env.ref('rehab_management.seq_rehab_student', raise_if_not_found=False)
        if student_seq:
            student_seq.prefix = self.rehab_student_id_prefix
        
        staff_seq = self.env.ref('rehab_management.seq_rehab_staff', raise_if_not_found=False)
        if staff_seq:
            staff_seq.prefix = self.rehab_staff_id_prefix

    def get_values(self):
        res = super().get_values()
        # Pull current prefix from the sequences
        student_seq = self.env.ref('rehab_management.seq_rehab_student', raise_if_not_found=False)
        if student_seq:
            res['rehab_student_id_prefix'] = student_seq.prefix
            
        staff_seq = self.env.ref('rehab_management.seq_rehab_staff', raise_if_not_found=False)
        if staff_seq:
            res['rehab_staff_id_prefix'] = staff_seq.prefix
        return res
