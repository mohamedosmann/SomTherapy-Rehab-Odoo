from odoo import models, fields, api, _

class RehabTeacher(models.Model):
    _name = 'rehab.teacher'
    _description = 'Rehab Teacher'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Related Partner', ondelete='restrict')
    name = fields.Char(related='partner_id.name', store=True, readonly=False)
    teacher_id = fields.Char(string='Teacher ID', required=True, copy=False)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    specialization = fields.Char(string='Specialization')
    department = fields.Char(string='Department')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='active', tracking=True)
    
    image = fields.Binary(string='Image')
    class_ids = fields.One2many('rehab.class', 'teacher_id', string='Classes')
    
    salary_amount = fields.Float(string='Monthly Salary', default=0.0)
    
    # Identity Documents
    passport_image = fields.Binary(string='Passport Image')
    cid_letter = fields.Binary(string='CID Letter')
    uni_certificates = fields.Binary(string='University Certificates')
    contract_url = fields.Char(string='Contract URL')
    
    # _sql_constraints = [
    #     ('teacher_id_unique', 'UNIQUE(teacher_id)', 'Teacher ID must be unique!')
    # ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('partner_id') and vals.get('name'):
                # Try to get the dedicated Staff Payable account from our module
                account_id = self.env.ref('rehab_management.account_staff_payable', raise_if_not_found=False).id
                
                # If not found, find any Liability Payable account as a safe fallback
                if not account_id:
                    fallback = self.env['account.account'].search([('account_type', '=', 'liability_payable')], limit=1)
                    account_id = fallback.id
                
                partner = self.env['res.partner'].create({
                    'name': vals.get('name'),
                    'is_company': False,
                    'supplier_rank': 1, 
                    'property_account_payable_id': account_id,
                })
                vals['partner_id'] = partner.id
        return super(RehabTeacher, self).create(vals_list)
