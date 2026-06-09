{
    'name': 'Technician Management',
    'version': '1.0',
    'depends': ['sale', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/technician_views.xml',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': True,
}