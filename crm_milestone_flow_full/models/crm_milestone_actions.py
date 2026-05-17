# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError

from odoo.exceptions import ValidationError

ARKA_COMPANY_REGISTRY = "311369490700003"


# -----------------------------
# Project Milestone (Inherited)
# -----------------------------
class ProjectMilestone(models.Model):
    _inherit = "project.milestone"

    x_sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Related SO Line',
        help="Reference to the sale order line created from CRM milestone groups"
    )


# -----------------------------
# CRM Lead
# -----------------------------
class CrmLead(models.Model):
    _inherit = "crm.lead"

    is_milestone_quotation_generated = fields.Boolean(default=False)

    def action_generate_milestone_quotation(self):
        self.ensure_one()

        # if not self.project_id:
        #     won_stage = self.env['crm.stage'].search([('is_won', '=', True)], limit=1)
        #
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'name': 'Confirm Project Creation',
        #         'res_model': 'lead.won.confirm.wizard',
        #         'view_mode': 'form',
        #         'target': 'new',
        #         'context': {
        #             'default_lead_id': self.id,
        #             'default_new_stage_id': won_stage.id,
        #             'after_project_create_action': 'generate_milestone_quotation',
        #         }
        #     }
        # منع تكرار إنشاء Quotation نهائياً
        if self.is_milestone_quotation_generated:
            raise UserError("غير مسموح بإنشاء عرض سعر آخر — تم إنشاء عرض السعر بالفعل.")

        if not self.milestone_group_ids:
            raise UserError("No milestone groups found.")

        partner = self.partner_id
        if not partner:
            raise UserError("Please select a customer first.")

        project = self.project_id
        analytic_account = False

        # ----------------------------
        # Analytic Account Logic
        # ----------------------------
        # if project:
        #     analytic_account = self.env['account.analytic.account'].search([
        #         ('project_ids', 'in', project.id)
        #     ], limit=1)
        #
        #     if not analytic_account:
        #         plan = self.env['account.analytic.plan'].search([], limit=1)
        #         if not plan:
        #             raise UserError("Please create an Analytic Plan first.")
        #
        #         analytic_account = self.env['account.analytic.account'].create({
        #             "name": project.name,
        #             "company_id": project.company_id.id,
        #             "plan_id": plan.id,
        #         })
        #
        #     project.account_id = analytic_account.id
        #
        # # =====================================================
        # # ================== NEW BUDGET LOGIC =================
        # # =====================================================
        #
        #
        # Budget = self.env["budget.analytic"]
        # BudgetLine = self.env["budget.line"]
        #
        # # إجمالي تكلفة المشروع = مجموع كل المجموعات
        # total_cost = sum(group.total_cost for group in self.milestone_group_ids)
        #
        # # حساب Total Unit Price لكل المجموعات (لـ Revenue Budget)
        # sum_total_unit_price = sum(
        #     (g.total_goods_unit_price or 0.0) + (g.total_service_unit_price or 0.0)
        #     for g in self.milestone_group_ids
        # )
        #
        #
        # if total_cost <= 0:
        #     raise UserError("Total cost cannot be zero when creating budgets.")
        #
        # # التاريخ من CRM → Planned Dates
        # date_from = self.date_start or fields.Date.today()
        # date_to = self.date_end or self.date_start or fields.Date.today()
        #
        # if not analytic_account:
        #     raise UserError("Could not determine project analytic account.")
        #
        # # ----------------------
        # # CREATE EXPENSE BUDGET
        # # ----------------------
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
        # # ----------------------
        # # CREATE REVENUE BUDGET
        # # ----------------------
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
        #     "budget_amount": sum_total_unit_price,
        #     "company_id": self.company_id.id,
        # })
        #
        # revenue_budget.action_budget_confirm()

        # =====================================================
        # END OF NEW LOGIC
        # =====================================================

        # ----------------------------
        # Create Sale Order
        # ----------------------------
        sale_order = self.env["sale.order"].create({
            "partner_id": partner.id,
            "partner_invoice_id": partner.id,
            "partner_shipping_id": partner.id,
            "opportunity_id": self.id,
            "origin": f"Milestones for {self.name}",
            "project_id": self.project_id.id,
            "is_crm_custom_quotation": True,

        })

        group_to_sol = {}
        milestone_line_to_sol = {}

        # ----------------------------
        # Create SO Lines for Groups
        # ----------------------------
        for group in self.milestone_group_ids:
            tmpl = group.milestone_id
            variant = tmpl.product_variant_id

            self.env["sale.order.line"].create({
                "order_id": sale_order.id,
                "name": tmpl.name,
                "display_type": "line_section",
            })

            milestone_sale_line = False

            if group.goods_line_ids or group.total_goods_unit_price:
                self.env["sale.order.line"].create({
                    "order_id": sale_order.id,
                    "name": f"Goods - Total Unit Price: {group.total_goods_unit_price or 0.0:.2f}",
                    "display_type": "line_section",
                })
                for line in group.goods_line_ids:
                    line_qty = line.qty or 1.0
                    goods_sol = self.env["sale.order.line"].create({
                        "order_id": sale_order.id,
                        "product_id": line.product_id.id,
                        "product_uom_qty": line_qty,
                        "price_unit": (line.unit_price or 0.0) / line_qty,
                        "name": line.description or line.product_id.display_name,
                    })
                    milestone_line_to_sol[line.id] = goods_sol.id
                    milestone_sale_line = milestone_sale_line or goods_sol

            if group.service_line_ids or group.total_service_unit_price:
                self.env["sale.order.line"].create({
                    "order_id": sale_order.id,
                    "name": f"Services - Total Unit Price: {group.total_service_unit_price or 0.0:.2f}",
                    "display_type": "line_section",
                })
                for line in group.service_line_ids:
                    line_qty = line.qty or 1.0
                    service_sol = self.env["sale.order.line"].create({
                        "order_id": sale_order.id,
                        "product_id": line.product_id.id,
                        "product_uom_qty": line_qty,
                        "price_unit": (line.unit_price or 0.0) / line_qty,
                        "name": line.description or line.product_id.display_name,
                    })
                    milestone_line_to_sol[line.id] = service_sol.id
                    milestone_sale_line = milestone_sale_line or service_sol

            if not milestone_sale_line:
                milestone_sale_line = self.env["sale.order.line"].create({
                    "order_id": sale_order.id,
                    "product_id": variant.id,
                    "product_uom_qty": group.quantity or 1.0,
                    "price_unit": 0.0,
                    "name": tmpl.name,
                })

            group_to_sol[group.id] = milestone_sale_line.id

        # ----------------------------
        # COPY milestone groups into Sale Order
        # ----------------------------
        for group in self.milestone_group_ids:

            new_group = group.copy({
                "sale_order_id": sale_order.id,
                "lead_id": False,
            })

            # Copy GOODS lines
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
                    "source_line_id": line.id,
                    "sale_order_line_id": milestone_line_to_sol.get(line.id),
                    "line_update_state": line.line_update_state or "from_pipeline",
                })

            # Copy SERVICES lines
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
                    "source_line_id": line.id,
                    "sale_order_line_id": milestone_line_to_sol.get(line.id),
                    "line_update_state": line.line_update_state or "from_pipeline",
                })

        # ----------------------------
        # Create Project Milestones
        # ----------------------------
        if self.project_id:
            for group in self.milestone_group_ids:
                sol_id = group_to_sol.get(group.id)
                if sol_id:
                    self.env["project.milestone"].create({
                        "project_id": self.project_id.id,
                        "name": group.milestone_id.name,
                        "sale_line_id": sol_id,
                    })

        # Hide button
        self.is_milestone_quotation_generated = True

        # ===============================
        # MOVE TO STAGE QUALIFIED
        # ===============================
        Stage = self.env["crm.stage"]

        qualified_stage = Stage.search([
            ('name', '=', 'Qualified'),
            '|',
            ('team_id', '=', self.team_id.id),
            ('team_id', '=', False),
        ], limit=1)

        if qualified_stage:
            self.stage_id = qualified_stage.id

        # ----------------------------
        # Open Sale Order
        # ----------------------------
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": sale_order.id,
        }


