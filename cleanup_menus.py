from odoo import models, api

def cleanup_menus():
    # Delete old teacher related menus that were renamed
    teacher_menus = env['ir.ui.menu'].search([('name', 'ilike', 'teacher')])
    for m in teacher_menus:
        print(f"Deleting menu: {m.complete_name}")
        m.unlink()
    
    # Also action names
    teacher_actions = env['ir.actions.act_window'].search([('name', 'ilike', 'teacher')])
    for a in teacher_actions:
        print(f"Renaming action: {a.name} -> {a.name.replace('Teacher', 'Staff')}")
        a.name = a.name.replace('Teacher', 'Staff')
        a.name = a.name.replace('teacher', 'staff')

cleanup_menus()
env.cr.commit()
