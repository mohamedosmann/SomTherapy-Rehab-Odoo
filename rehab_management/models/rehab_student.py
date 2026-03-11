from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RehabStudent(models.Model):
    _name = 'rehab.student'
    _description = 'Rehab Student'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Financial Account', ondelete='restrict', help="Link to Odoo's native partner for accounting.")
    name = fields.Char(related='partner_id.name', string='Name', store=True, readonly=False)
    student_id = fields.Char(string='Student ID', required=True, copy=False)
    phone = fields.Char(string='Phone')
    type = fields.Selection([
        ('Normal', 'Normal'),
        ('VIP', 'VIP')
    ], string='Type', default='Normal', tracking=True)
    status = fields.Selection([
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ], string='Status', default='Active', tracking=True)
    department = fields.Char(string='Department')
    is_archived = fields.Boolean(string='Archived', default=False)

    # Documents & Identity
    profile_image = fields.Binary(string='Profile Image')
    passport_image = fields.Binary(string='Passport Image')
    cid_letter = fields.Binary(string='CID Letter')
    contract_url = fields.Char(string='Contract URL')
    uni_certificates = fields.Binary(string='University Certificates')

    # Kin of Next
    kin1_name = fields.Char(string='Kin 1 Name')
    kin1_phone = fields.Char(string='Kin 1 Phone')
    kin1_image = fields.Binary(string='Kin 1 Image')
    kin2_name = fields.Char(string='Kin 2 Name')
    kin2_phone = fields.Char(string='Kin 2 Phone')
    kin2_image = fields.Binary(string='Kin 2 Image')

    room_id = fields.Many2one('rehab.room', string='Room')
    class_id = fields.Many2one('rehab.class', string='Class')
    
    # Financial Fields
    monthly_fee = fields.Float(string='Monthly Fee', compute='_compute_monthly_fee', store=True)
    last_billing_date = fields.Date(string='Last Billing Date')
    prepaid_balance = fields.Float(string='Prepaid Balance', default=0.0)
    opening_balance = fields.Float(string='Opening Balance', default=0.0)
    opening_balance_date = fields.Date(string='Opening Balance Date')

    case_ids = fields.One2many('rehab.discipline.case', 'student_id', string='Discipline Cases')

    _student_id_unique = models.Constraint(
        'UNIQUE(student_id)',
        'Student ID must be unique!'
    )

    @api.depends('type', 'room_id.type')
    def _compute_monthly_fee(self):
        for record in self:
            # Basic Logic: VIP gets a base rate, plus room type adjustments
            base_rate = 500.0 if record.type == 'VIP' else 300.0
            room_extra = 0.0
            if record.room_id:
                room_extra = 100.0 if record.room_id.type == 'VIP' else 50.0
            record.monthly_fee = base_rate + room_extra

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('partner_id') and vals.get('name'):
                # Automatically create a partner if not provided
                partner = self.env['res.partner'].create({
                    'name': vals.get('name'),
                    'customer_rank': 1,
                    'is_company': False,
                })
                vals['partner_id'] = partner.id
        return super(RehabStudent, self).create(vals_list)
