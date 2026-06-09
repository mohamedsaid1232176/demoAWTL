from odoo import models, fields

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    code = fields.Char(
        string='Short Name',
        required=True,
        size=100
    )
