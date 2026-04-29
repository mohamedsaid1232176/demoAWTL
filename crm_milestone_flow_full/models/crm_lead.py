# -*- coding: utf-8 -*-
from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import UserError

from odoo.exceptions import ValidationError

ARKA_COMPANY_REGISTRY = "311369490700003"


class CrmMilestoneGroup(models.Model):
    _name = "crm.milestone.group"
    _description = "Milestone Group"

    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")

    planned_date_from = fields.Date(
        string="Planned Date From",
    )

    planned_date_to = fields.Date(
        string="Planned Date To",
    )
    total_sale_milestone = fields.Float(
        string="Total Sale",
        compute="_compute_totals",
        store=True
    )

    quantity = fields.Float(string="Quantity Milestone", default=1, store=True)
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        ondelete="cascade"
    )
    total_cost = fields.Float(
        string="Total Cost (G+S)",
        compute="_compute_total_cost",
        store=True
    )

    @api.depends(
        "total_goods_cost",
        "total_service_cost"
    )
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = (rec.total_goods_cost or 0.0) + (rec.total_service_cost or 0.0)

    def action_open_po_wizard(self):
        self.ensure_one()
        return {
            'name': "Create Purchase Order",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.create.po',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_group_idx': self.id,
            }
        }

    def action_open_job_order_wizard(self):
        self.ensure_one()
        return {
            'name': "Create Job Order",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.create.job.order',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_group_idx': self.id,
            }
        }

    stage = fields.Selection([
        ('project', 'إدارة المشروع'),
        ('technical', 'المكتب الفني'),

    ], string="Stage", default='technical')

    def action_to_technical(self):
        for rec in self:
            rec.stage = 'technical'

    def action_to_project(self):
        for rec in self:
            rec.stage = 'project'

    lead_id = fields.Many2one("crm.lead", string="Opportunity", ondelete="cascade")

    milestone_id = fields.Many2one(
        "product.template",
        domain=[('is_milestone_flag', '=', True)],
        string="Milestone"
    )

    def action_open_goods_popup(self):
        self.ensure_one()
        return {
            'name': 'Select Goods',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.goods.selector',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.lead_id.id,
                'default_milestone_id': self.milestone_id.id,
                'force_type': 'goods',
                'default_group_idx': self.id,
            }
        }

    def action_open_services_popup(self):
        self.ensure_one()
        return {
            'name': 'Select Services',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.services.selector',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.lead_id.id,
                'default_milestone_id': self.milestone_id.id,
                'force_type': 'service',
                'default_group_idx': self.id,
            }
        }

    # goods + services lines for this group ONLY
    goods_line_ids = fields.One2many(
        "crm.milestone.line",
        "goods_group_idx",
        string="Goods Lines"
    )

    service_line_ids = fields.One2many(
        "crm.milestone.line",
        "service_group_idx",
        string="Service Lines"
    )
    goods_line_ids = fields.One2many("crm.milestone.line", "goods_group_id")
    service_line_ids = fields.One2many("crm.milestone.line", "service_group_id")

    # totals (store=False عشان تتحدث فوراً وما تختفيش)
    total_goods_cost = fields.Float(compute="_compute_totals", store=True)
    total_goods_unit_price = fields.Float(compute="_compute_totals", store=True)
    total_goods_sale = fields.Float(compute="_compute_totals", store=False)

    total_service_cost = fields.Float(compute="_compute_totals", store=True)
    total_service_unit_price = fields.Float(compute="_compute_totals", store=True)
    total_service_sale = fields.Float(compute="_compute_totals", store=False)

    @api.depends(
        "goods_line_ids.unit_price",
        "goods_line_ids.qty",
        "goods_line_ids.manual_product_cost",
        "goods_line_ids.manual_product_sale_price",
        "service_line_ids.unit_price",
        "service_line_ids.qty",
        "service_line_ids.manual_product_cost",
        "service_line_ids.manual_product_sale_price",
        "quantity",
    )
    def _compute_totals(self):
        """Recompute totals dynamically. Always correct & never disappears."""
        for rec in self:
            # GOODS
            rec.total_goods_cost = sum(line.manual_product_cost * line.qty for line in rec.goods_line_ids)
            rec.total_goods_unit_price = sum(line.unit_price for line in rec.goods_line_ids)
            rec.total_goods_sale = (
                rec.total_goods_unit_price / rec.quantity if rec.quantity else 0.0
            )

            # rec.total_goods_sale = sum(line.manual_product_sale_price * line.qty for line in rec.goods_line_ids)

            # SERVICES
            rec.total_service_cost = sum(line.manual_product_cost * line.qty for line in rec.service_line_ids)
            rec.total_service_unit_price = sum(line.unit_price for line in rec.service_line_ids)
            rec.total_service_sale = (
                rec.total_service_unit_price / rec.quantity if rec.quantity else 0.0
            )
            # rec.total_service_sale = sum(line.manual_product_sale_price * line.qty for line in rec.service_line_ids)
            rec.total_sale_milestone = (
                    rec.total_goods_sale + rec.total_service_sale
            )

