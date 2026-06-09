from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    building_product_id = fields.Many2one(
        'product.template',
        string="مبنى",
        readonly=True,
    )