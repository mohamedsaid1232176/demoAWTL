# mexly_crm_project_link

This module adds two fields to CRM leads:
- project_id (Many2one to project.project)
- project_manager_ids (Many2many to res.users)

When a project is selected, the project's user_id is copied to project_manager_ids (onchange).
