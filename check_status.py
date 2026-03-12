
import sys
import os
server_path = r'C:\Program Files\Odoo 19.0.20260308\server'
sys.path.append(server_path)
import odoo
from odoo.tools.config import config
config.parse_config(['-c', 'my_odoo.conf', '-d', 'rehab-db'])
try:
    from odoo.modules.registry import Registry
    db_name = config['db_name']
    if isinstance(db_name, list):
        db_name = db_name[0]
    registry = Registry(db_name)
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        student_model = env['ir.model'].search([('model', '=', 'rehab.student')])
        print(f"CHECK_START")
        print(f"Database: {config['db_name']}")
        print(f"Model rehab.student found: {bool(student_model)}")
        module = env['ir.module.module'].search([('name', '=', 'rehab_management')])
        print(f"Module rehab_management state: {module.state if module else 'Not Found'}")
        
        # Check all available databases
        from odoo.service import db
        print(f"Available Databases: {db.list_dbs()}")
        print(f"CHECK_END")
except Exception as e:
    import traceback
    traceback.print_exc()
