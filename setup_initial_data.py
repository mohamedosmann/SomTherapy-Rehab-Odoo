import os
import sys

# Setup Odoo path
odoo_path = r"C:\Program Files\Odoo 19.0.20260308\server"
sys.path.append(odoo_path)

import odoo
from odoo import api, SUPERUSER_ID

# Config
db_name = 'rehab-db'
config_file = r"c:\Users\PC\.gemini\antigravity\scratch\som-rehab-odoo\my_odoo.conf"
odoo.tools.config.parse_config(['-c', config_file])

with odoo.api.Environment.manage():
    with odoo.registry(db_name).cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # 1. Setup Student Types
        types = ['Normal', 'VIP', 'Scholarship']
        for t_name in types:
            if not env['rehab.student.type'].search([('name', '=', t_name)]):
                env['rehab.student.type'].create({'name': t_name})
                print(f"Created Student Type: {t_name}")

        # 2. Setup a Sample Teacher
        if not env['rehab.teacher'].search([('teacher_id', '=', 'TEA-001')]):
            env['rehab.teacher'].create({
                'name': 'Dr. Ahmed Ali',
                'teacher_id': 'TEA-001',
                'specialization': 'Psychotherapy',
                'department': 'Counseling'
            })
            print("Created Sample Teacher: Dr. Ahmed Ali")

        cr.commit()
