## -*- coding: utf-8 -*-
{
    "name": "CRM Milestone Flow (ARKA Only)",
    "version": "18.0.1.0.0",
    "author": "Mohamed said",
    "license": "LGPL-3",
    "category": "Sales",
    "depends": [
        "base",
        "product",
        "crm",
        "sale",  # ← مهم جداً
        "sale_management",  # ← مهم لو هتورّث sale.order.form
        "product_milestone_odoo18",
        "crm_proposition_button",
        "crm_project_link",
        "account_budget",
    ],

    "data": [
        "security/ir.model.access.csv",
        "views/crm_lead_views.xml",
        "views/crm_lead_milestone_button.xml",
        "views/inheri_sale_order.xml",
        "views/add_field_remaining_days_crm.xml",
        "views/debit_credit_change.xml",
        "views/stock_warehouse_view_checkbox.xml",
        "data/cron.xml",
        "wizard/goods_wizard_views.xml",
        "wizard/wizards_button.xml",
        "wizard/services_wizard_views.xml"
    ],
    "installable": True,
    "application": True,
    'assets': {
        'web.assets_backend': [
            'crm_milestone_flow_full/static/src/css/milestone_groups.css',
        ],
    },

}
