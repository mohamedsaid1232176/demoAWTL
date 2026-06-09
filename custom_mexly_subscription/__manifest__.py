{
    'name': 'Mexly Subscription',
    'version': '18.0',
    'description': 'apply some changes to subscription module',
    'summary': 'apply some changes to subscription module',
    'author': 'Fayrouz',
    'license': 'LGPL-3',
    'category': '',
    'depends': ['sale','sale_subscription','account_followup'],

    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/account_move.xml',
        'views/product_template.xml',
        'views/analytic_account.xml',
        'views/res_company.xml',
        'views/subscription_state.xml',
        'views/sale_subscription_plan.xml',
        # 🔥 مهم جدًا
        'views/report_dashboard.xml',

        # 🔥 بعده dashboard
        'views/contract_type.xml',
        'views/organization_type.xml',
        'views/property_type.xml',
        'views/broker_entity.xml',
        'views/title_deed_type.xml',
        'views/dashboard.xml',
        'report/report.xml',
        'data/subscription_state_data.xml',
        'wizard/one_product_wizard.xml',
        'wizard/multi_product_wizard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_mexly_subscription/static/src/css/dashboard.css',
        ],
    },
    'installable': True,
    'application': True,
}