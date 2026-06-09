from odoo import models, fields, api

class ServicesWizard(models.TransientModel):
    _name = "wizard.services.selector"
    _description = "Select Services for Milestone"

    lead_id = fields.Many2one("crm.lead")
    milestone_id = fields.Many2one("product.template")
    product_ids = fields.Many2many("product.product", string="Products")

    @api.model
    def create(self, vals):
        wizard = super().create(vals)

        # نوع الـ product المطلوب من context
        force_type = wizard.env.context.get("force_type", "service")

        for product in wizard.product_ids:
            tmpl = product.product_tmpl_id

            # اربط milestone لو لازم
            if wizard.milestone_id and wizard.milestone_id not in tmpl.milestone_ids:
                tmpl.milestone_ids = [(4, wizard.milestone_id.id)]

            # ❌ ما نغيرش الـ type Standard
            # tmpl.type = force_type

            # ✔️ استخدم الفلاج الجديد بدل type
            if force_type == "milestone":
                tmpl.is_milestone_flag = True
            else:
                tmpl.is_milestone_flag = False

        return wizard

    def action_add_services(self):
        group = self.env["crm.milestone.group"].browse(self.env.context.get("default_group_idx"))
        group.add_products_from_selector(self.product_ids, "service")
        return {'type': 'ir.actions.act_window_close'}
