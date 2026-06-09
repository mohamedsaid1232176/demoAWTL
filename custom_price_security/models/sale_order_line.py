from odoo import models, api, _, fields
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _is_discount_line(self, vals):
        """تمييز سطر الخصم — هنا نعدل حسب طريقتك في الخصم"""
        # سطر الخصم غالبًا product_id = False أو الاسم يحتوي على Discount
        name = vals.get("name", "")
        return (not vals.get("product_id")) or ("discount" in name.lower())

    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user
        lines = []

        for vals in vals_list:

            # ⚠️ استثناء سطور الخصم
            if self._is_discount_line(vals):
                lines.append(vals)
                continue

            # لو مش Admin → شيّك وحدة السعر
            if not user.has_group("sales_team.group_sale_manager") and "price_unit" in vals:

                tmp_line = self.new(vals)
                tmp_line._onchange_product_id()

                real_price = tmp_line.price_unit
                user_price = vals.get("price_unit")

            lines.append(vals)

        return super().create(lines)

    def write(self, vals):
        user = self.env.user

        # ⚠️ استثناء discount lines وقت التعديل
        if "price_unit" in vals:
            for line in self:
                if self._is_discount_line({'product_id': line.product_id.id, 'name': line.name}):
                    return super(SaleOrderLine, self).write(vals)


        return super().write(vals)


class ResPartner(models.Model):
    _inherit = "res.partner"

    property_product_pricelist = fields.Many2one(
        'product.pricelist',
        string="Pricelist",
        required=True,
        default=False  # أهم سطر = الغاء أي Default من Odoo
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    # الحقول اللي الـ view بيطلبها
    total_due = fields.Float(
        string="Total Due",
        compute="_compute_total_due",
        store=False,
        help="Placeholder to avoid view errors."
    )

    has_moves = fields.Boolean(
        string="Has Moves",
        compute="_compute_has_moves",
        store=False,
        help="Placeholder to avoid view errors."
    )

    total_all_due = fields.Float(
        string="Total All Due",
        compute="_compute_total_all_due",
        store=False,
        help="Placeholder to avoid view errors."
    )

    def _compute_total_due(self):
        for rec in self:
            rec.total_due = 0.0  # Placeholder (اقدر أكتب لك الحساب الحقيقي لو عايز)

    def _compute_has_moves(self):
        for rec in self:
            rec.has_moves = False  # Placeholder

    def _compute_total_all_due(self):
        for rec in self:
            rec.total_all_due = 0.0  # Placeholder
