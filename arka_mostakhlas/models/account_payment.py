# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # ── ربط بأمر البيع ──────────────────────────────
    sale_order_id = fields.Many2one(
        "sale.order",
        string="أمر البيع",
        ondelete="set null",
        index=True,
    )

    # ── هل استُخدمت في مستخلص بيع ──────────────────
    is_used_in_sale_mostakhlas = fields.Boolean(
        string="تم استخدامها في مستخلص",
        default=False,
        copy=False,
    )

    # ── أونشانج أمر البيع ────────────────────────────
    @api.onchange("sale_order_id")
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.partner_id = self.sale_order_id.partner_id
            self.partner_type = "customer"
            self.payment_type = "inbound"
