from odoo import models, fields


class EventType(models.Model):
    _name = "event.type"
    _description = "Event Type"

    name = fields.Char(required=True)

class GiftType(models.Model):
    _name = "gift.type"
    _description = "Gift Type"

    name = fields.Char(required=True)
class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_tags = fields.Many2many("res.partner.category")
