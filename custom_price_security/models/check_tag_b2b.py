from odoo import models, api, _, fields
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_tags = fields.Many2many(
        related="partner_id.category_id",
        string="Customer Tags",
        readonly=True,  # مهم — ما يتعدلش من السيلز
        store=False  # مش محتاج يتخزن
    )

    # def action_confirm(self):
    #     user = self.env.user
    #
    #     # لو user مش admin
    #     if not user.has_group("sales_team.group_sale_manager"):
    #         partner = self.partner_id
    #
    #         # check لو على العميل Tag اسمه B2B
    #         if "B2B" in partner.category_id.mapped("name"):
    #             raise UserError(_("You cannot confirm this order because the customer is tagged as B2B."))
    #
    #     return super().action_confirm()
    #
