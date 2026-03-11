import os
from lxml import etree

schema_path = r'C:\Program Files\Odoo 19.0.20260309\server\odoo\import_xml.rng'

def test_xml(root_tag):
    xml_content = f'<?xml version="1.0" encoding="utf-8"?><{root_tag}><menuitem id="test" name="test"/></{root_tag}>'
    with open('test_alt_root.xml', 'w', encoding='utf-8') as f:
        f.write(xml_content)
    try:
        schema_doc = etree.parse(schema_path)
        relaxng = etree.RelaxNG(schema_doc)
        xml_doc = etree.parse('test_alt_root.xml')
        relaxng.assert_(xml_doc)
        print(f"Root <{root_tag}>: SUCCESS")
    except Exception as e:
        print(f"Root <{root_tag}>: FAILED - {e}")

test_xml('odoo')
test_xml('data')
test_xml('openerp')
