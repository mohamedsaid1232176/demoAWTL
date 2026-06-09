from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        domain="[('subscription_product','=',False)]" 
    )