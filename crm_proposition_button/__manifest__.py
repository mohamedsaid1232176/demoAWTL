{
    "name": "CRM Proposition Button ARKA Only",
    "version": "18.0",
    "installable": True,
    "application": True,
    "depends": ["crm"],
    'assets': {
        'web.assets_backend': [
            'crm_proposition_button/static/src/css/css.css',
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/crm_lead_views.xml",
        "views/show_project_button.xml",
        "wizards/assign_user.xml",
    ]
}
