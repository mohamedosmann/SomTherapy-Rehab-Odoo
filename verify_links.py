
# Verify Links
for xml_id in ['journal_cash_payments', 'journal_bank_payments', 'journal_student_invoices', 'journal_staff_expenses']:
    data = env['ir.model.data'].search([('module', '=', 'rehab_management'), ('name', '=', xml_id)])
    if data:
        print(f"XML_ID {xml_id} is linked to {data.model} ID {data.res_id}")
    else:
        print(f"XML_ID {xml_id} is NOT linked")

# Check Journals
for code in ['INV', 'CASH', 'BNK', 'STF']:
    j = env['account.journal'].search([('code', '=', code)])
    if j:
        print(f"Journal with code {code} exists: ID {j.id}, Name {j.name}")
    else:
        print(f"Journal with code {code} does NOT exist")

# Force Link if missing but journal exists
def force_link(xml_id, model, search_domain):
    j = env[model].search(search_domain)
    if j:
        data = env['ir.model.data'].search([('module', '=', 'rehab_management'), ('name', '=', xml_id)])
        if not data:
            env['ir.model.data'].create({
                'module': 'rehab_management',
                'name': xml_id,
                'model': model,
                'res_id': j[0].id,
                'noupdate': True,
            })
            print(f"FORCE LINKED {xml_id} to {j[0].id}")
        else:
            if data.res_id != j[0].id:
                print(f"WARNING: {xml_id} linked to {data.res_id} but found match with {j[0].id}")

force_link('journal_student_invoices', 'account.journal', [('code', '=', 'INV')])
# Note: CASH and BNK don't exist yet, so they will be created. 
# But maybe there are other journals with different codes we should link to?
# No, let's stick to linking INV which is the one causing the clash.

env.cr.commit()
