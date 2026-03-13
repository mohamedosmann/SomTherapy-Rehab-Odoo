from odoo import models, fields, api

class RehabRoom(models.Model):
    _name = 'rehab.room'
    _description = 'Dormitory Room'

    name = fields.Char(string='Room Name', required=True)
    capacity = fields.Integer(string='Capacity', default=2)
    type = fields.Selection([
        ('Normal', 'Normal'),
        ('VIP', 'VIP')
    ], string='Type', default='Normal')
    extra_charge = fields.Float(string='Extra Charge', default=0.0)
    is_archived = fields.Boolean(string='Archived', default=False)
    student_ids = fields.One2many('rehab.student', 'room_id', string='Students')

class RehabClass(models.Model):
    _name = 'rehab.class'
    _description = 'Class'

    name = fields.Char(string='Class Name', required=True)
    schedule = fields.Char(string='Schedule')
    is_archived = fields.Boolean(string='Archived', default=False)
    teacher_id = fields.Many2one('rehab.staff', string='Staff/Teacher')
    student_ids = fields.One2many('rehab.student', 'class_id', string='Students')
