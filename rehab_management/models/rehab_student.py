from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class RehabStudentType(models.Model):
    _name = 'rehab.student.type'
    _description = 'Student Type'

    name = fields.Char(string='Type Name', required=True)
    description = fields.Text(string='Description')
    default_monthly_fee = fields.Float(string='Default Monthly Fee', default=300.0)


class RehabStudent(models.Model):
    _name = "rehab.student"
    _description = "Rehab Student"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Financial Account', ondelete='restrict')
    name = fields.Char(related='partner_id.name', string='Name', store=True, readonly=False)
    student_id = fields.Char(string='Student ID', required=True, copy=False)
    phone = fields.Char(string='Phone')
    type_id = fields.Many2one('rehab.student.type', string='Type', tracking=True)
    status = fields.Selection([
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ], string='Status', default='Active', tracking=True)
    department = fields.Char(string='Department')
    is_archived = fields.Boolean(string='Archived', default=False)

    # Re-adding missing fields that are in the XML view to prevent installation errors
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

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
    prepaid_balance = fields.Monetary(string='Prepaid Balance', compute='_compute_prepaid_balance')
    opening_balance = fields.Float(string='Opening Balance', default=0.0)
    opening_balance_date = fields.Date(string='Opening Balance Date')
    
    total_invoiced = fields.Monetary(string='Total Invoiced', compute='_compute_financial_totals')
    total_paid = fields.Monetary(string='Total Paid', compute='_compute_financial_totals')
    total_due = fields.Monetary(string='Total Due', compute='_compute_financial_totals')

    case_ids = fields.One2many('rehab.discipline.case', 'student_id', string='Discipline Cases')

    @api.depends('type_id', 'room_id.extra_charge')
    def _compute_monthly_fee(self):
        for record in self:
            base_rate = record.type_id.default_monthly_fee if record.type_id else 300.0
            room_extra = record.room_id.extra_charge if record.room_id else 0.0
            record.monthly_fee = base_rate + room_extra

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('partner_id') and vals.get('name'):
                try:
                    # Auto-link to the pre-configured 'Students Receivable' account from our module
                    account = self.env.ref('rehab_management.rehab_account_students_receivable', raise_if_not_found=False)
                    account_id = account.id if account else False
                    
                    if not account_id:
                        fallback = self.env['account.account'].search([('account_type', '=', 'asset_receivable')], limit=1)
                        account_id = fallback.id if fallback else False
                    
                    partner_vals = {
                        'name': vals.get('name'),
                        'customer_rank': 1,
                        'is_company': False,
                        'property_account_receivable_id': account_id,
                    }
                        
                    partner = self.env['res.partner'].create(partner_vals)
                    vals['partner_id'] = partner.id
                except Exception as e:
                    # Log the error but allow student creation if partner creation fails? 
                    # Actually, for a student, partner is usually required for billing.
                    # We'll re-raise as UserError to provide a clean message to the UI.
                    raise UserError(_("Could not create financial account for student: %s") % str(e))
        return super().create(vals_list)

    @api.depends('partner_id')
    def _compute_prepaid_balance(self):
        for record in self:
            if not record.partner_id:
                record.prepaid_balance = 0.0
                continue
            # Odoo 19 robust payment search
            payments = self.env['account.payment'].search([
                ('partner_id', '=', record.partner_id.id),
                ('state', '=', 'posted'),
                ('is_reconciled', '=', False)
            ])
            record.prepaid_balance = sum(payments.mapped('amount'))

    @api.depends('partner_id')
    def _compute_financial_totals(self):
        for record in self:
            if not record.partner_id:
                record.total_invoiced = 0.0
                record.total_paid = 0.0
                record.total_due = 0.0
                continue
            # Search for posted customer invoices
            invoices = self.env['account.move'].search([
                ('partner_id', '=', record.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ])
            record.total_invoiced = sum(invoices.mapped('amount_total'))
            record.total_due = sum(invoices.mapped('amount_residual'))
            record.total_paid = record.total_invoiced - record.total_due

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.partner_id.id), ('move_type', '=', 'out_invoice')],
            'context': {'default_partner_id': self.partner_id.id, 'default_move_type': 'out_invoice'},
        }

    def action_view_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id, 'default_payment_type': 'inbound'},
        }

    def action_register_advanced_payment(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Please ensure this student has a related Financial Account (Partner) set."))
        
        # Ensure the partner has a receivable account set
        if not self.partner_id.property_account_receivable_id:
            receivable_account = self.env.ref('rehab_management.rehab_account_students_receivable', raise_if_not_found=False)
            if receivable_account:
                self.partner_id.sudo().property_account_receivable_id = receivable_account.id
            else:
                # Fallback to any receivable account if ours isn't found
                fallback = self.env['account.account'].search([('account_type', '=', 'asset_receivable')], limit=1)
                self.partner_id.sudo().property_account_receivable_id = fallback.id

        return {
            'name': 'Register Advanced Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_is_advance': True,  # Using the new Advance Payment feature
            },
        }
    def action_print_statement(self):
        self.ensure_one()
        return self.env.ref('rehab_management.action_report_student_statement').report_action(self)
