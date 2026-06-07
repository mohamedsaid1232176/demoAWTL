from odoo import models, fields


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    room_ids = fields.Many2many(
        'product.template',
        'account_analytic_account_room_rel', 
        'account_id',                        
        'product_id',                       
        string="غرفة"
    )

    apartment_ids = fields.Many2many(
        'product.template',
        'account_analytic_account_apartment_rel',  
        'account_id',
        'product_id',
        string="شقة"
    )

    bed_ids = fields.Many2many(
    'product.template',
    'account_analytic_account_bed_rel',
    'account_id',
    'product_id',
    string="سرير"
)
    
    is_company_subscription = fields.Boolean(string="Is Subscription Company", related='company_id.is_subscription', readonly=True)


    building_id = fields.Many2one('product.template', string ='مبنى')

    apartment_id = fields.Many2one('product.template', string ='شقة')

    room_id = fields.Many2one('product.template', string ='غرفة')

    product_id = fields.Many2one(
        'product.template',
        string="Unit"
    )

    unit_type = fields.Selection(
        related='product_id.unit_type',
        string="Unit Type",
        store=True
    )