from odoo import models, fields, api, _

class RehabStaff(models.Model):
    _name = 'rehab.staff'
    _description = 'Rehab Staff'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Related Partner', ondelete='restrict')
    name = fields.Char(related='partner_id.name', store=True, readonly=False)
    staff_id = fields.Char(string='Staff ID', required=True, copy=False)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    job_role = fields.Selection([
        ('teacher', 'Teacher'),
        ('cleaner', 'Cleaner'),
        ('security', 'Security'),
        ('admin', 'Admin'),
        ('other', 'Other')
    ], string='Role', default='teacher', tracking=True)
    specialization = fields.Char(string='Specialization')
    department = fields.Char(string='Department')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='active', tracking=True)
    
    image = fields.Binary(string='Image')
    class_ids = fields.One2many('rehab.class', 'teacher_id', string='Classes') # Map classes to staff
    
    salary_amount = fields.Float(string='Monthly Salary', default=0.0)
    
    # Identity Documents
    passport_image = fields.Binary(string='Passport Image')
    cid_letter = fields.Binary(string='CID Letter')
    uni_certificates = fields.Binary(string='University Certificates')
    contract_url = fields.Char(string='Contract URL')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('partner_id'):
                partner_vals = {
                    'name': vals.get('name'),
                    'email': vals.get('email'),
                    'phone': vals.get('phone'),
                    'is_company': False,
                    'customer_rank': 0,
                    'supplier_rank': 1,
                }

                # Determine the payable account for the partner
                account_id = False
                account = self.env['account.account'].search([('code', '=', '201200')], limit=1)
                if not account:
                    account = self.env['account.account'].search([('account_type', '=', 'liability_payable')], limit=1)
                if account:
                    account_id = account.id
                
                if account_id:
                    partner_vals['property_account_payable_id'] = account_id

                partner = self.env['res.partner'].create(partner_vals)
                vals['partner_id'] = partner.id
        return super(RehabStaff, self).create(vals_list)
