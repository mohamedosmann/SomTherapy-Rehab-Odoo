sudo -u odoo psql -d rehab-prod -c "SELECT name FROM ir_module_module WHERE state = 'installed' AND name LIKE 'account%'"
