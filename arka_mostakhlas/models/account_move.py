# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_sale_mostakhlas_proforma = fields.Boolean(
        string="Sale Mostakhlas Proforma",
        copy=False,
    )
    mostakhlas_sale_order_id = fields.Many2one(
        "sale.order",
        string="Mostakhlas Sale Order",
        copy=False,
        index=True,
    )

    def write(self, vals):
        if self.env.context.get("arka_mostakhlas_proforma"):
            vals = dict(vals)
            vals["move_type"] = "out_invoice"
        return super().write(vals)
