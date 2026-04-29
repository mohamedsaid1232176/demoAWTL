from odoo import models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if not vals.get('default_code'):
            vals['default_code'] = self.env['ir.sequence'].next_by_code(
                'product.default.code'
            )
        return super().create(vals)
