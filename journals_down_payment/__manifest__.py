{
    'name': 'Journal Down Payment',
    'version': '1.1',
    "version": "18.0.1.0.0",
    "author": "Mohamed Said",
    'category': 'Accounting',
    'summary': 'Add Down Payment boolean field to Journals with unique constraint and integrate with Sales Down Payment invoices',
    'description': 'This module adds a Down Payment field to Account Journals, ensures only one journal can have it enabled, and uses it automatically for Down Payment invoices.',
    'depends': ['account', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_journal_views.xml',
    ],
    'qweb': [
        'views/qwep.xml',
    ],
    'assets': {
        "web.assets_backend": [
            'journals_down_payment/static/src/js/qw.js',
            'journals_down_payment/static/src/js/qw2.js',
        ],
    },
    'installable': True,
    'application': True,
}
