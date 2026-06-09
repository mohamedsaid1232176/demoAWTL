{
    'name': 'Contact & Sales Security',
    'version': '1.0',
    'summary': 'Contacts access + sales approval control with user tabs',
    'depends': ['base', 'sale', 'contacts'],
    'data': [
        'security/security.xml',
        'security/ir_rule.xml',
        'views/res_users_view.xml',
    ],
    'application': True,
    'installable': True,
}
