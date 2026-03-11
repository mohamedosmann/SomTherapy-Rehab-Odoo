import os
from lxml import etree

schema_path = r'C:\Program Files\Odoo 19.0.20260309\server\odoo\import_xml.rng'
with open(r'c:\Users\yuusuf\.gemini\antigravity\scratch\rehab-odoo\rehab_management\views\menus.xml', 'r', encoding='utf-8') as f:
    xml_content = f.read()

with open('test_menus_exact.xml', 'w', encoding='utf-8') as f:
    f.write(xml_content)

try:
    schema_doc = etree.parse(schema_path)
    relaxng = etree.RelaxNG(schema_doc)
    
    xml_doc = etree.parse('test_menus_exact.xml')
    relaxng.assert_(xml_doc)
    print("Validation SUCCESSFUL")
except etree.RelaxNGError as e:
    print(f"Validation FAILED: {e}")
    for error in relaxng.error_log:
        print(f"Error: {error.message} at line {error.line}")
except AssertionError as e:
    print(f"AssertionError: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
