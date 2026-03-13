
def find_action(name_part):
    actions = env['ir.actions.act_window'].search([('name', 'ilike', name_part)])
    for a in actions:
        # get xml_id
        xml_ids = env['ir.model.data'].search([('model', '=', 'ir.actions.act_window'), ('res_id', '=', a.id)])
        for x in xml_ids:
            print(f"Action: {a.name}, XML_ID: {x.module}.{x.name}")

find_action('Inventory')
find_action('Stock')
find_action('Quant')