class CrmMilestoneLine(models.Model):
    _name = "crm.milestone.line"
    _description = "Milestone Line"
    _order = "id desc"

    po_line_ids = fields.One2many(
        "purchase.order.line",
        "milestone_line_id",
        string="Related PO Lines"
    )

    delivered_quantity = fields.Float(
        string="Delivered Qty",
        compute="_compute_delivered_quantity",
        store=False
    )

    @api.depends("po_line_ids.qty_received")
    def _compute_delivered_quantity(self):
        for rec in self:
            rec.delivered_quantity = sum(rec.po_line_ids.mapped("qty_received"))

    selected_for_po = fields.Boolean(
        string="Select for PO",
        help="Include this line when creating Purchase Order."
    )
    # NEW: Manual fields (بديل للـ related)
    manual_product_cost = fields.Float(
        string="Cost"
    )

    manual_product_sale_price = fields.Float(
        string="Sale Price"
    )

    current_stage = fields.Selection(
        [
            ('technical', 'المكتب الفني'),
            ('project', 'إدارة المشروع'),
        ],
        string="Stage",
        compute="_compute_current_stage",
        store=False,
    )

    @api.depends("goods_group_id.stage", "service_group_id.stage")
    def _compute_current_stage(self):
        for rec in self:
            rec.current_stage = rec.goods_group_id.stage or rec.service_group_id.stage

    goods_group_id = fields.Many2one("crm.milestone.group", string="Goods Group")
    service_group_id = fields.Many2one("crm.milestone.group", string="Service Group")

    total_price = fields.Float(
        string="Total",
        compute="_compute_unit_price",
        store=False
    )

    margin = fields.Float(string="Margin (%)")
    unit_price = fields.Float(
        string="Unit Price",
        compute="_compute_unit_price",
        store=False
    )

    @api.depends("manual_product_cost", "manual_product_sale_price", "product_cost", "product_sale_price", "margin",
                 "qty")
    def _compute_unit_price(self):
        for rec in self:
            # cost manual لو موجود، otherwise استخدم related القديم
            cost = rec.manual_product_cost or rec.manual_product_cost

            margin_value = cost * rec.qty * (rec.margin / 100) + cost * rec.qty
            rec.unit_price = margin_value

    goods_lead_id = fields.Many2one("crm.lead", string="Goods Lead")
    service_lead_id = fields.Many2one("crm.lead", string="Service Lead")

    product_default_code = fields.Char(
        string="Internal Reference",
        related="product_id.default_code",
        store=False
    )

    product_barcode = fields.Char(
        string="Barcode",
        related="product_id.barcode",
        store=False
    )

    product_cost = fields.Float(
        string="Cost",
        related="product_id.standard_price",
        store=False
    )

    product_sale_price = fields.Float(
        string="Sale Price",
        related="product_id.list_price",
        store=False
    )

    product_uom = fields.Many2one(
        "uom.uom",
        string="UoM",
        related="product_id.uom_id",
        store=False
    )

    product_variants = fields.Many2many(
        "product.attribute.value",
        string="Variants",
        compute="_compute_product_variants",
        store=False
    )

    @api.depends("product_id")
    def _compute_product_variants(self):
        for rec in self:
            if rec.product_id:
                rec.product_variants = rec.product_id.product_template_attribute_value_ids.mapped(
                    "product_attribute_value_id")
            else:
                rec.product_variants = False

    lead_id = fields.Many2one("crm.lead", ondelete="cascade", string="Opportunity")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    qty = fields.Float(string="Quantity", default=1.0)
    price = fields.Float(string="Unit Price", related="product_id.list_price", store=True)
    type = fields.Selection([('goods', 'Goods'), ('service', 'Service')], string="Type")
    description = fields.Char(string="Description")


