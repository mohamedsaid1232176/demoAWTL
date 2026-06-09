from odoo import models, fields, api


class OneProductWizard(models.TransientModel):
    _name = 'one.product.wizard'
    _description = 'One Product Wizard'

    product_id = fields.Many2one('product.product',string="Product",required=True,
        domain="""
        [
            ('product_tmpl_id.subscription_product', '=', False),
            ('product_tmpl_id.building_id', '=', context.get('building_product_id')),
            ('product_tmpl_id.unit_type', 'in', ['apartment', 'room', 'bed'])
        ]
        """
    )
    quantity = fields.Float(string="Quantity", readonly=True)
    unit_price = fields.Float(string="Unit Price", readonly=True)

    sale_order_id = fields.Many2one('sale.order')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        sale_order_id = self.env.context.get('default_sale_order_id')
        if sale_order_id:
            order = self.env['sale.order'].browse(sale_order_id)

            if order.subscription_duration:
                res['quantity'] = order.subscription_duration
            else:
                res['quantity'] = 1

            if order.total_value and order.subscription_duration:
                res['unit_price'] = order.total_value / order.subscription_duration
            else:
                res['unit_price'] = 0

        return res

    def action_confirm(self):
        self.ensure_one()
        order = self.sale_order_id

        analytic_distribution = {}
        if self.product_id.analytic_account_id:
            analytic_distribution = {
                self.product_id.analytic_account_id.id: 100
            }

        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_id.id,
            'analytic_distribution': analytic_distribution,
            'product_uom_qty': self.quantity,
            'product_uom': order.plan_id.unit_of_measure_id.id,
            'price_unit': self.unit_price,
        })

        return {'type': 'ir.actions.act_window_close'}