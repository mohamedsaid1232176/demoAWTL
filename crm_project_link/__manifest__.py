## -*- coding: utf-8 -*-
{
    'name': "Arka CRM Project Link",
    'summary': "Link CRM opportunities to Projects and populate project managers",
    'version': "18.0.1.0.0",
    'author': "Mohamed saud",
    'license': "LGPL-3",
    'category': "Sales",
    'depends': ["crm", "project","sale"],
    'data': [
        "security/ir.model.access.csv",
        "views/crm_lead_views.xml",
        "views/menu_models.xml",
        "wizards/lead_won_confirm_wizard.xml",
    ],
    'installable': True,
    'application': True,

}
