from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MultiProductWizard(models.TransientModel):

    _name = 'multi.product.wizard'
    _description = 'Multi Product Wizard'

    product_ids = fields.One2many(
        'multi.product.wizard.line',
        'wizard_id',
        string="Products",
    )
    
    sale_order_id = fields.Many2one('sale.order')


    def action_confirm(self):
        self.ensure_one()
        order = self.sale_order_id

        subscription_qty = order.subscription_duration or 1
        total_amount = 0.0

        for line in self.product_ids:
            line_amount = subscription_qty * line.total_value
            total_amount += line_amount

        if total_amount > order.total_value:
            raise ValidationError(
                f"""
                إجمالي قيمة المنتجات ({total_amount})
                أكبر من المبلغ المستحق في أمر البيع ({order.total_value})
                """
            )
        if total_amount < order.total_value:
            raise ValidationError(
                f"""
                إجمالي قيمة المنتجات ({total_amount})
                أقل من المبلغ المستحق في أمر البيع ({order.total_value})
                """
            )
        
        for line in self.product_ids:
            analytic_distribution = {}
            if line.product_id.analytic_account_id:
                analytic_distribution = {
                    line.product_id.analytic_account_id.id: 100
                }

            self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': line.product_id.id,
                'analytic_distribution': analytic_distribution,
                'product_uom_qty': subscription_qty, 
                'product_uom': order.plan_id.unit_of_measure_id.id,
                'price_unit': line.total_value,
            })

        return {'type': 'ir.actions.act_window_close'}
    


class MultiProductWizardLine(models.TransientModel):
    _name = 'multi.product.wizard.line'
    _description = 'Multi Product Wizard Line'

    wizard_id = fields.Many2one(
        'multi.product.wizard',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain="""
        [
            ('product_tmpl_id.subscription_product', '=', False),
            ('product_tmpl_id.building_id', '=', context.get('building_product_id')),
            ('product_tmpl_id.unit_type', 'in', ['apartment', 'room', 'bed'])
        ]
        """,
        required=True
    )

    total_value = fields.Float(string='المبلغ المستحق')

    quantity = fields.Integer(string='Quantity',related='wizard_id.sale_order_id.subscription_duration',readonly=True,)

    @api.depends('wizard_id.sale_order_id.subscription_duration')
    def _compute_quantity_display(self):
        for line in self:
            line.quantity_display = line.quantity or 1   