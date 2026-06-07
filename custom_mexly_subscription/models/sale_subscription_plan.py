from odoo import models, fields


class SaleSubscriptionPlan(models.Model):


    _inherit = 'sale.subscription.plan'

    unit_of_measure_id = fields.Many2one('uom.uom',string="Unit of Measure")

