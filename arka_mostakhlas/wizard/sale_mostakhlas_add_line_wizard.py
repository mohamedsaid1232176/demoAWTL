# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class SaleMostakhlasAddLineWizard(models.TransientModel):
    _name = "sale.mostakhlas.add.line.wizard"
    _description = "Add Sale Mostakhlas Lines"

    order_id = fields.Many2one("sale.order", required=True, readonly=True)
    sale_line_ids = fields.Many2many(
        "sale.order.line",
        string="Order Lines",
    )

    def action_add_lines(self):
        self.ensure_one()
        if not self.sale_line_ids:
            raise UserError("Please select at least one order line.")
        self.order_id._add_mostakhlas_lines_from_sale_lines(self.sale_line_ids)
        self.order_id.show_mostakhlas_tab = True
        return {"type": "ir.actions.act_window_close"}
