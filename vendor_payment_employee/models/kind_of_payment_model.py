from odoo import models, fields


class KindOfPayment(models.Model):
    _name = "kind.of.payment"
    _description = "Kind of Payment"

    name = fields.Char(
        string="Kind of Payment",
        required=True
    )

