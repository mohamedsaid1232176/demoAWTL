{
    'name': 'ARKA Purchase Mostakhlas',
    'version': '18.0.1.0.0',
    'summary': 'Add Mostakhlas tab and button for ARKA company only',
    'category': 'Purchases',
    'author': 'Mohamed said',
    'depends': ['purchase', 'arka_mostakhlas'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_view.xml',
        'views/account_move_mostakhlas_views.xml',
        'views/mostakhlas_mune.xml',
        'reports/report.xml',
        'views/button_print.xml',
        'wizards/wizard_print_mostkhlas.xml',
    ],

    'installable': True,
    'application': True,
}
