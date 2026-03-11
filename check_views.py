import json
views = env['ir.ui.view'].search([('model', '=', 'rehab.student')])
found = False
for v in views:
    if '"type"' in v.arch_db or "'type'" in v.arch_db:
        print(f"====== FOUND IN VIEW: {v.name} (ID: {v.id}) ======")
        print(v.arch_db)
        found = True

filters = env['ir.filters'].search([('model_id', '=', 'rehab.student')])
for f in filters:
    if 'type' in f.domain or 'type' in f.context:
        print(f"====== FOUND IN FILTER: {f.name} ======")
        found = True

if not found:
    print("====== NOT FOUND IN ANY REHAB.STUDENT VIEW OR FILTER ======")
