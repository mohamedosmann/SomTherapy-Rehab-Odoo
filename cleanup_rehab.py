import logging

def run(env):
    # 1. Check for stale 'type' field in ir.model.fields
    f = env['ir.model.fields'].search([('model', '=', 'rehab.student'), ('name', '=', 'type')])
    if f:
        logging.info(f"Found stale field 'type' on 'rehab.student'. Deleting it.")
        f.unlink()
    
    # 2. Clear user-customized views and filters that might reference 'type'
    filters = env['ir.filters'].search([('model_id', '=', 'rehab.student')])
    if filters:
        logging.info(f"Deleting {len(filters)} potential stale filters for rehab.student.")
        filters.unlink()
    
    custom_views = env['ir.ui.view.custom'].search([('ref_id.model', '=', 'rehab.student')])
    if custom_views:
        logging.info(f"Deleting {len(custom_views)} customized views for rehab.student.")
        custom_views.unlink()

    # 3. Force recompute of monthly fee just in case
    students = env['rehab.student'].search([])
    students._compute_monthly_fee()
    
    env.cr.commit()
    logging.info("Cleanup successful.")

if __name__ == '__main__':
    pass
