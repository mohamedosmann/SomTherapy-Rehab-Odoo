
import sys
import os
server_path = r'C:\Program Files\Odoo 19.0.20260308\server'
sys.path.append(server_path)
import odoo
from odoo.tools.config import config
config.parse_config(['-c', 'my_odoo.conf', '-d', 'rehab-db'])
try:
    from odoo.modules.registry import Registry
    registry = Registry(config['db_name'])
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        account_obj = env['account.account']
        selection = account_obj._fields['account_type'].selection(env)
        print("ACCOUNT_TYPES_START")
        for key, val in selection:
            print(f"{key}|{val}")
        print("ACCOUNT_TYPES_END")
except Exception as e:
    import traceback
    traceback.print_exc()
