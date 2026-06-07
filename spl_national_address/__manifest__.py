{
    'name': 'SPL National Address Integration',
    'version': '18.0.1.0.0',
    'summary': 'Validate and fetch Saudi National Address data from SPL.',
    'author': 'AWTL',
    'license': 'LGPL-3',
    'depends': ['base', 'contacts'],
    'data': [
        'views/menu_views.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
}
