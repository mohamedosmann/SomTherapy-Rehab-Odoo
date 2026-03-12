from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RehabDisciplineCase(models.Model):
    _name = 'rehab.discipline.case'
    _description = 'Discipline Case'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    student_id = fields.Many2one('rehab.student', string='Student', required=True, ondelete='cascade', tracking=True)
    partner_id = fields.Many2one('res.partner', related='student_id.partner_id', string='Financial Partner', store=True)
    violation = fields.Char(string='Violation', required=True)
    priority = fields.Selection([
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low')
    ], string='Priority', default='Medium', tracking=True)
    status = fields.Selection([
        ('Under Review', 'Under Review'),
        ('Payment Pending', 'Payment Pending'),
        ('In Rehabilitation', 'In Rehabilitation'),
        ('Completed', 'Completed'),
        ('Cleared', 'Cleared')
    ], string='Status', default='Under Review', tracking=True)
    date_reported = fields.Datetime(string='Date Reported', default=fields.Datetime.now)
    notes = fields.Text(string='Notes')
    fine_amount = fields.Float(string='Fine Amount (USD)')
    
    invoice_id = fields.Many2one('account.move', string='Related Invoice', readonly=True)
    payment_status = fields.Selection(related='invoice_id.payment_state', string='Payment Status')

    session_ids = fields.One2many('rehab.session', 'case_id', string='Sessions')
    log_ids = fields.One2many('rehab.progress.log', 'case_id', string='Progress Logs')

    def action_generate_fine_invoice(self):
        self.ensure_one()
        if not self.fine_amount or self.fine_amount <= 0:
            raise UserError(_("Please set a fine amount before generating an invoice."))
        if self.invoice_id:
            raise UserError(_("An invoice already exists for this case."))
        if not self.student_id.partner_id:
            raise UserError(_("Student has no financial account (partner). Please create one first."))
            
        try:
            # Standard Odoo 19 Invoice Creation
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': self.student_id.partner_id.id,
                'invoice_origin': f"Discipline Case: {self.violation}",
                'invoice_line_ids': [(0, 0, {
                    'name': _("Disciplinary Fine: %s") % self.violation,
                    'quantity': 1.0,
                    'price_unit': self.fine_amount,
                })],
            }
            invoice = self.env['account.move'].create(invoice_vals)
            self.invoice_id = invoice.id
            self.status = 'Payment Pending'
            return {
                'name': _('Invoice'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'type': 'ir.actions.act_window',
            }
        except Exception as e:
            raise UserError(_("Failed to generate invoice: %s") % str(e))

class RehabSession(models.Model):
    _name = 'rehab.session'
    _description = 'Rehabilitation Session'

    case_id = fields.Many2one('rehab.discipline.case', string='Discipline Case', required=True, ondelete='cascade')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    session_type = fields.Selection([
        ('Counseling', 'Counseling'),
        ('Community Service', 'Community Service'),
        ('Ethics Training', 'Ethics Training')
    ], string='Session Type')
    notes = fields.Text(string='Notes')

class RehabProgressLog(models.Model):
    _name = 'rehab.progress.log'
    _description = 'Progress Log'

    case_id = fields.Many2one('rehab.discipline.case', string='Discipline Case', required=True, ondelete='cascade')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    note = fields.Text(string='Note', required=True)
    behavior_score = fields.Integer(string='Behavior Score (0-100)')
