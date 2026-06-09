from odoo import models, fields, _, api
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = "project.task"

    vehicle_ids = fields.Many2many(
        "vehicledata",
        string="Vehicles"
    )

    technician_id = fields.Many2one(
        "res.users",
        string="Technician",
        required=True

    )

    product_line_ids = fields.One2many(
        "task.product.line",
        "task_id",
        string="Products",

    )
    dest_location_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        domain="[('name', 'ilike', 'Consignment')]",
        help="Select destination location that contains 'Consignment' in the name",
    )

    # sale order ///////////////////////////////////////////////////////////////////////////////////
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sales Order",
        readonly=True
    )

    sale_order_count = fields.Integer(
        compute="_compute_sale_order_count"
    )

    def _compute_sale_order_count(self):
        for task in self:
            task.sale_order_count = 1 if task.sale_order_id else 0

    def action_create_sales_order(self):
        self.ensure_one()

        if self.sale_order_id:
            raise UserError("Sales Order already created.")

        if not self.partner_id:
            raise UserError("Please select a customer first.")

        # 🔹 استنتاج Warehouse من Parent Location الخاصة بالـ Destination Location
        if not self.dest_location_id:
            raise UserError("Please select Destination Location first.")

        parent_loc = self.dest_location_id.location_id

        warehouse = self.env["stock.warehouse"].search([
            ("view_location_id", "child_of", parent_loc.id)
        ], limit=1)

        if not warehouse:
            raise UserError("لا يوجد Warehouse مرتبط بالـ Parent Location المختار.")

        # 🔹 خطوط المنتجات من تبويب Products
        product_lines = self.product_line_ids.filtered(
            lambda l: l.quantity_used > 0
        )

        if not product_lines:
            raise UserError("No used quantities to invoice.")

        # 🔹 إنشاء Sales Order
        sale_order = self.env["sale.order"].create({
            "partner_id": self.partner_id.id,
            "warehouse_id": warehouse.id,
            "origin": self.name,
            "company_id": self.company_id.id,
        })

        # 🔹 إنشاء Order Lines
        for line in product_lines:
            self.env["sale.order.line"].create({
                "order_id": sale_order.id,
                "product_id": line.product_id.id,
                "product_uom_qty": line.quantity_used,
                "product_uom": line.product_id.uom_id.id,
                "name": line.product_id.display_name,
                "price_unit": line.product_id.lst_price,
            })

        # 🔗 ربط الـ Sales Order بالـ Task
        self.sale_order_id = sale_order.id

        return {
            "type": "ir.actions.act_window",
            "name": "Sales Order",
            "res_model": "sale.order",
            "res_id": sale_order.id,
            "view_mode": "form",
        }

    def action_view_sales_order(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Sales Order",
            "res_model": "sale.order",
            "res_id": self.sale_order_id.id,
            "view_mode": "form",
        }

    # create internal transfer ////////////////////////////////////////////////////////////////////////////////////////

    source_location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        domain=[("usage", "=", "internal")],
        required=True
    )

    picking_id = fields.Many2one(
        "stock.picking",
        string="Internal Transfer",
        readonly=True
    )

    picking_count = fields.Integer(
        compute="_compute_picking_count"
    )

    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = 1 if rec.picking_id else 0

    def action_open_internal_transfer(self):
        self.ensure_one()

        if not self.picking_id:
            return False

        return {
            "type": "ir.actions.act_window",
            "name": "Internal Transfer",
            "res_model": "stock.picking",
            "res_id": self.picking_id.id,
            "view_mode": "form",
        }

    # ===============================
    # Open Wizard
    # ===============================
    def action_open_spare_parts_wizard(self):
        self.ensure_one()

        if not self.product_line_ids:
            raise UserError("No spare parts found on this task.")

        wizard = self.env["request.spare.parts.wizard"].create({
            "task_id": self.id,
            "line_ids": [
                (0, 0, {
                    "task_line_id": line.id,
                    "quantity": line.quantity_ordered,
                })
                for line in self.product_line_ids
                if line.quantity_ordered > 0
            ]
        })

        return {
            "type": "ir.actions.act_window",
            "name": "Confirm Spare Parts Request",
            "res_model": "request.spare.parts.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    # ===============================
    # Create Internal Transfer
    # ===============================
    def _create_internal_transfer(self, wizard_lines):
        self.ensure_one()

        if not self.source_location_id:
            raise UserError("Please select Source Location")

        # Destination Location (your field)
        dest_location = self.dest_location_id
        if not dest_location:
            raise UserError("Please select Destination Location")

        # Picking Type (any internal)
        picking_type = self.env["stock.picking.type"].search([
            ("code", "=", "internal"),
        ], limit=1)

        if not picking_type:
            raise UserError("Internal picking type not found")

        # Create Picking
        picking = self.env["stock.picking"].create({
            "picking_type_id": picking_type.id,
            "location_id": self.source_location_id.id,
            "location_dest_id": dest_location.id,  # initial assignment
            "origin": self.name,
            "partner_id": self.technician_id.partner_id.id,
        })

        # 🔥 override Odoo default destination location
        picking.location_dest_id = dest_location.id

        # Create Moves
        for line in wizard_lines:
            if line.quantity <= 0:
                continue

            product = line.task_line_id.product_id

            self.env["stock.move"].create({
                "picking_id": picking.id,
                "product_id": product.id,
                "product_uom_qty": line.quantity,
                "product_uom": product.uom_id.id,
                "location_id": self.source_location_id.id,
                "location_dest_id": dest_location.id,
                "name": product.display_name,
            })

        return picking


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # ==================================
    # Helpers
    # ==================================

    is_internal_transfer = fields.Boolean(
        string="Is Internal Transfer",
        compute="_compute_is_internal_transfer",
        store=True
    )

    @api.depends("picking_type_id.code")
    def _compute_is_internal_transfer(self):
        for rec in self:
            rec.is_internal_transfer = rec.picking_type_id.code == "internal"

    # ==================================
    # UI Fields (Mirror real stock fields)
    # ==================================

    internal_source_id = fields.Many2one(
        "stock.location",
        string="Internal Source Location",
        domain=[("usage", "=", "internal")],
        related="location_id",
        store=True,
        readonly=False,
    )

    internal_dest_id = fields.Many2one(
        "stock.location",
        string="Internal Destination Location",
        domain=[("usage", "=", "internal")],
        related="location_dest_id",
        store=True,
        readonly=False,
    )

    def button_validate(self):
        res = super().button_validate()

        for picking in self:

            # ===============================
            # 1️⃣ Internal Transfer (مش Return)
            # ===============================
            if (
                    picking.state == "done"
                    and picking.picking_type_id.code == "internal"
                    and not (picking.origin and picking.origin.startswith("Return of"))
            ):
                task = self.env["project.task"].search([
                    ("picking_id", "=", picking.id)
                ], limit=1)

                if not task:
                    continue

                for move in picking.move_ids_without_package:
                    qty_done = sum(move.move_line_ids.mapped("qty_done"))
                    if not qty_done:
                        qty_done = move.product_uom_qty

                    task_lines = task.product_line_ids.filtered(
                        lambda l: l.product_id == move.product_id
                    )

                    for line in task_lines:
                        line.quantity_transferred += qty_done

            # ===============================
            # 2️⃣ Return Picking
            # ===============================
            if picking.origin and picking.origin.startswith("Return of"):
                origin_name = picking.origin.replace("Return of ", "").strip()

                original_picking = self.search([
                    ("name", "=", origin_name)
                ], limit=1)

                if not original_picking:
                    continue

                task = self.env["project.task"].search([
                    ("picking_id", "=", original_picking.id)
                ], limit=1)

                if not task:
                    continue

                for move in picking.move_ids_without_package:
                    qty_done = sum(move.move_line_ids.mapped("qty_done"))
                    if not qty_done:
                        qty_done = move.product_uom_qty

                    task_lines = task.product_line_ids.filtered(
                        lambda l: l.product_id == move.product_id
                    )

                    for line in task_lines:
                        line.quantity_returned += qty_done

        return res


class RequestSparePartsWizard(models.TransientModel):
    _name = "request.spare.parts.wizard"
    _description = "Confirm Spare Parts Request"

    task_id = fields.Many2one(
        "project.task",
        required=True,
        readonly=True
    )

    line_ids = fields.One2many(
        "request.spare.parts.wizard.line",
        "wizard_id",
        string="Spare Parts"
    )

    def action_confirm(self):
        self.ensure_one()

        # ✅ تحديث الكميات في Task
        for line in self.line_ids:
            line.task_line_id.quantity_ordered = line.quantity
            if line.quantity <= 0:
                raise UserError("Quantity must be greater than zero.")
        # ✅ إنشاء Internal Transfer
        picking = self.task_id._create_internal_transfer(self.line_ids)
        # 🔗 ربط الـ picking بالـ task
        self.task_id.picking_id = picking.id

        return {
            "type": "ir.actions.act_window",
            "name": "Internal Transfer",
            "res_model": "stock.picking",
            "res_id": picking.id,
            "view_mode": "form",
        }


class RequestSparePartsWizardLine(models.TransientModel):
    _name = "request.spare.parts.wizard.line"
    _description = "Spare Parts Line"

    wizard_id = fields.Many2one(
        "request.spare.parts.wizard",
        ondelete="cascade"
    )

    task_line_id = fields.Many2one(
        "task.product.line",  # عدّل الاسم حسب موديلك
        string="Task Product Line",
        required=True,
        readonly=True
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        related="task_line_id.product_id",
        readonly=True
    )

    quantity = fields.Float(
        string="Quantity",
        required=True
    )
