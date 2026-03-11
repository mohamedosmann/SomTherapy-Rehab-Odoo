{
    'name': 'Rehab Management',
    'version': '1.0',
    'summary': 'Odoo customization for Rehab and Dormitory Management',
    'description': """
        Customization for Rehab and Dormitory Management, 
        mirroring features from Somtherapy system.
    """,
    'author': 'Antigravity',
    'depends': ['base', 'mail', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/rehab_billing_wizard_views.xml',
        'views/menus.xml',
        'views/rehab_student_views.xml',
        'views/rehab_discipline_views.xml',
        'views/rehab_dormitory_views.xml',
    ],
    'installable': True,
    'application': True,
}
