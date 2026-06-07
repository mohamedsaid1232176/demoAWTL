# -*- coding: utf-8 -*-
{
    'name': 'Arka Sale Mostakhlas',
    'version': '18.0.1.0.0',
    'category': 'Construction',
    'summary': 'إدارة المستخلصات لأوامر البيع مع دفعات العملاء',
    'author': 'Arka',
    'depends': [
        'sale_management',
        'account',
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/mostakhlas_type_views.xml',
        'views/sale_mostakhlas_views.xml',
        'views/account_move_mostakhlas_views.xml',
        'views/sale_wizard_views.xml',
        'views/sale_mostakhlas_add_line_wizard_views.xml',
        'report/sale_mostakhlas_report.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
