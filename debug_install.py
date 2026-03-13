import odoo
from odoo import api, SUPERUSER_ID

def install_module(db_name):
    print(f"Attempting to install rehab_management on {db_name}")
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        module = env['ir.module.module'].search([('name', '=', 'rehab_management')])
        if not module:
            print("Module rehab_management not found")
            return
        try:
            module.button_immediate_install()
            print("Successfully installed")
        except Exception as e:
            import traceback
            print("Installation failed:")
            print(traceback.format_exc())

if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else 'test_install_4'
    install_module(db)
