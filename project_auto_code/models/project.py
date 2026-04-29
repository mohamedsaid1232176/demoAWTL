from odoo import models, fields, api

# env['project.project'].action_generate_code_for_existing_projects()


class ProjectProject(models.Model):
    _inherit = 'project.project'

    code = fields.Char(
        string="Project Code",
        readonly=True,
        copy=False,
        index=True
    )

    _sql_constraints = [
        ('unique_project_code', 'unique(code)', 'Project Code must be unique!')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('project.project.code')
        return super(ProjectProject, self).create(vals)

    def action_generate_code_for_existing_projects(self):
        projects = self.search([('code', '=', False)])
        for project in projects:
            project.code = self.env['ir.sequence'].next_by_code('project.project.code')
