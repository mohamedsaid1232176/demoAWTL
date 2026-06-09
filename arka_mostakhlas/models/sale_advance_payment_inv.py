# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(
        selection_add=[
            ("mostakhlas_proforma", "Proforma Invoice"),
        ],
        ondelete={"mostakhlas_proforma": "set default"},
    )

    def _create_invoices(self, sale_orders):
        if self.advance_payment_method == "mostakhlas_proforma":
            invoices = self.env["account.move"]
            for order in sale_orders:
                invoices |= order._create_mostakhlas_proforma_invoice()
            return invoices
        return super()._create_invoices(sale_orders)
