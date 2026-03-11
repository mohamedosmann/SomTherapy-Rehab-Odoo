import logging
from odoo import api, SUPERUSER_ID

def run(env):
    Type = env['rehab.student.type']
    types = ['Normal', 'VIP']
    for t in types:
        if not Type.search([('name', '=', t)]):
            Type.create({'name': t})
            logging.info(f"Created student type: {t}")
    env.cr.commit()

if __name__ == '__main__':
    # Called by Odoo shell
    pass
