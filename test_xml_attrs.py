import os
from lxml import etree

schema_path = r'C:\Program Files\Odoo 19.0.20260309\server\odoo\import_xml.rng'

def test_xml(content):
    xml_content = f'<?xml version="1.0" encoding="utf-8"?><odoo>{content}</odoo>'
    with open('test_attrs.xml', 'w', encoding='utf-8') as f:
        f.write(xml_content)
    try:
        schema_doc = etree.parse(schema_path)
        relaxng = etree.RelaxNG(schema_doc)
        xml_doc = etree.parse('test_attrs.xml')
        relaxng.assert_(xml_doc)
        print("Validation: SUCCESS")
    except Exception as e:
        print(f"Validation: FAILED - {e}")

print("Testing menuitem with parent:")
test_xml('<menuitem id="m1" name="root"/><menuitem id="m2" name="child" parent="m1"/>')

print("Testing menuitem with action:")
test_xml('<record id="a1" model="ir.actions.act_window"><field name="name">Test</field></record><menuitem id="m1" name="root" action="a1"/>')

print("Testing menuitem with parent AND action:")
test_xml('<record id="a1" model="ir.actions.act_window"><field name="name">Test</field></record><menuitem id="m1" name="root"/><menuitem id="m2" parent="m1" action="a1"/>')
