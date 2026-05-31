from odoo import models, fields, api
from odoo.exceptions import ValidationError

ALLOWED_COMPANY_REGISTRIES = ["7012242793", "1010232192","1010689416"]   # ✅ المتغير الوحيد المستخدم الآن



class ResUsers(models.Model):
    _inherit = "res.users"

    allow_payment_confirm = fields.Boolean(
        string="Allow Payment Confirm"
    )

    show_employee_fields = fields.Boolean(
        compute="_compute_show_employee_fields",
        store=False
    )

    @api.depends("company_id")
    def _compute_show_employee_fields(self):
        for rec in self:
            rec.show_employee_fields = bool(
                rec.company_id
                and rec.company_id.company_registry in ALLOWED_COMPANY_REGISTRIES
            )