# -----------------------------
# Sale Order
# -----------------------------
class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_crm_custom_quotation = fields.Boolean(default=False)

    milestone_group_ids_proxy = fields.One2many(
        "crm.milestone.group",
        "sale_order_id",
        string="Editable Milestone Groups"
    )

    milestone_group_ids = fields.One2many(
        comodel_name="crm.milestone.group",
        inverse_name="lead_id",
        string="Milestone Groups (CRM Readonly)",
        readonly=True,
        compute="_compute_milestone_groups",
    )


    show_milestone_tab = fields.Boolean(
        string="Show Milestone Tab",
        compute="_compute_show_milestone_tab",
        store=False
    )

    @api.model
    def create(self, vals):

        if vals.get('is_crm_custom_quotation'):

            if not vals.get('warehouse_id'):
                warehouse = self.env['stock.warehouse'].search([
                    ('is_project_warehouse', '=', True)
                ], limit=1)

                if warehouse:
                    vals['warehouse_id'] = warehouse.id

        return super(SaleOrder, self).create(vals)

    def _compute_milestone_groups(self):
        for order in self:
            order.milestone_group_ids = order.opportunity_id.milestone_group_ids

    def _compute_show_milestone_tab(self):
        for rec in self:
            rec.show_milestone_tab = (
                    rec.company_id.company_registry == ARKA_COMPANY_REGISTRY
            )

    def action_confirm(self):
        for order in self:
            lead = order.opportunity_id

            # If lead exists and project isn't created yet → show wizard
            if order.is_crm_custom_quotation:
                if lead and not lead.project_id:
                    return {
                        "type": "ir.actions.act_window",
                        "name": "Create Project?",
                        "res_model": "sale.order.project.wizard",
                        "view_mode": "form",
                        "target": "new",
                        "context": {
                            "default_sale_order_id": order.id,
                            "default_lead_id": lead.id,
                        }
                    }

        # If project already exists → normal confirm
        return super().action_confirm()

    def _action_confirm_after_project(self):
        return super(SaleOrder, self).action_confirm()



