{
    'name': 'Rehab Management',
    'version': '1.0',
    'summary': 'Odoo customization for Rehab and Dormitory Management',
    'description': """
        Customization for Rehab and Dormitory Management, 
        mirroring features from Somtherapy system.
    """,
    'author': 'Antigravity',
    'depends': ['base', 'mail', 'account', 'stock', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/account.account.csv',
        'data/account.journal.csv',
        'wizard/rehab_billing_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'views/menus.xml',
        'views/rehab_student_views.xml',
        'views/rehab_discipline_views.xml',
        'views/rehab_dormitory_views.xml',
        'views/rehab_teacher_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': True,
}
