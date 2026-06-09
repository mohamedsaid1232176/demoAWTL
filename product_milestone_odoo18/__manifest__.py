{
    'name': 'Product Milestone',
    'version': '18.0.1.0.0',
    'summary': 'Add Milestone product type + link products to milestones (Company ARKA only)',
    'description': 'Adds a new product type milestone and restricts milestones to ARKA company only.',
    'category': 'Productivity',
    'author': 'Mohamed said',
    'license': 'LGPL-3',
    'depends': ['product'],
    'data': [
        'data/product_milestone_data.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': True,
}
