from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    def _default_subscription_state_ids(self):
        return self.env['subscription.state'].search([])

    is_subscription = fields.Boolean(string='Is Subscription Company', default=False)

    subscription_product = fields.Boolean(string='Subscription Product', default=False)

    subscription_state_ids = fields.Many2many(
        'subscription.state',
        string='Subscription States',
        default=_default_subscription_state_ids,
    )

    organization_type = fields.Many2one('organization.type', string="نوع المنظمة")
    unified_number = fields.Char(string="الرقم الموحد")
    cr_date = fields.Date(string="تاريخ السجل التجاري")
    issued_by = fields.Char(string="جهة الإصدار")


    def write(self, vals):
        res = super().write(vals)

        if 'subscription_state_ids' in vals:
            orders = self.env['sale.order'].search([
                ('company_id', 'in', self.ids)
            ])

            orders._recompute_subscription_products()

        return res
