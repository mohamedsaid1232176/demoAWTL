{
    "name": "Warehouse Sales Journal",
    "version": "1.0",
    "category": "Inventory",
    "depends": ["stock", "account","sale"],
    "data": [
        "views/warehouse_view.xml",
        "views/replace_fields.xml",
    ],
    "installable": True,
    "application": True
}