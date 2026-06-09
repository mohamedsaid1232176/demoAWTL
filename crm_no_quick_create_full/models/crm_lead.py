from odoo import models, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        ctx = self._context or {}

        # IF not from form view → it's quick create
        is_quick = not ctx.get("form_view_ref") and not ctx.get("view_ref") and not ctx.get("view_id")

        if is_quick and not ctx.get("allow_partner_create"):
            raise UserError("⚠️ غير مسموح بإنشاء جهات الاتصال من الإنشاء السريع. استخدم Create and Edit.")

        return super().create(vals)