class CrmLead(models.Model):
    _inherit = "crm.lead"


    total_cost_project = fields.Float(
        string="Total Cost Project",
        compute="_compute_totals_project",
        store=False
    )

    total_unit_price_project = fields.Float(
        string="Total Unit Price Project",
        compute="_compute_totals_project",
        store=False
    )

    show_unit_price_field = fields.Boolean(
        compute="_compute_show_unit_price_field",
        store=False
    )

    @api.depends("stage_id")
    def _compute_show_unit_price_field(self):
        for rec in self:
            rec.show_unit_price_field = rec.stage_id.name != "Technical Office"

    @api.depends("milestone_group_ids.total_cost",
                 "milestone_group_ids.total_goods_unit_price",
                 "milestone_group_ids.total_service_unit_price")
    def _compute_totals_project(self):
        for rec in self:
            rec.total_cost_project = sum(g.total_cost for g in rec.milestone_group_ids)
            rec.total_unit_price_project = sum(
                (g.total_goods_unit_price or 0.0) + (g.total_service_unit_price or 0.0)
                for g in rec.milestone_group_ids
            )

    milestone_group_ids = fields.One2many(
        "crm.milestone.group",
        "lead_id",
        string="Milestone Groups"
    )

    def action_add_milestone_group(self):
        self.ensure_one()
        self.env["crm.milestone.group"].create({"lead_id": self.id})

    milestone_id = fields.Many2one(
        "product.template",
        domain=[('is_milestone_flag', '=', True)],
        string="Milestone",
        help="Select the milestone for this opportunity (Arka only)."
    )
    milestone_line_ids = fields.One2many(
        "crm.milestone.line", "lead_id", string="Milestone Lines"
    )
    milestone_line_goods_ids = fields.One2many(
        "crm.milestone.line",
        "goods_lead_id",
        string="Goods Lines"
    )

    milestone_line_service_ids = fields.One2many(
        "crm.milestone.line",
        "service_lead_id",
        string="Service Lines"
    )

    is_proposition_stage = fields.Boolean(
        compute="_compute_is_proposition_stage",
        store=False
    )
    is_arka_company = fields.Boolean(
        compute="_compute_is_arka_company",
        store=False
    )

    def _compute_is_arka_company(self):
        for r in self:
            r.is_arka_company = (r.env.company.company_registry == ARKA_COMPANY_REGISTRY)

    def _compute_is_proposition_stage(self):
        for r in self:
            r.is_proposition_stage = (r.stage_id and r.stage_id.name == 'Technical Office')

    def action_open_goods_popup(self):
        self.ensure_one()
        if not self.milestone_id:
            raise UserError('Please select a Milestone first.')
        return {
            'name': 'Select Goods for Milestone',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.goods.selector',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_milestone_id': self.milestone_id.id,
                'force_type': 'goods',
            }
        }

    def action_open_services_popup(self):
        self.ensure_one()
        if not self.milestone_id:
            raise UserError('Please select a Milestone first.')
        return {
            'name': 'Select Services for Milestone',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.services.selector',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_milestone_id': self.milestone_id.id,
                'force_type': 'service',
            }
        }



