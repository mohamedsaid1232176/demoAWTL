from odoo import models, fields


class ProjectSummary(models.Model):
    _name = "project.summary"
    _description = "Projects Summary"
    _auto = False
    _rec_name = "project_id"
    project_name = fields.Char(string="Project Name")

    project_id = fields.Many2one("crm.lead", string="Project")
    total_project_cost = fields.Float(string="Total Project Cost")
    total_unit_price_project = fields.Float(string="Total Project Unit Price")

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS project_summary CASCADE;")
        self.env.cr.execute("""
            CREATE VIEW project_summary AS (
                SELECT
                    cl.id AS id,
                    cl.id AS project_id,
                    cl.name AS project_name,  -- <<< اسم المشروع
                    COALESCE(SUM(mg.total_cost), 0) AS total_project_cost,
                    COALESCE(SUM(
                        (mg.total_goods_unit_price) +
                        (mg.total_service_unit_price)
                    ), 0) AS total_unit_price_project
                FROM crm_lead cl
                LEFT JOIN crm_milestone_group mg
                    ON mg.lead_id = cl.id
                WHERE cl.type = 'opportunity'
                GROUP BY cl.id
            );
        """)


