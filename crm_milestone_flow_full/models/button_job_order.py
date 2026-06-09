from odoo import models, fields, api
from odoo.exceptions import UserError

ARKA_COMPANY_REGISTRY = "1010689416"


class WizardCreateJobOrder(models.TransientModel):
    _name = "wizard.create.job.order"
    _description = "Create Job Order Wizard"

    group_idx = fields.Many2one(
        "crm.milestone.group",
        string="Milestone Group",
        ondelete="set null",
    )

    job_type = fields.Selection([
        ('internal', "Internal Manufacturing Order"),
        ('sub_with', "Subcontractor (with material)"),
        ('sub_without', "Subcontractor (without material)")
    ], required=True)

    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor",
    )

    @api.onchange('job_type')
    def _onchange_job_type(self):
        """Vendor يظهر فقط في sub_with و sub_without"""
        if self.job_type in ("sub_with", "sub_without"):
            return {'domain': {'vendor_id': [('supplier_rank', '>', 0)]}}
        else:
            self.vendor_id = False

    def action_confirm(self):
        self.ensure_one()
        group = self.group_idx

        # ============================================
        # GET GOODS & SERVICES (Selected OR All)
        # ============================================

        selected_goods = group.goods_line_ids.filtered(lambda l: l.selected_for_po)
        selected_services = group.service_line_ids.filtered(lambda l: l.selected_for_po)

        if not selected_goods:
            selected_goods = group.goods_line_ids

        if not selected_services:
            selected_services = group.service_line_ids

        product = group.milestone_id.product_variant_id
        qty = group.quantity

        location = group.sale_order_id.last_po_location_id
        if not location:
            raise UserError("Previous Purchase Order not yet created → location missing.")

        # =======================================================
        #  CASE 1 → Internal Manufacturing (GOODS ONLY)
        # =======================================================

        if self.job_type == "internal":

            mo = self.env["mrp.production"].create({
                "product_id": product.id,
                "product_qty": qty,
                "product_uom_id": product.uom_id.id,
                "location_src_id": location.id,
                "location_dest_id": location.id,

                # 🔴 الإضافة الجديدة فقط
                "project_id": group.sale_order_id.project_id.id,

                "job_order_generated": True,
                "job_order_type": self.job_type,
            })

            for line in selected_goods:
                self.env["stock.move"].create({
                    "name": line.product_id.display_name,
                    "product_id": line.product_id.id,
                    "product_uom": line.product_uom.id,
                    "product_uom_qty": line.qty,
                    "location_id": mo.location_src_id.id,
                    "location_dest_id": mo.location_dest_id.id,
                    "raw_material_production_id": mo.id,
                })

            return {
                "type": "ir.actions.act_window",
                "res_model": "mrp.production",
                "view_mode": "form",
                "res_id": mo.id,
            }

        # =======================================================
        #  CASE 2 → Subcontractor WITH Material (GOODS ONLY)
        # =======================================================

        if self.job_type == "sub_with":

            if not self.vendor_id:
                raise UserError("Vendor is required for subcontract with material.")

            po = self.env["purchase.order"].create({
                "partner_id": self.vendor_id.id,
                "project_id": group.sale_order_id.project_id.id,
                "origin": f"Job Order: {group.milestone_id.name}",
                "milestone_location_dest_id": location.id,
                "job_order_generated": True,
                "job_order_type": self.job_type,
            })

            # for line in selected_goods:
            #     self.env["purchase.order.line"].create({
            #         "order_id": po.id,
            #         "product_id": line.product_id.id,
            #         "name": line.product_id.display_name,
            #         "product_qty": line.qty,
            #         "price_unit": line.unit_price/line.qty,
            #         "product_uom": line.product_uom.id,
            #     })

            # Milestone product نفسه
            self.env["purchase.order.line"].create({
                "order_id": po.id,
                "product_id": product.id,
                "name": product.display_name,
                "product_qty": qty,
                "price_unit": (group.total_goods_unit_price + group.total_service_unit_price)/qty,
                "product_uom": product.uom_id.id,
            })
            return {
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "view_mode": "form",
                "res_id": po.id,
            }

        # =======================================================
        #  CASE 3 → Subcontractor WITHOUT Material
        # =======================================================

        if self.job_type == "sub_without":

            if not self.vendor_id:
                raise UserError("Vendor is required for subcontract without material.")

            mo = self.env["mrp.production"].create({
                "product_id": product.id,
                "product_qty": qty,
                "product_uom_id": product.uom_id.id,
                "location_src_id": location.id,
                "location_dest_id": location.id,

                # 🔴 الإضافة الجديدة فقط
                "project_id": group.sale_order_id.project_id.id,

                "job_order_generated": True,
                "job_order_type": self.job_type,
            })

            for line in selected_goods:
                self.env["stock.move"].create({
                    "name": line.product_id.display_name,
                    "product_id": line.product_id.id,
                    "product_uom": line.product_uom.id,
                    "product_uom_qty": line.qty,
                    "location_id": mo.location_src_id.id,
                    "location_dest_id": mo.location_dest_id.id,
                    "raw_material_production_id": mo.id,
                })

            po = self.env["purchase.order"].create({
                "partner_id": self.vendor_id.id,
                "project_id": group.sale_order_id.project_id.id,
                "origin": f"Job Order (Subcontract WO Material): {group.milestone_id.name}",
                "milestone_location_dest_id": location.id,
                "job_order_generated": True,
                "job_order_type": self.job_type,
            })

            for line in selected_services:
                self.env["purchase.order.line"].create({
                    "order_id": po.id,
                    "product_id": line.product_id.id,
                    "name": line.product_id.display_name,
                    "product_qty": line.qty,
                    "price_unit": line.unit_price/line.qty,
                    "product_uom": line.product_uom.id,
                })

            return {
                "type": "ir.actions.act_window",
                "res_model": "mrp.production",
                "view_mode": "form",
                "res_id": mo.id,
            }



# ===========================================================
#   SALE ORDER EXTENSION
# ===========================================================

class SaleOrder(models.Model):
    _inherit = "sale.order"

    last_po_location_id = fields.Many2one(
        "stock.location",
        string="Last PO Location",
        help="Stores the location used for the last milestone purchase order."
    )