# create location due confirm quotation
class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    is_project_warehouse = fields.Boolean("Project Warehouse")


    @api.constrains('is_project_warehouse')
    def _check_single_project_warehouse(self):
        for rec in self:
            if rec.is_project_warehouse:
                warehouses = self.search([
                    ('is_project_warehouse', '=', True),
                    ('id', '!=', rec.id)
                ])
                if warehouses:
                    raise ValidationError("مسموح Warehouse واحد بس يكون Project Warehouse ❌")




class Project(models.Model):
    _inherit = "project.project"

    location_id = fields.Many2one("stock.location")



# preview share quotation
import logging
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class CustomPortal(CustomerPortal):

    @http.route(['/my/orders/<int:order_id>/accept'], type='json', auth="public", website=True)
    def portal_quote_accept(self, order_id, access_token=None, **post):

        order = request.env['sale.order'].sudo().browse(order_id)
        company = order.company_id

        if order.partner_id.company_id != company:
            order.partner_id.sudo().write({"company_id": company.id})

        if order.opportunity_id.company_id != company:
            order.opportunity_id.sudo().write({"company_id": company.id})

        request.env = request.env(context=dict(
            request.env.context,
            allowed_company_ids=[company.id]
        ))

        response = super().portal_quote_accept(
            order_id,
            access_token=access_token,
            **post
        )

        try:
            order.invalidate_recordset()

            if order.is_crm_custom_quotation:
                lead = order.opportunity_id

                if lead and not lead.project_id:
                    env = request.env(context=dict(
                        request.env.context,
                        allowed_company_ids=[company.id]
                    ))

                    manager = lead.project_manager_ids[:1]

                    project = env["project.project"].sudo().with_company(company).create({
                        "name": lead.won_text or lead.name,
                        "partner_id": lead.partner_id.id,
                        "company_id": company.id,
                        "user_id": manager.id if manager else False,
                    })

                    warehouse = env['stock.warehouse'].sudo().search([
                        ('is_project_warehouse', '=', True)
                    ], limit=1)

                    if not warehouse:
                        raise UserError("لازم تختار Project Warehouse الأول")

                    location = env['stock.location'].sudo().create({
                        "name": project.name,
                        "usage": "internal",
                        "location_id": warehouse.view_location_id.id,
                        "company_id": company.id,
                    })

                    project.write({"location_id": location.id})
                    order.write({"project_id": project.id})

                    # ✅ crm.stage مفيش company_id — بس ابحث بـ is_won
                    won_stage = env['crm.stage'].sudo().search(
                        [('is_won', '=', True)], limit=1
                    )

                    lead_vals = {
                        "project_id": project.id,
                        "is_project_confirmed": True,
                    }
                    if won_stage:
                        lead_vals["stage_id"] = won_stage.id

                    lead.write(lead_vals)

                    # Analytic Account
                    plan = env['account.analytic.plan'].sudo().search([], limit=1)
                    if not plan:
                        raise UserError("لازم تعمل Analytic Plan الأول")

                    analytic = env['account.analytic.account'].sudo().with_company(company).create({
                        "name": project.name,
                        "company_id": company.id,
                        "plan_id": plan.id,
                    })
                    project.account_id = analytic.id

                    # Budgets
                    total_cost = sum(g.total_cost for g in lead.milestone_group_ids)
                    total_revenue = sum(
                        (g.total_goods_unit_price or 0.0) +
                        (g.total_service_unit_price or 0.0)
                        for g in lead.milestone_group_ids
                    )

                    Budget = env["budget.analytic"].sudo().with_company(company)
                    BudgetLine = env["budget.line"].sudo().with_company(company)

                    date_from = lead.date_start or fields.Date.today()
                    date_to = lead.date_end or date_from

                    expense = Budget.create({
                        "name": f"{project.name} - Expense",
                        "user_id": lead.user_id.id,
                        "budget_type": "expense",
                        "date_from": date_from,
                        "date_to": date_to,
                        "company_id": company.id,
                    })
                    BudgetLine.create({
                        "account_id": analytic.id,
                        "budget_analytic_id": expense.id,
                        "budget_amount": total_cost,
                    })
                    expense.action_budget_confirm()

                    revenue = Budget.create({
                        "name": f"{project.name} - Revenue",
                        "user_id": lead.user_id.id,
                        "budget_type": "revenue",
                        "date_from": date_from,
                        "date_to": date_to,
                        "company_id": company.id,
                    })
                    BudgetLine.create({
                        "account_id": analytic.id,
                        "budget_analytic_id": revenue.id,
                        "budget_amount": total_revenue,
                    })
                    revenue.action_budget_confirm()

                # ✅ Confirm الأوردر
                order.with_company(company).sudo()._action_confirm_after_project()
                _logger.info("✅ Order %s confirmed successfully", order.name)

        except Exception as e:
            _logger.error("❌ portal_quote_accept error for order %s: %s", order_id, str(e))

        return response
