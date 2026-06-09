from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    equipment_count = fields.Integer(
        string="Equipments",
        compute="_compute_equipment_count"
    )

    def _compute_equipment_count(self):
        Vehicle = self.env["vehicledata"]
        for partner in self:
            partner.equipment_count = Vehicle.search_count([
                ("company_id", "=", partner.id)
            ])

    def action_open_partner_equipments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Equipments",
            "res_model": "vehicledata",
            "view_mode": "list,form",
            "domain": [("company_id", "=", self.id)],
            "context": {
                "default_company_id": self.id
            }
        }
