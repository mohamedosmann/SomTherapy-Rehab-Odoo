import os
from lxml import etree

schema_path = r'C:\Program Files\Odoo 19.0.20260309\server\odoo\import_xml.rng'

def test_xml(content):
    xml_content = f'<?xml version="1.0" encoding="utf-8"?><odoo>{content}</odoo>'
    with open('test_scaling.xml', 'w', encoding='utf-8') as f:
        f.write(xml_content)
    try:
        schema_doc = etree.parse(schema_path)
        relaxng = etree.RelaxNG(schema_doc)
        xml_doc = etree.parse('test_scaling.xml')
        relaxng.assert_(xml_doc)
        print("Validation: SUCCESS")
    except Exception as e:
        print(f"Validation: FAILED - {e}")

print("Testing two menuitems:")
test_xml('<menuitem id="m1" name="n1"/><menuitem id="m2" name="n2"/>')

print("Testing menuitem + record:")
test_xml('<menuitem id="m1" name="n1"/><record id="r1" model="res.partner"><field name="name">Test</field></record>')
