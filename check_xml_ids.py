
def check_xml_id(xml_id):
    try:
        res = env.ref(xml_id)
        print(f"XML_ID {xml_id} is VALID: {res._name} ID {res.id}")
    except Exception as e:
        print(f"XML_ID {xml_id} is INVALID: {str(e)}")

# Logistics
check_xml_id('stock.stock_picking_type_action')
check_xml_id('stock.stock_move_line_action')
check_xml_id('stock.stock_quant_action')
check_xml_id('purchase.purchase_rfq')
check_xml_id('purchase.purchase_form_action')

# Financials
check_xml_id('account.action_move_out_invoice_type')
check_xml_id('account.action_move_in_invoice_type')
check_xml_id('account.action_account_payments')
check_xml_id('account.action_account_payments_payable')
check_xml_id('account.action_account_journal_form')
check_xml_id('account.action_account_form')
check_xml_id('account.action_account_invoice_report_all')
check_xml_id('account.action_account_moves_all')
