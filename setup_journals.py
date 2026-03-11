company = self.env.company
journals = self.env['account.journal'].search([('company_id', '=', company.id)])
types = set(journals.mapped('type'))
print('Current journal types:', types)

if 'sale' not in types:
    self.env['account.journal'].create({'name': 'Customer Invoices', 'type': 'sale', 'code': 'INV', 'company_id': company.id})
    print('Created: Customer Invoices (sale)')

if 'purchase' not in types:
    self.env['account.journal'].create({'name': 'Vendor Bills', 'type': 'purchase', 'code': 'BILL', 'company_id': company.id})
    print('Created: Vendor Bills (purchase)')

if 'bank' not in types:
    self.env['account.journal'].create({'name': 'Bank', 'type': 'bank', 'code': 'BNK', 'company_id': company.id})
    print('Created: Bank')

if 'cash' not in types:
    self.env['account.journal'].create({'name': 'Cash', 'type': 'cash', 'code': 'CSH', 'company_id': company.id})
    print('Created: Cash')

self.env.cr.commit()
print('Done - all journals created!')
