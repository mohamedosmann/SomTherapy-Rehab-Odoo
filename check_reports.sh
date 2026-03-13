sudo -u odoo psql -d Rehab-prod -c "SELECT id, name FROM ir_ui_menu WHERE name LIKE '%IFRS%';"
sudo -u odoo psql -d Rehab-prod -c "SELECT id, name FROM ir_act_window WHERE res_model = 'rehab.financial.report.wizard';"
