{
    "name": "CRM Disable Quick Create",
    "version": "1.0",
    "depends": ["crm","web"],
    "assets": {
        "web.assets_backend": [
            "crm_no_quick_create_full/static/src/js/disable_quick_create.js"
        ]
    },
    "data": [
        "views/crm_limit_create.xml"
    ],
    "installable": True,
    "application": True,
}
