{
    "name": "Warehouse Restriction",
    "version": "1.0",
    "summary": "User-based warehouse access restriction",
    "depends": ["stock", "stock_account"],
    "data": [
        "security/ir.model.access.csv",
        "security/warehouse_rules.xml",
        "views/res_users_views.xml",
        "views/f.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "warehouse_restriction/static/src/xml/s.xml",
        ],
    },

    "installable": True,
    "application": True
}
