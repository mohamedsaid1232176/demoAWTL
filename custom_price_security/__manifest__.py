{
    'name': 'Custom Unit Price Permissions',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Make Unit Price readonly for users except Administrator',
    'depends': ['sale'],
    'data': [
        'security/groups.xml',
        'views/sale_order_view.xml',
        'views/res_partner_view.xml',
        'views/add_related_field_tag.xml',
        'views/sale_order_line_wizard_form.xml',
        'views/report_merge.xml',

    ],

    'installable': True,
    'application': True,
}
