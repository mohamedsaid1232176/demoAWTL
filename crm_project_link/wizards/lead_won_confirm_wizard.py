from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrderProjectWizard(models.TransientModel):
    _name = 'sale.order.project.wizard'
    _description = 'Create Project After Sale Order Confirm'

    lead_id = fields.Many2one('crm.lead')
    sale_order_id = fields.Many2one('sale.order')

    def action_confirm_project(self):
        self.ensure_one()
        lead = self.lead_id
        order = self.sale_order_id

        # ----------------------------------
        # 1) Create Project
        # ----------------------------------


        # ----------------------------------
        # 1) Get first project manager
        # ----------------------------------
        manager = lead.project_manager_ids[:1]  # أول واحد بس

        # ----------------------------------
        # 2) Create Project
        # ----------------------------------
        project_name = lead.won_text or lead.name

        project = self.env["project.project"].create({
            "name": project_name,
            "partner_id": lead.partner_id.id,
            "user_id": manager.id if manager else False,  # 🔥 هنا المهم
        })

        # ----------------------------------
        # 🔥 Create Stock Location
        # ----------------------------------
        warehouse = self.env['stock.warehouse'].search([
            ('is_project_warehouse', '=', True)
        ], limit=1)

        if not warehouse:
            raise UserError("لازم تختار Project Warehouse الأول")

        location = self.env['stock.location'].create({
            "name": project.name,
            "usage": "internal",
            "location_id": warehouse.view_location_id.id,
            "company_id": project.company_id.id,
        })

        # ربطها بالمشروع
        project.write({
            "location_id": location.id
        })

        # Link project to SO
        if order:
            order.write({"project_id": project.id})

        # Update lead
        lead.write({
            "project_id": project.id,
            "is_project_confirmed": True,
            "stage_id": self.env['crm.stage'].search([('is_won', '=', True)], limit=1).id
        })

        # ----------------------------------
        # 2) Compute costs for budgets
        # ----------------------------------
        total_cost = sum(group.total_cost for group in lead.milestone_group_ids)

        total_revenue = sum(
            (g.total_goods_unit_price or 0.0) +
            (g.total_service_unit_price or 0.0)
            for g in lead.milestone_group_ids
        )

        # ----------------------------------
        # 3) Create Analytic Account
        # ----------------------------------
        plan = self.env['account.analytic.plan'].search([], limit=1)
        analytic_account = self.env['account.analytic.account'].create({
            "name": project.name,
            "company_id": project.company_id.id,
            "plan_id": plan.id,
        })
        project.account_id = analytic_account.id

        # ----------------------------------
        # 4) Create Budgets
        # ----------------------------------
        Budget = self.env["budget.analytic"]
        BudgetLine = self.env["budget.line"]

        date_from = lead.date_start or fields.Date.today()
        date_to = lead.date_end or date_from

        # Expense Budget
        expense = Budget.create({
            "name": f"{project.name} - Expense",
            "user_id": lead.user_id.id,
            "budget_type": "expense",
            "date_from": date_from,
            "date_to": date_to,
            "company_id": lead.company_id.id,
        })

        BudgetLine.create({
            "account_id": analytic_account.id,
            "budget_analytic_id": expense.id,
            "budget_amount": total_cost,
        })
        expense.action_budget_confirm()

        # Revenue Budget
        revenue = Budget.create({
            "name": f"{project.name} - Revenue",
            "user_id": lead.user_id.id,
            "budget_type": "revenue",
            "date_from": date_from,
            "date_to": date_to,
            "company_id": lead.company_id.id,
        })

        BudgetLine.create({
            "account_id": analytic_account.id,
            "budget_analytic_id": revenue.id,
            "budget_amount": total_revenue,
        })
        revenue.action_budget_confirm()

        return order._action_confirm_after_project()
class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_confirm_after_project(self):
        return super(SaleOrder, self).action_confirm()
