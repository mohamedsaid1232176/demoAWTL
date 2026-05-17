from odoo import models, fields, api

class GoodsWizard(models.TransientModel):
    _name = "wizard.goods.selector"
    _description = "Select Goods for Milestone"

    lead_id = fields.Many2one("crm.lead")
    milestone_id = fields.Many2one("product.template")
    product_ids = fields.Many2many("product.product", string="Products")

    @api.model
    def create(self, vals):
        """
        لو المستخدم أنشأ product جديدة من داخل wizard
        نربطها تلقائياً بالـ milestone اللي في wizard
        """
        wizard = super().create(vals)

        for product in wizard.product_ids:
            tmpl = product.product_tmpl_id

            # لو الـ product template مش مرتبط بالـ milestone – نربطه
            if wizard.milestone_id and wizard.milestone_id not in tmpl.milestone_ids:
                tmpl.milestone_ids = [(4, wizard.milestone_id.id)]

        return wizard

    def action_add_goods(self):
        group = self.env["crm.milestone.group"].browse(self.env.context.get("default_group_idx"))
        group.add_products_from_selector(self.product_ids, "goods")
        return {'type': 'ir.actions.act_window_close'}

