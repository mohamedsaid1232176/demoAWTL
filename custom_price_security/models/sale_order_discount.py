from odoo import models, api, _, fields
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)




class SaleOrderDiscount(models.TransientModel):
        _inherit = "sale.order.discount"

        # الحدود
        max_discount_line = fields.Float(string="Max Line Discount (%)")
        max_discount_global = fields.Float(string="Max Global Discount (%)")
        max_discount_fixed = fields.Float(string="Max Fixed Amount (SAR)")

        # فيلد إظهار/إخفاء
        show_line_limit = fields.Boolean(compute="_compute_visibility")
        show_global_limit = fields.Boolean(compute="_compute_visibility")
        show_fixed_limit = fields.Boolean(compute="_compute_visibility")

        # Read-only fields for normal users
        max_discount_line_ro = fields.Float(string="Max Line Discount (%)", compute="_compute_ro_limits")
        max_discount_global_ro = fields.Float(string="Max Global Discount (%)", compute="_compute_ro_limits")
        max_discount_fixed_ro = fields.Float(string="Max Fixed Amount (SAR)", compute="_compute_ro_limits")

        # helper field to detect admin
        is_admin = fields.Boolean(compute="_compute_is_admin")

        @api.depends()
        def _compute_ro_limits(self):
            company = self.env.company
            for rec in self:
                rec.max_discount_line_ro = company.max_discount_line
                rec.max_discount_global_ro = company.max_discount_global
                rec.max_discount_fixed_ro = company.max_discount_fixed

        @api.depends()
        def _compute_is_admin(self):
            user = self.env.user
            for rec in self:
                rec.is_admin = user.has_group("sales_team.group_sale_manager")


        @api.depends("discount_type")
        def _compute_visibility(self):
            for rec in self:
                rec.show_line_limit = rec.discount_type == "sol_discount"
                rec.show_global_limit = rec.discount_type == "so_discount"
                rec.show_fixed_limit = rec.discount_type == "amount"

        def default_get(self, fields_list):
            res = super().default_get(fields_list)
            company = self.env.company

            # تحميل القيم للحقول الأصلية (editable admin)
            res.update({
                "max_discount_line": company.max_discount_line,
                "max_discount_global": company.max_discount_global,
                "max_discount_fixed": company.max_discount_fixed,
            })

            # تحميل القيم للحقول الـ read only (للمستخدم العادي)
            res.update({
                "max_discount_line_ro": company.max_discount_line,
                "max_discount_global_ro": company.max_discount_global,
                "max_discount_fixed_ro": company.max_discount_fixed,
            })

            return res

        def action_apply_discount(self):
            discount_type = self.discount_type

            # Line / Global Discount
            if discount_type in ("sol_discount", "so_discount"):
                percentage = self.discount_percentage or 0

                if discount_type == "sol_discount":
                    max_allowed = self.max_discount_line
                else:
                    max_allowed = self.max_discount_global

                # 🔥 log الذكي
                _logger.warning(
                    "CHECK PERCENTAGE: %.2f > %.2f → %s",
                    percentage, max_allowed,
                    "TRUE" if percentage > max_allowed else "FALSE"
                )

                if percentage > max_allowed/100:
                    raise UserError(_(f"Maximum allowed discount is {max_allowed}%."))

            # Fixed amount
            elif discount_type == "amount":
                amount = self.discount_amount or 0
                if amount > self.max_discount_fixed:
                    raise UserError(
                        _(f"Maximum allowed fixed amount is {self.max_discount_fixed} SAR.")
                    )

            # حفظ القيم في الشركة
            company = self.env.company
            company.max_discount_line = self.max_discount_line
            company.max_discount_global = self.max_discount_global
            company.max_discount_fixed = self.max_discount_fixed

            return super().action_apply_discount()


class ResCompany(models.Model):
    _inherit = "res.company"

    max_discount_line = fields.Float(string="Max Line Discount (%)", default=0)
    max_discount_global = fields.Float(string="Max Global Discount (%)", default=0)
    max_discount_fixed = fields.Float(string="Max Fixed Discount Amount", default=0)



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.constrains("discount")
    def _check_max_line_discount(self):
        for line in self:

            # لو مفيش order (rare in draft cases)
            if not line.order_id:
                continue

            company = line.order_id.company_id
            max_allowed = company.max_discount_line or 0

            # لو الخصم أكبر من الحد
            if line.discount > max_allowed:
                raise UserError(
                    _(f"Line discount cannot exceed {max_allowed}%.")
                )
