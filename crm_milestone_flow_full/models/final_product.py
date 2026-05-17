# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

ARKA_COMPANY_REGISTRY = "311369490700003"


class CrmLeadFinalProduct(models.Model):
    _inherit = "crm.lead"

    # =========================================================
    # Flags
    # =========================================================
    is_final_product_quotation_generated = fields.Boolean(default=False)

    # =========================================================
    # Final Product Fields
    # =========================================================
    final_product = fields.Boolean(string="Final Product")
    final_product_id = fields.Many2one(
        "product.product",
        string="Final Product",
        domain=[("sale_ok", "=", True)],
    )

    # =========================================================
    # Generate Final Product Quotation Button
    # =========================================================
    def action_generate_final_product_quotation(self):
        """
        يعمل مثل زر Generate Quotation الأصلي
        لكن لا يضع خطوط الميلاستون داخل order lines
        بل يضيف Sections + خط واحد فقط للـ Final Product
        """
        self.ensure_one()

        # منع التكرار
        if self.is_final_product_quotation_generated:
            raise UserError("❌ غير مسموح بإنشاء عرض سعر Final Product مرة أخرى.")

        if not self.final_product_id:
            raise UserError("Please select the Final Product first.")

        # if not self.project_id:
        #     raise UserError("Please select a project before generating quotation.")

        partner = self.partner_id
        if not partner:
            raise UserError("Please select a customer first.")

        project = self.project_id

        # =========================================================
        # Analytic Account Logic
        # =========================================================
        # analytic_account = self.env['account.analytic.account'].search([
        #     ('project_ids', 'in', project.id)
        # ], limit=1)
        #
        # if not analytic_account:
        #     plan = self.env['account.analytic.plan'].search([], limit=1)
        #     if not plan:
        #         raise UserError("Please create an Analytic Plan first.")
        #
        #     analytic_account = self.env['account.analytic.account'].create({
        #         "name": project.name,
        #         "company_id": project.company_id.id,
        #         "plan_id": plan.id,
        #     })
        #
        # project.account_id = analytic_account.id

        # =========================================================
        # Budget Logic
        # =========================================================
        # Budget = self.env["budget.analytic"]
        # BudgetLine = self.env["budget.line"]
        #
        # total_cost = sum(group.total_cost for group in self.milestone_group_ids)
        # total_unit_price = self.total_unit_price_project
        #
        # date_from = self.date_start or fields.Date.today()
        # date_to = self.date_end or date_from
        #
        # # EXPENSE BUDGET
        # expense_budget = Budget.create({
        #     "name": f"{project.name} - Expense Budget",
        #     "user_id": self.user_id.id,
        #     "budget_type": "expense",
        #     "date_from": date_from,
        #     "date_to": date_to,
        #     "company_id": self.company_id.id,
        # })
        #
        # BudgetLine.create({
        #     "account_id": analytic_account.id,
        #     "budget_analytic_id": expense_budget.id,
        #     "budget_amount": total_cost,
        #     "company_id": self.company_id.id,
        # })
        #
        # expense_budget.action_budget_confirm()
        #
        # # REVENUE BUDGET
        # revenue_budget = Budget.create({
        #     "name": f"{project.name} - Revenue Budget",
        #     "user_id": self.user_id.id,
        #     "budget_type": "revenue",
        #     "date_from": date_from,
        #     "date_to": date_to,
        #     "company_id": self.company_id.id,
        # })
        #
        # BudgetLine.create({
        #     "account_id": analytic_account.id,
        #     "budget_analytic_id": revenue_budget.id,
        #     "budget_amount": total_unit_price,
        #     "company_id": self.company_id.id,
        # })
        #
        # revenue_budget.action_budget_confirm()

        # =========================================================
        # Create Sale Order
        # =========================================================
        sale_order = self.env["sale.order"].create({
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": partner.id,
            "opportunity_id": self.id,
            "origin": f"Final Product for {self.name}",
            "project_id": project.id,
            "is_crm_custom_quotation": True,

        })

        # =========================================================
        # Copy Milestone Groups (NO order lines)
        # =========================================================
        for group in self.milestone_group_ids:

            new_group = group.copy({
                "sale_order_id": sale_order.id,
                "lead_id": False,
            })

            # GOODS COPY
            for line in group.goods_line_ids:
                self.env["crm.milestone.line"].create({
                    "goods_group_id": new_group.id,
                    "product_id": line.product_id.id,
                    "qty": line.qty,
                    "pricing_method": line.pricing_method,
                    "pricelist_id": line.pricelist_id.id,
                    "margin": line.margin,
                    "manual_product_cost": line.manual_product_cost,
                    "manual_product_sale_price": line.manual_product_sale_price,
                    "type": "goods",
                })

            # SERVICES COPY
            for line in group.service_line_ids:
                self.env["crm.milestone.line"].create({
                    "service_group_id": new_group.id,
                    "product_id": line.product_id.id,
                    "qty": line.qty,
                    "pricing_method": line.pricing_method,
                    "pricelist_id": line.pricelist_id.id,
                    "margin": line.margin,
                    "manual_product_cost": line.manual_product_cost,
                    "manual_product_sale_price": line.manual_product_sale_price,
                    "type": "service",
                })

        # =========================================================
        # Add Final Product Line FIRST (sequence صغير جداً)
        # =========================================================
        self.env["sale.order.line"].create({
            "order_id": sale_order.id,
            "product_id": self.final_product_id.id,
            "name": f"🎯 Final Product: {self.final_product_id.name}",
            "product_uom_qty": 1,
            "price_unit": self.total_unit_price_project,
            "product_uom": self.final_product_id.uom_id.id,
            "sequence": 1,  # ← أول سطر
        })

        # =========================================================
        # Add Milestone Sections AFTER final product
        # =========================================================
        seq = 10
        for group in self.milestone_group_ids:
            self.env["sale.order.line"].create({
                "order_id": sale_order.id,
                "display_type": "line_section",
                "name": f"📌 {group.milestone_id.name}",
                "sequence": seq,
            })
            seq += 10

        # =========================================================
        # Mark as generated
        # =========================================================
        self.is_final_product_quotation_generated = True

        # =========================================================
        # Open the SO
        # =========================================================
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": sale_order.id,
        }
