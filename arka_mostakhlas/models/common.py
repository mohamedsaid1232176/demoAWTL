# -*- coding: utf-8 -*-
from odoo import models, fields, api


# ══════════════════════════════════════════════════════════════════
#                         MOSTAKHLAS TYPE
# ══════════════════════════════════════════════════════════════════
class MostakhlasType(models.Model):
    _name = "mostakhlas.type"
    _description = "Mostakhlas Type"
    _order = "name"

    name = fields.Char(string="نوع المستخلص", required=True)
    active = fields.Boolean(default=True)


# ══════════════════════════════════════════════════════════════════
#               SALE MOSTAKHLAS LINE
# ══════════════════════════════════════════════════════════════════
class SaleMostakhlasLine(models.Model):
    _name = "sale.mostakhlas.line"
    _description = "Sale Mostakhlas Line"
    _order = "sequence_int, id"

    order_id = fields.Many2one(
        "sale.order", required=True, ondelete="cascade"
    )
    sequence_int = fields.Integer(string="رقم البند", store=True)

    customer_id = fields.Many2one(related="order_id.partner_id", store=True)
    project_id = fields.Many2one(related="order_id.project_id", store=True)

    mostakhlas_type_id = fields.Many2one("mostakhlas.type", string="نوع المستخلص")

    sale_line_id = fields.Many2one(
        "sale.order.line",
        string="Sale Order Line",
        ondelete="set null",
        index=True,
    )
    product_id = fields.Many2one("product.product", string="المنتج")
    name = fields.Text(string="الوصف")

    product_qty = fields.Float(string="الكمية", default=1.0)
    product_uom = fields.Many2one("uom.uom", string="وحدة القياس")
    price_unit = fields.Float(string="سعر الوحدة", default=0.0)
    discount = fields.Float(string="الخصم %")
    taxes_id = fields.Many2many("account.tax", string="الضرائب")

    currency_id = fields.Many2one(
        related="order_id.currency_id", store=True, readonly=True
    )
    price_subtotal = fields.Monetary(
        string="المبلغ",
        currency_field="currency_id",
        compute="_compute_price_subtotal",
        store=True,
    )

    analytic_distribution = fields.Json(string="التوزيع التحليلي")
    print_in_report = fields.Boolean(string="طباعة في التقرير", default=False)

    # نسبة الإنجاز في هذا المستخلص
    progress_percent = fields.Float(string="نسبة الإنجاز الحالية (%)", default=0.0)
    # إجمالي الإنجاز التراكمي بعد هذا المستخلص
    done_progress = fields.Float(string="إجمالي الإنجاز (%)", default=0.0)

    # نسبة الإنجاز قبل هذا المستخلص = done_progress - progress_percent
    previous_progress = fields.Float(
        string="نسبة الإنجاز السابقة (%)",
        compute="_compute_previous_progress",
        store=False,
    )

    @api.depends("done_progress", "progress_percent")
    def _compute_previous_progress(self):
        for line in self:
            line.previous_progress = max(
                0.0,
                (line.done_progress or 0.0) - (line.progress_percent or 0.0),
            )

    is_progress_locked = fields.Boolean(
        compute="_compute_is_progress_locked", store=False
    )

    @api.depends("done_progress")
    def _compute_is_progress_locked(self):
        for line in self:
            line.is_progress_locked = line.done_progress >= 100

    @api.depends("product_qty", "price_unit", "discount")
    def _compute_price_subtotal(self):
        for line in self:
            subtotal = (line.product_qty or 0.0) * (line.price_unit or 0.0)
            if line.discount:
                subtotal -= subtotal * (line.discount / 100)
            line.price_subtotal = subtotal


# ══════════════════════════════════════════════════════════════════
#               SALE MOSTAKHLAS PRINT BUFFER
# ══════════════════════════════════════════════════════════════════
class SaleMostakhlasPrintBuffer(models.Model):
    _name = "sale.mostakhlas.print.buffer"
    _description = "Buffered Lines For Sale Mostakhlas Printing"

    line_id = fields.Many2one(
        "sale.mostakhlas.line", required=True, ondelete="cascade"
    )
    order_id = fields.Many2one(
        "sale.order", required=True, ondelete="cascade"
    )