# add
class WizardCreatePO(models.TransientModel):
    _name = "wizard.create.po"
    _description = "Create PO Wizard"

    group_idx = fields.Many2one("crm.milestone.group")

    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
    )

    # ➤ إضافة اختيار Service هنا
    po_type = fields.Selection(
        [
            ('inventory', "With Inventory Material"),
            ('non_inventory', "Non Inventory Material"),
            ('service', "Service"),
        ],
        string="Material Type",
        required=True
    )

    def action_confirm_create_po(self):
        self.ensure_one()
        group = self.group_idx

        # ============================================
        # 1) SELECT LINES BASED ON TYPE
        # ============================================
        if self.po_type == "service":
            # خــدمــات فقط
            lines = group.service_line_ids.filtered(lambda l: l.selected_for_po)
            if not lines:
                lines = group.service_line_ids

        else:
            # Goods فقط (inventory + non-inventory)
            lines = group.goods_line_ids.filtered(lambda l: l.selected_for_po)
            if not lines:
                lines = group.goods_line_ids

        if not lines:
            raise UserError("No products selected for purchase order.")

        # ============================================
        # 2) GET PROJECT + SALE ORDER
        # ============================================
        sale_order = group.sale_order_id
        project = sale_order.project_id if sale_order else False

        # ============================================
        # 3) DETERMINE LOCATION
        # ============================================
        StockLocation = self.env["stock.location"].search([
            ("company_id", "=", self.env.company.id),
            ("usage", "=", "internal"),
            ("name", "=", "Stock"),
        ], limit=1)

        if not StockLocation:
            raise UserError("Could not find WH/Stock location for this company.")

        # ➤ اختيار Service → بدون Location نهائياً
        if self.po_type == "service":
            location_dest = False

        # ➤ Inventory → WH/Stock
        elif self.po_type == "inventory":
            location_dest = StockLocation

        # ➤ Non-inventory → يعمل / يعيد استخدام موقع المشروع
        else:
            if not project:
                raise UserError("No project selected in this sale order.")

            if not project.location_id:
                raise UserError("Project has no location. اعمل confirm الأول")

            location_dest = project.location_id

        # ============================================
        # 4) CREATE PURCHASE ORDER
        # ============================================
        po_vals = {
            "partner_id": self.vendor_id.id,
            "project_id": project.id if project else False,
            "origin": f"Milestone: {group.milestone_id.name}",
            "milestone_po": True,
            "milestone_type": self.po_type,
        }

        # ➤ محدد location فقط لو مش Service
        if location_dest:
            po_vals["milestone_location_dest_id"] = location_dest.id

        po = self.env["purchase.order"].create(po_vals)

        # حفظ آخر location فقط لو مش Service
        if sale_order and location_dest:
            sale_order.last_po_location_id = location_dest

        # ============================================
        # 5) CREATE PO LINES
        # ============================================
        for line in lines:
            self.env["purchase.order.line"].create({
                "order_id": po.id,
                "product_id": line.product_id.id,
                "name": line.product_id.display_name,
                "product_qty": line.qty,
                "price_unit": line.manual_product_cost,
                "date_planned": fields.Date.today(),
                "product_uom": line.product_uom.id,
                "milestone_line_id": line.id,
            })

        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": po.id,
        }



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    milestone_location_dest_id = fields.Many2one(
        "stock.location",
        string="Milestone Destination Location",
        invisible=True
    )

    def _prepare_picking(self):
        vals = super()._prepare_picking()

        if self.milestone_location_dest_id:
            vals["location_dest_id"] = self.milestone_location_dest_id.id

        return vals

    @api.constrains('group_idx')
    def _check_group_id_valid(self):
        for rec in self:
            if rec.group_idx and not self.env['crm.milestone.group'].search([('id', '=', rec.group_idx.id)], limit=1):
                raise ValidationError("Invalid Milestone Group! This group does not exist.")


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    milestone_line_id = fields.Many2one(
        "crm.milestone.line",
        string="Milestone Line",
        ondelete="set null"
    )

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()

        for picking in self:
            po = self.env["purchase.order"].search([
                ("name", "=", picking.origin)
            ], limit=1)

            if po and po.milestone_location_dest_id:
                new_loc = po.milestone_location_dest_id.id

                # 🔥 ده المهم الحقيقي
                for move_line in picking.move_line_ids:
                    move_line.location_dest_id = new_loc

        return res