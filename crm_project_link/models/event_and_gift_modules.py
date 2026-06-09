from odoo import models, fields


class EventType(models.Model):
    _name = "event.type"
    _description = "Event Type"

    name = fields.Char(required=True)


class KindOfEvent(models.Model):
    _name = "kind.of.event"
    _description = "Kind of Event"

    name = fields.Char(required=True)
    legacy_key = fields.Char(
        string="Legacy Key",
        help="Old selection value used to migrate CRM leads.",
    )

    _sql_constraints = [
        (
            "legacy_key_unique",
            "unique(legacy_key)",
            "The legacy key must be unique.",
        ),
    ]


class GiftType(models.Model):
    _name = "gift.type"
    _description = "Gift Type"

    name = fields.Char(required=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_tags = fields.Many2many("res.partner.category")
