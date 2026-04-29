{
    'name': 'إدارة المشروعات',
    'version': '1.0',
    'summary': 'عرض المشروعات في مرحلة Proposition',
    'category': 'Project',
    'depends': ['crm',"sale_management","crm_milestone_flow_full"],
    'data': [
        'security/ir.model.access.csv',
        'views/project_management_views.xml',
        'views/sale_oerder.xml',
        'views/invisible_tabs.xml',
        'views/other_setting.xml',
    ],
    'installable': True,
    'application': True,
}
