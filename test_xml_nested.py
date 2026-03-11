import os
from lxml import etree

schema_path = r'C:\Program Files\Odoo 19.0.20260309\server\odoo\import_xml.rng'

def test_xml(root_content):
    xml_content = f'<?xml version="1.0" encoding="utf-8"?><odoo>{root_content}</odoo>'
    with open('test_nested.xml', 'w', encoding='utf-8') as f:
        f.write(xml_content)
    try:
        schema_doc = etree.parse(schema_path)
        relaxng = etree.RelaxNG(schema_doc)
        xml_doc = etree.parse('test_nested.xml')
        relaxng.assert_(xml_doc)
        print("Validation: SUCCESS")
    except Exception as e:
        print(f"Validation: FAILED - {e}")

print("Testing <odoo><data>:")
test_xml('<data><menuitem id="m1" name="n1"/></data>')

print("Testing <odoo> direct:")
test_xml('<menuitem id="m1" name="n1"/>')
