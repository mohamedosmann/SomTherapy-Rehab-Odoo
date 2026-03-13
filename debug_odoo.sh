sudo -u odoo psql -d rehab-prod -c "SELECT name, model, res_id FROM ir_model_data WHERE module = 'rehab_management'"
sudo -u odoo psql -d rehab-prod -c "SELECT id, name, code FROM account_journal"
sudo -u odoo psql -d rehab-prod -c "SELECT id, name, code FROM account_account"
