from odoo import models, fields, api
import logging

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"


    internal_source_id = fields.Many2one(
        "stock.location",
        string="Internal Source",
        domain=[('usage', '=', 'internal')],
        help="Shown only for internal transfers"
    )

    internal_dest_id = fields.Many2one(
        "stock.location",
        string="Destination Transit Location",
        domain=[
            '|',
            ('usage', '=', 'transit'),
            '&',
            ('usage', '=', 'internal'),
            ('name', 'ilike', 'Consignment'),
        ],
        help="Shown only for internal transfers"
    )

    def _is_internal_picking(self, picking_type_id):
        if not picking_type_id:
            return False
        return (
                picking_type_id.code == "internal"
                or "internal" in (picking_type_id.name or "").lower()
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if rec._is_internal_picking(rec.picking_type_id):
                if not rec.internal_source_id:
                    raise ValidationError(
                        "Internal Source is required for Internal Transfers."
                    )
                if not rec.internal_dest_id:
                    raise ValidationError(
                        "Internal Destination is required for Internal Transfers."
                    )
        return records

    def write(self, vals):
        res = super().write(vals)

        for rec in self:
            # picking_type ممكن يتغير في write
            picking_type = (
                self.env["stock.picking.type"].browse(vals["picking_type_id"])
                if "picking_type_id" in vals
                else rec.picking_type_id
            )

            if rec._is_internal_picking(picking_type):
                if not rec.internal_source_id:
                    raise ValidationError(
                        "Internal Source is required for Internal Transfers."
                    )
                if not rec.internal_dest_id:
                    raise ValidationError(
                        "Internal Destination is required for Internal Transfers."
                    )
        return res

    @api.onchange("picking_type_id")
    def _onchange_operation_type(self):
        """Show internal fields only when picking type is INTERNAL."""
        for rec in self:
            pt = rec.picking_type_id
            if not pt:
                rec.internal_source_id = False
                rec.internal_dest_id = False
                return

            name_low = (pt.name or "").lower()
            code = pt.code or ""

            rec.is_internal_transfer = ("internal" in name_low) or (code == "internal")

    @api.onchange("internal_source_id")
    def _onchange_internal_source(self):
        """If internal source selected, push it to original source field."""
        for rec in self:
            if rec.internal_source_id:
                rec.location_id = rec.internal_source_id

    @api.onchange("internal_dest_id")
    def _onchange_internal_dest(self):
        """If internal destination selected, push it to original destination field."""
        for rec in self:
            if rec.internal_dest_id:
                rec.location_dest_id = rec.internal_dest_id

    # helper computed boolean for visibility in XML
    is_internal_transfer = fields.Boolean(compute="_compute_internal_flag")

    @api.depends("picking_type_id")
    def _compute_internal_flag(self):
        for rec in self:
            name_low = (rec.picking_type_id.name or "").lower()
            code = rec.picking_type_id.code or ""
            rec.is_internal_transfer = ("internal" in name_low) or (code == "internal")
