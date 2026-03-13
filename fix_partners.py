import logging
from odoo import api, fields, models, SUPERUSER_ID

_logger = logging.getLogger(__name__)

def fix_partners(env):
    # Fix Students
    students = env['rehab.student'].search([])
    receivable_account = env.ref('rehab_management.account_students_receivable', raise_if_not_found=False)
    if not receivable_account:
        _logger.warning("Students receivable account NOT found. Falling back to company default.")
        receivable_account = env.company.property_account_receivable_id

    for student in students:
        if student.partner_id and not student.partner_id.property_account_receivable_id:
            _logger.info(f"Fixing receivable account for student partner: {student.partner_id.name}")
            student.partner_id.property_account_receivable_id = receivable_account.id

    # Fix Teachers
    teachers = env['rehab.teacher'].search([])
    payable_account = env.ref('rehab_management.account_staff_payable', raise_if_not_found=False)
    if not payable_account:
        _logger.warning("Staff payable account NOT found. Falling back to company default.")
        payable_account = env.company.property_account_payable_id

    for teacher in teachers:
        if teacher.partner_id and not teacher.partner_id.property_account_payable_id:
            _logger.info(f"Fixing payable account for teacher partner: {teacher.partner_id.name}")
            teacher.partner_id.property_account_payable_id = payable_account.id

    env.cr.commit()
    _logger.info("Partner account fix completed.")

if __name__ == "__main__":
    if 'env' in globals():
        fix_partners(globals()['env'])
    else:
        print("This script must be run within the Odoo shell environment.")
