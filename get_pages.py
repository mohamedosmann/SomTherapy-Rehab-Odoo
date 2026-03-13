from odoo import api
view = env.ref('account.view_account_journal_form')
print("Pages:")
for node in view.arch_db.split('<page'):
    if 'name="' in node:
        name = node.split('name="')[1].split('"')[0]
        string = node.split('string="')[1].split('"')[0] if 'string="' in node else 'N/A'
        print(f"- {name} ({string})")
