from odoo import models, api, fields, SUPERUSER_ID,_
from odoo.exceptions import ValidationError,UserError



class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _load_user_context(self):
        ctx = super()._load_user_context()
        ctx['allowed_warehouse_ids'] = self.env.user.allowed_warehouse_ids.ids

        return ctx
    allowed_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Allowed Warehouses'
    )

    allowed_location_ids = fields.Many2many(
        'stock.location',
        compute="_compute_allowed_locations",
        string="Allowed Locations",
        store=False
    )

    def _compute_allowed_locations(self):
        for user in self:
            locations = user.allowed_warehouse_ids.mapped('view_location_id').mapped('child_ids')
            user.allowed_location_ids = locations




class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    @api.model
    def get_current_warehouses(self, *args, **kwargs):

        warehouses = self.search([])
        result = [{"id": w.id, "name": w.name} for w in warehouses]

        user = self.env.user

        # Admin يشوف الكل
        if user.id == SUPERUSER_ID:
            return result

        # لو مفيش صلاحيات محددة → رجّع الكل
        if not user.allowed_warehouse_ids:
            return result

        # غير كده → فلترة حسب المسموح
        allowed = set(user.allowed_warehouse_ids.ids)
        return [w for w in result if w["id"] in allowed]


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    allowed_for_user = fields.Boolean(
        compute="_compute_allowed_for_user",
        search="_search_allowed_for_user",
        store=False
    )

    def _compute_allowed_for_user(self):
        user = self.env.user
        allowed_ids = set(user.allowed_warehouse_ids.ids)

        for rec in self:
            rec.allowed_for_user = (
                not allowed_ids or rec.warehouse_id.id in allowed_ids
            )

    @api.model
    def _search_allowed_for_user(self, operator, value):
        """Make allowed_for_user searchable."""
        user = self.env.user
        allowed_ids = user.allowed_warehouse_ids.ids

        if not allowed_ids:
            # User has no restriction → return everything
            return []

        # Return only picking types with allowed warehouses
        return [('warehouse_id', 'in', allowed_ids)]






class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    allowed_for_user = fields.Boolean(
        compute="_compute_allowed_for_user",
        search="_search_allowed_for_user",
        store=False
    )

    def _compute_allowed_for_user(self):
        user = self.env.user
        allowed_locations = user.allowed_location_ids.ids

        # لو المستخدم ملوش صلاحيات → يشوف الكل
        if not allowed_locations:
            for rec in self:
                rec.allowed_for_user = True
            return

        for rec in self:
            rec.allowed_for_user = (
                    rec.location_id.id in allowed_locations or
                    rec.location_dest_id.id in allowed_locations
            )

    @api.model
    def _search_allowed_for_user(self, operator, value):
        user = self.env.user
        allowed_locations = user.allowed_location_ids.ids

        if not allowed_locations:
            return []  # يشوف كل شيء

        return [
            '|',
            ('location_id', 'in', allowed_locations),
            ('location_dest_id', 'in', allowed_locations),
        ]


class StockLocation(models.Model):
    _inherit = "stock.location"

    allowed_for_user = fields.Boolean(
        compute="_compute_allowed_for_user",
        search="_search_allowed_for_user",
        store=False
    )

    def _compute_allowed_for_user(self):
        user = self.env.user
        allowed_warehouses = user.allowed_warehouse_ids

        # user ملوش صلاحيات → يشوف الكل
        if not allowed_warehouses:
            for loc in self:
                loc.allowed_for_user = True
            return

        # كل المواقع التابعة للـ warehouses
        allowed_locations = (
            allowed_warehouses.mapped("view_location_id").mapped("child_ids").ids
        )

        for loc in self:
            loc.allowed_for_user = loc.id in allowed_locations


    @api.model
    def _search_allowed_for_user(self, operator, value):
        user = self.env.user
        allowed_warehouses = user.allowed_warehouse_ids

        if not allowed_warehouses:
            return []  # يشوف الكل

        allowed_locations = (
            allowed_warehouses.mapped("view_location_id").mapped("child_ids").ids
        )

        return [('id', 'in', allowed_locations)]



