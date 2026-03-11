import os
from lxml import etree

schema_path = r'C:\Program Files\Odoo 19.0.20260309\server\odoo\import_xml.rng'
xml_path = r'c:\Users\yuusuf\.gemini\antigravity\scratch\rehab-odoo\rehab_management\views\menus.xml'

schema_doc = etree.parse(schema_path)
relaxng = etree.RelaxNG(schema_doc)

with open(xml_path, 'r', encoding='utf-8') as f:
    xml_content = f.read()

# Full validation
print("Attempting full validation...")
try:
    doc = etree.fromstring(xml_content.encode('utf-8'))
    relaxng.assert_(doc)
    print("Full validation SUCCESSFUL")
except Exception as e:
    print(f"Full validation FAILED: {e}")

# Granular validation
print("\nAttempting granular validation...")
root = etree.fromstring(xml_content.encode('utf-8'))
for i, child in enumerate(root):
    # Create a dummy root for each child
    test_root = etree.Element("odoo")
    test_root.append(child)
    try:
        relaxng.assert_(test_root)
        # print(f"Child {i} ({child.tag} id={child.get('id')}): SUCCESS")
    except Exception as e:
        print(f"Child {i} ({child.tag} id={child.get('id')}) FAILED: {e}")
        # Print the child content to see what's wrong
        print(etree.tostring(child, encoding='unicode'))
