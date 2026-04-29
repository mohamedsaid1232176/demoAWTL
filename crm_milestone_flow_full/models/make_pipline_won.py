from odoo import models, api, fields
from odoo.exceptions import UserError

ARKA_COMPANY_REGISTRY = "311369490700003"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        company_registry = self.env.company.company_registry

        # ❗ منع الـ Confirm لو الشركة Arka والـ Lead في حالة WON
        # if company_registry == ARKA_COMPANY_REGISTRY:
        #     lead = self.opportunity_id
        #     if lead and lead.stage_id and lead.stage_id.name == "Won":
        #         raise UserError("غير مسموح بتأكيد عرض السعر في حالة Won.\n"
        #                         "يجب إنشاء العرض من نظام الـ Milestones فقط.")

        # --- 1. نفذ عملية التأكيد العادية ---
        res = super().action_confirm()

        # --- 2. بعد التأكيد، خلي الـ Lead = WON ---
        for order in self:
            lead = order.opportunity_id
            if lead and lead.type == "opportunity" and lead.probability < 100:
                try:
                    lead.action_set_won_rainbowman()
                except Exception:
                    lead.write({
                        "stage_id": self.env['crm.stage'].search([('is_won', '=', True)], limit=1).id,
                        "probability": 100,
                    })

        return res


class CrmLead(models.Model):
    _inherit = "crm.lead"

    show_milestone_tab = fields.Boolean(
        compute="_compute_show_milestone_tab",
        store=False
    )

    @api.depends("stage_id")
    def _compute_show_milestone_tab(self):
        for rec in self:
            rec.show_milestone_tab = rec.stage_id.name in ["Technical Office", "Won","Projects Management"]

    # ====================================================
    #  NEW FUNCTION: منع New Quotation في Arka
    # ====================================================
    def action_sale_quotations_new(self):
        """Prevent creating new quotation manually for Arka company."""

        company_registry = self.env.company.company_registry

        # لو الشركة Arka → امنع إنشاء Quotation من CRM
        if company_registry == ARKA_COMPANY_REGISTRY:

            # لو الـ Lead في Proposition أو Won
            if self.stage_id.name in ["Won"]:
                raise UserError(
                    "غير مسموح بإنشاء امر بيع مره اخري."
                )

        # otherwise → نفذ السلوك الافتراضي
        return super().action_sale_quotations_new()
