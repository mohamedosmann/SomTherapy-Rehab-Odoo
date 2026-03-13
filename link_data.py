
def link_record(model, xml_id, search_domain):
    record = env[model].search(search_domain, limit=1)
    if record:
        # Check if xml_id already exists
        existing_data = env['ir.model.data'].search([
            ('module', '=', 'rehab_management'),
            ('name', '=', xml_id)
        ])
        if not existing_data:
            env['ir.model.data'].create({
                'module': 'rehab_management',
                'name': xml_id,
                'model': model,
                'res_id': record.id,
                'noupdate': True,
            })
            print(f"Linked {xml_id} to {model}({record.id})")
        else:
            print(f"{xml_id} already linked")

# Link Accounts
link_record('account.account', 'account_students_receivable', [('code', '=', '101200')])
link_record('account.account', 'account_staff_payable', [('code', '=', '201200')])
link_record('account.account', 'account_cash_on_hand', [('code', '=', '101100')])
link_record('account.account', 'account_bank_account', [('code', '=', '101400')])
link_record('account.account', 'account_student_fees', [('code', '=', '401100')])
link_record('account.account', 'account_staff_salaries', [('code', '=', '601100')])
link_record('account.account', 'account_dormitory_expenses', [('code', '=', '601300')])
link_record('account.account', 'account_supplies', [('code', '=', '601400')])

# Link Journals
link_record('account.journal', 'journal_cash_payments', [('code', '=', 'CASH')])
link_record('account.journal', 'journal_bank_payments', [('code', '=', 'BNK')])
link_record('account.journal', 'journal_evc_payments', [('code', '=', 'EVC')])
link_record('account.journal', 'journal_salaam_payments', [('code', '=', 'SLM')])
link_record('account.journal', 'journal_student_invoices', [('code', '=', 'INV')])
link_record('account.journal', 'journal_staff_expenses', [('code', '=', 'STF')])

env.cr.commit()
