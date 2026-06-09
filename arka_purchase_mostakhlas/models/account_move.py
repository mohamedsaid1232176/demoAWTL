from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_purchase_mostakhlas_proforma = fields.Boolean(
        string="Purchase Mostakhlas Proforma",
        copy=False,
    )
    mostakhlas_purchase_order_id = fields.Many2one(
        "purchase.order",
        string="Mostakhlas Purchase Order",
        copy=False,
        index=True,
    )
