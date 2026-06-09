{
    "name": "Task Vehicles Link",
    "version": "1.0",
    "category": "Field Service",
    "summary": "Link Vehicles with Field Service Tasks",
    "depends": ["project", "industry_fsm","vehicle_data_management"],
    "data":[
        "security/ir.model.access.csv",
        "views/project_task_view.xml",
        "views/wizard_internal.xml",
    ],
    "installable": True,
    "application": True
}