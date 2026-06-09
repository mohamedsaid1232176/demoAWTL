{
    "name": "Auto Assign Partner User",
    "version": "1.0",
    "summary": "Automatically assign current user to user_id when creating new contacts",
    "category": "Contacts",
    "author": "Fayrouz",
    "depends": ["base","sale","sales_team"],
    "data": [
        'security/security.xml',
        'views/crm_lead.xml',
        'views/res_partner.xml',

    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
